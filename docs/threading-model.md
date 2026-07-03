# Threading Model

This page describes how McRogueFace coordinates the C++ render loop with Python
threads, and states the **normative rule** for touching engine objects from a
thread other than the one running the game loop.

## The rule

> **Any access to `mcrfpy` objects from a non-main thread must happen inside a
> `with mcrfpy.lock():` block. Behavior outside the lock is undefined.**

This is a frozen part of the 1.0 contract. It holds identically under the
default GIL build and under free-threaded (`--disable-gil`) builds. Reads and
writes both require the lock: creating, mutating, or even reading properties of
Frames, Captions, Sprites, Grids, Entities, Colors, Vectors, Scenes, Timers, or
any other `mcrfpy` object from a worker thread is only defined while the lock is
held.

Code that runs on the main thread — script initialization, `Scene.on_key` and
other input handlers, `Timer` callbacks, animation callbacks, grid/cell
callbacks — is already synchronized with the render loop and does **not** need
the lock. `with mcrfpy.lock():` is a no-op there, so the same helper function
can be called safely from both contexts.

## Why the lock exists

The engine is single-threaded by design: the game loop owns all `mcrfpy` state
and mutates it freely between frames without internal locking. Rather than make
every engine object internally thread-safe, McRogueFace exposes one coarse
synchronization point. Worker threads park on it until the main loop opens a
safe window; the main loop never has to defend against concurrent mutation.

This coarse-grained contract is what keeps a future free-threading port
(tracked in #336) tractable — the promise to callers never changes, and the
engine never has to become internally thread-safe.

## How it works

The mechanism is `FrameLock` (`src/GameEngine.cpp`) driving the
`PyLockContext` context manager returned by `mcrfpy.lock()`
(`src/PyLock.cpp`):

1. **GIL released around `display()`.** Each frame, the engine releases the GIL
   while it presents the frame (`Py_BEGIN_ALLOW_THREADS` around
   `window->display()` / `headless_renderer->display()`,
   `src/GameEngine.cpp:475-499`). This lets waiting Python worker threads get
   scheduled.

2. **Safe window between frames.** After `display()` and before the next
   frame's processing, if any thread is waiting on the frame lock, the engine
   opens a window (`frameLock.openWindow()`), releases the GIL so the waiting
   threads can run their `with mcrfpy.lock():` bodies, then closes the window
   once they finish (`frameLock.closeWindow()`).

3. **`mcrfpy.lock()` on a worker thread blocks (GIL released) until that
   window opens.** `PyLockContext.__enter__` calls `FrameLock::acquire()`,
   which waits on a condition variable with the GIL released
   (`src/GameEngine.cpp:29-40`). When the block exits, `__exit__` releases the
   frame lock.

4. **`mcrfpy.lock()` on the main thread is a no-op.** `__enter__` detects the
   main thread and returns immediately without acquiring anything
   (`src/PyLock.cpp:70-85`), because the main thread is already the sole owner
   of engine state.

5. **Engine → Python callbacks re-acquire the GIL.** All callbacks the engine
   invokes into Python (animations, scene/input handlers, timers) wrap their
   work in `PyGILState_Ensure` / `PyGILState_Release`
   (`src/Animation.cpp`, `src/PySceneObject.cpp`), so they run correctly
   regardless of which thread advanced the frame.

## Worker-thread example

A background thread computes something expensive (pathfinding, procedural
generation, network I/O) and then updates the UI. Only the UI update needs the
lock; the computation itself does not touch `mcrfpy` objects and runs freely.

```python
import mcrfpy
import threading

scene = mcrfpy.Scene("game")
label = mcrfpy.Caption(text="working...", pos=(10, 10))
scene.children.append(label)
mcrfpy.current_scene = scene

def worker():
    # Heavy work OUTSIDE the lock: touches no mcrfpy objects.
    result = expensive_computation()

    # Touching mcrfpy objects: MUST be inside the lock on a worker thread.
    with mcrfpy.lock():
        label.text = f"done: {result}"
        label.fill_color = mcrfpy.Color(0, 255, 0)

    # Read-modify-writeback for value types (Color/Vector) also goes
    # inside the lock when done off the main thread:
    with mcrfpy.lock():
        c = label.fill_color      # copy
        c.a = 128                 # mutate the copy
        label.fill_color = c      # write it back

threading.Thread(target=worker, daemon=True).start()
```

### What not to do

```python
def worker_bad():
    result = expensive_computation()
    # WRONG: mutating an mcrfpy object from a worker thread without the lock.
    # Behavior is undefined — visual glitches, torn reads, or a crash.
    label.text = f"done: {result}"
```

Keep lock blocks short. The main loop is stalled for the duration of every open
window, so do heavy work outside the lock and hold it only for the actual
engine-object access.

## Related

- `mcrfpy.lock()` — the API entry point (see its docstring).
- [API stability policy](api-stability.md) — the frozen 1.0 contract.
- #219 — original concurrency design.
- #336 — free-threading hardening (implementation may harden; the contract above does not change).
- #220 — subinterpreters, the *other* concurrency model, which is out of scope for 1.x (see the stability policy).
