# The frame barrier: `mcrfpy.lock()`

McRogueFace runs its world on one thread. `mcrfpy.lock()` is the barrier that lets a
background thread — a network client, a worker pool, an embedder's message bus — hand
mutations back to that world safely.

This document states the rules, **the measured cost of breaking them**, and the failure
modes. The cost is the part that matters: every rule here fails *silently*, and a silent
failure that costs frame time presents as "the engine is slow", never as "a handler is
misbehaving".

---

## The mechanism

`FrameLock` lives in `src/GameEngine.h` / `src/GameEngine.cpp`. Once per frame, after the
frame's work has settled and before `currentFrame++`, the main thread opens a **safe
window**:

```cpp
if (frameLock.hasWaiting()) {
    frameLock.openWindow();          // wake every waiter
    Py_BEGIN_ALLOW_THREADS
    frameLock.closeWindow();         // park until every holder has released
    Py_END_ALLOW_THREADS
}
```

Both frame paths do this: `GameEngine::doFrame()` (windowed) and
`GameEngine::runSimFrame()` (headless — the path `mcrfpy.step()` and `mcrfpy.advance()`
drive). The headless half was added for #398; before it, a background thread under a
headless main loop blocked in `acquire()` forever, because the condition variable it waits
on has **no timeout**.

On the thread that **drives the clock**, `mcrfpy.lock()` is a documented no-op
(`src/PyLock.cpp`). The same handler body therefore works unchanged from a timer callback,
from script init, and from a background thread.

**Exactly one thread drives the clock (#411).** The first thread to run a frame owns it:
the main thread once the engine's own loop starts (always, when windowed), otherwise the
first caller of `step()`/`advance()`. It owns the clock until it exits. Any other thread
that calls `step()`/`advance()` gets `RuntimeError`, and a headless `--run-forever` loop
refuses to start if a background thread already owns it. If a background thread drives
the clock, the **main thread is just another thread**: its `lock()` is a real barrier
that waits for the owner's safe window. Before #411, any thread could run a frame, so two
frame bodies could run concurrently over one scene graph.

---

## Rule 1 — inside the lock, mutate only

No I/O. No `await`. No network call. No blocking wait. No `sleep`. No frame advance.

```python
data = bus.poll()                  # compute OUTSIDE
with mcrfpy.lock():
    entity.cell_pos = data.pos     # apply INSIDE — assignment only
```

### The measured cost of breaking it

The main thread parks in `closeWindow()` until every holder returns, so **time held inside
the lock is added to the frame that serves it, approximately 1:1.**

Measured by `tests/integration/frame_lock_hold_budget_test.py` (re-run it to regenerate
these numbers; it is a test, so they cannot rot). One handler invocation per frame, the
same thread and the same `time.sleep(H)` in both arms — the only variable is which side of
the barrier the sleep happens on:

| hold H (ms) | peak frame time, sleep **inside** the lock (ms) | peak frame time, sleep **outside** the lock (ms) |
|---:|---:|---:|
| 0 | 0.15 | 0.14 |
| 1 | 1.31 | 0.16 |
| 2 | 2.34 | 0.18 |
| 4 | 4.32 | 0.18 |
| 8 | 8.35 | 0.18 |
| 16 | 16.32 | 0.18 |

- **Coefficient: 1.005 ms of frame time per ms held** (least-squares slope; 1.001–1.016
  across five runs).
- **Control: 0.002** ms per ms slept outside the lock — three orders of magnitude smaller.
  The cost is the barrier, not the sleeping.
- **Barrier overhead per acquire: 0.06–0.15 ms.** Acquiring is cheap. Holding is not.

**The budget.** At 60 fps you have 16.67 ms per frame. A handler holding for `H` ms leaves
`16.67 − H − (this frame's own work)` ms of headroom. A hold at or above the frame budget
drops a frame outright. A 100 ms HTTP request inside the lock costs six frames, and
nothing in any log will say so.

### Re-acquiring in a loop (#410, fixed)

A safe window serves a given thread **at most once**. `closeWindow()` first marks the
window as closing (under the barrier's mutex); a non-nested `lock()` arriving after that
waits for the *next* window, while threads that were already waiting when the window
opened, and nested `lock()` calls by a thread that is already inside, still pass. So a
thread that releases and immediately re-acquires gets one acquire per frame, not an
unbounded number inside one frame.

Before the fix, `closeWindow()` waited for `waiting == 0` while the window was still open,
so a re-entering thread was served again in the same window and the window never closed.
One thread with a 1 ms hold reduced the main loop to 31 frames in 2 s, and eight polite
threads (1 ms gap) could trigger the same thing once hold time approached the gap. Now
the same greedy thread is served exactly 1.0 acquires per frame at every hold length
(`tests/integration/frame_lock_hold_budget_test.py`, and the re-admission gate in
`tests/regression/issue_410_framelock_readmission_test.py`).

The rule still stands as a cost model: time held is added to the frame that serves it,
and a greedy loop is now paced to one acquire per frame, so a backlog drains at the frame
rate. Do bounded work per acquire.

---:|---:|---:|---:|---:|
| 0 | 376 883 | 0.005 | 0.5 | 4.0 |
| 1 | **31** | **32.1** | **683** | 56.6 |
| 2 | 18 | 40.8 | 438 | 54.6 |
| 5 | 10 | 118.7 | 568 | 39.2 |

One background thread with a 1 ms hold reduced the main loop to **31 frames in two
seconds**. It is not a deadlock — the engine does make progress — which is exactly what
makes it hard to find. This is engine issue **#410**; the barrier does not bound how many
times a thread may be served per frame. Until it does, the rule is: **do one bounded unit
of work per acquire, and do not re-acquire without yielding to a frame.**

---

## Rule 2 — never drive a frame from inside the lock

`mcrfpy.step()` and `mcrfpy.advance()` **raise `RuntimeError`** when called from a thread
that holds the lock:

```
RuntimeError: mcrfpy.step() cannot be called while this thread holds mcrfpy.lock():
it would re-enter the frame the lock is synchronising with, and the frame cannot
complete until this thread releases. Inside the lock, mutate only ...
```

This was backlog item B7. Without the raise:

- If another thread is waiting, the re-entered frame's `closeWindow()` waits for `active`
  to reach 0 — but the caller's own hold *is* part of `active`, so it never can, and the
  main thread is already parked in the outer frame's `closeWindow()` on the same count.
  Three threads, no timeout anywhere, **hard hang with no error and no stack**.
- If nobody is waiting, `hasWaiting()` short-circuits the safe window and the call
  "succeeds" — running a whole simulation frame (timers, `Scene.update()`, animations,
  transitions, `currentFrame++`) on a non-main thread while the main thread sits parked
  mid-frame. Two frame bodies interleaved, and a plausible-looking trace to show for it.
  That is worse than the hang.

A silent no-op and a re-entrancy guard were both considered and rejected: the first
returns "no time passed" to a caller that asked for time to pass and leaves a trace that
merely looks sparse; the second removes the hang while leaving the off-thread frame body
in place, hiding the symptom of the thing that is actually wrong.

**This cannot fire on the clock's owner.** `mcrfpy.lock()` is a no-op there, so the owner
never becomes a holder — `with mcrfpy.lock(): mcrfpy.step()` in a script or a timer
callback keeps working exactly as before. The holder count is per-thread and is a
*counter*, not a flag, so nested `with mcrfpy.lock():` blocks are handled correctly.

---

## Rule 3 — never let frame time feed back into world advancement

Drive world advancement off elapsed wall time with catch-up, never off frame count or a
fixed per-frame delta. A frame-driven world slows down exactly when the thing consuming
frames is slow, which buys the consumer free time and hides the very latency you are
trying to measure.

---

## Failure modes, and how each presents

| what you did | how it presents | how to find it |
|---|---|---|
| held the lock for `H` ms | frame time up by `H` ms; stutter | `frame_lock_hold_budget_test.py`; `get_metrics()['current_frame']` rate |
| re-acquired in a tight loop | paced to one acquire per frame (was: engine at single-digit FPS, #410) | acquires-per-frame ratio |
| called `step()`/`advance()` while holding | `RuntimeError` (previously: silent hard hang) | the exception names the call and the rule |
| called `step()`/`advance()` from a thread that does not drive the clock | `RuntimeError` (previously: two frame bodies ran concurrently) | #411; `tests/regression/issue_411_clock_owner_test.py` |
| mutated from a background thread *without* the lock | torn reads; corruption that reproduces rarely | `tests/integration/observe_under_frame_lock_test.py` phase A/B |
| main loop stopped opening windows | every background thread parks forever in `acquire()` | #398; `tests/regression/issue_398_headless_frame_lock_test.py` |

---

## Coverage

| file | covers |
|---|---|
| `tests/integration/frame_lock_hold_budget_test.py` | the 1:1 coefficient, the control arm, barrier overhead |
| `tests/integration/frame_lock_stress_test.py` | contention across many threads, fairness, no starvation |
| `tests/integration/frame_lock_soak_test.py` | sustained load: no drift in wait time, frame time, or allocation |
| `tests/regression/frame_lock_reentrancy_test.py` | B7 — re-entrancy, nesting, the deadlock arrangement itself |
| `tests/regression/issue_398_headless_frame_lock_test.py` | #398 — the headless safe window exists at all |
| `tests/regression/issue_411_clock_owner_test.py` | #411 — one clock owner; a non-owner main thread's `lock()` is a real barrier |
| `tests/integration/observe_under_frame_lock_test.py` | frame-atomic reads under the lock |
| `tests/integration/background_thread_network_test.py` | the real topology: a bus thread handing results back |

---

## Side-effect-free reads

`GridData.observe()` is designed to be called from inside the lock: it never advances a
frame and never releases the GIL, so it cannot participate in the re-entrancy class above.
As of #402 it is also **side-effect-free with or without an origin** — it computes its
field of view in a scratch buffer private to the call, and never writes the shared
per-grid FOV state that `compute_fov()` / `is_in_fov()` use. A background observer
projecting from an NPC's position therefore cannot disturb a field of view the player or
the renderer just computed.

Note the asymmetry: `compute_fov()` **does** write shared state, by design — it is one
half of a two-call API. Anything that computes between another caller's `compute_fov()`
and its `is_in_fov()` reads silently re-answers that caller's question from the wrong
vantage point. If two subsystems need fields of view on one grid, at least one of them
should be using `observe()`.
