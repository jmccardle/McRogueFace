"""Re-entrancy coverage for mcrfpy.lock() -- backlog B7, part of #395.

THE DEFECT
==========
A background thread that calls mcrfpy.step() (or mcrfpy.advance()) *while holding*
mcrfpy.lock() re-enters GameEngine::runSimFrame(). The re-entered frame reaches the
#219 safe-window block, and if any other thread is waiting there, closeWindow() waits
for FrameLock's `active` count to reach 0 -- but the caller's own hold is part of
`active`, so it never can. Meanwhile the main thread is already parked in the OUTER
frame's closeWindow() on the same count. FrameLock's condition variable has no
timeout (that was #398), so nothing breaks the tie: the process hangs with no error,
no log line and no stack, and it presents as "the engine froze". The same shape is
latent in doFrame() for the windowed path.

Even the case that does NOT hang -- no other thread waiting, so hasWaiting() skips
the safe window entirely -- is wrong: a whole simulation frame (timers, Scene.update,
animations, transitions, currentFrame++) executes on a non-main thread while the main
thread sits parked mid-frame. That is the mutate-only discipline violated in exactly
the way the discipline exists to forbid, and its "success" is worse than the hang
because it yields a plausible-looking trace with two frame bodies interleaved.

THE DECIDED BEHAVIOUR: RAISE
============================
mcrfpy.step() and mcrfpy.advance() raise RuntimeError when the calling thread holds
the frame lock. The two alternatives were considered and rejected:

  * a silent no-op returns 0.0 to a caller that asked for time to pass -- the world
    does not advance, the trace merely looks sparse, and nothing says why;
  * a re-entrancy guard that runs the frame but skips the safe window removes the
    hang while leaving the off-thread frame body in place -- it hides the symptom of
    the thing that is actually wrong.

A RuntimeError names the rule at the call site, in the offending thread, at the
instant of the mistake.

WHAT THIS FILE GATES
====================
  1. step() from a lock-holding background thread raises RuntimeError, and the
     message names the lock.
  2. advance() likewise -- doing it for one and forgetting the other is the failure
     mode, so both are asserted independently.
  3. The refusal is SIDE-EFFECT-FREE: the simulation clock and current_frame are
     unchanged across the refused call. A raise that half-ran a frame first would be
     worse than no raise.
  4. The lock is still usable afterwards: the holder's depth accounting is balanced,
     so the `with` block exits normally, the main thread's frame completes, and a
     LATER acquire from the same thread still works. (A leaked depth would make every
     subsequent step() on that thread raise forever -- a fix that breaks the engine.)
  5. Main-thread `with mcrfpy.lock(): mcrfpy.step()` KEEPS WORKING. lock() is a
     documented no-op on the main thread, so the main thread never becomes a holder
     and there is nothing to re-enter. This is the regression gate on the fix: a
     naive "is any lock held anywhere" check would break every existing headless
     script and timer callback.
  6. Nested `with mcrfpy.lock():` on a background thread still refuses at depth 2 AND
     still refuses at depth 1 after the inner block exits -- i.e. the holder counter
     is a counter, not a flag.
  7. THE DEADLOCK ITSELF: the three-thread arrangement that actually hangs pre-fix
     (a holder that calls step() while a second background thread waits on the
     barrier) completes instead of hanging. This is the only section that reproduces
     B7's literal failure mode rather than its precondition.

WHAT SECTION 4's DEADLINE CAN AND CANNOT DO -- stated because it matters
=======================================================================
Section 4's `drive_until` deadline catches a regression that makes the arrangement
SLOW, or one that leaves a thread parked in acquire(). It CANNOT catch a full
re-introduction of B7, and no Python-side deadline can: in that state the main
thread is blocked inside FrameLock::closeWindow() with the GIL released and no
timeout on the condition variable, so no Python code runs to check any deadline.
This file would hang, and `tests/run_tests.py`'s per-test subprocess timeout is what
turns that into a reported failure. That is a property of the barrier, not a gap in
this test -- the absence of a timeout in acquire()/closeWindow() is deliberate (#398)
and it is exactly why the raise in sections 1-2 has to exist upstream of it.

Run: ./mcrogueface --headless --exec ../tests/regression/frame_lock_reentrancy_test.py
"""

import sys
import threading
import time

import mcrfpy

STEP_SECONDS = 0.016
DEADLINE = 6.0

failures = []


def check(label, got, expected):
    if got != expected:
        failures.append(f"{label}: got {got!r}, expected {expected!r}")
        print(f"  FAILURE: {label}: got {got!r}, expected {expected!r}")
    else:
        print(f"  ok  {label}: {got!r}")


def check_true(label, cond):
    if not cond:
        failures.append(label)
        print(f"  FAILURE: {label}")
    else:
        print(f"  ok  {label}")


scene = mcrfpy.Scene("b7")
probe = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
scene.children.append(probe)
mcrfpy.current_scene = scene


def refusal_kind(exc):
    """Which rule a step()/advance() RuntimeError names: the lock, or (#411) the clock."""
    msg = str(exc)
    if "holds mcrfpy.lock()" in msg:
        return "refused:lock"
    if "does not drive the simulation clock" in msg:
        return "refused:clock"
    return "RuntimeError:" + msg


def drive_until(event, deadline_s=DEADLINE):
    """Run the headless main loop until `event` is set or the deadline passes.

    Returns (fired, steps). The deadline is what turns a re-introduced deadlock into
    a reported FAILURE instead of a hung test process.
    """
    steps = 0
    end = time.monotonic() + deadline_s
    while not event.is_set() and time.monotonic() < end:
        mcrfpy.step(STEP_SECONDS)
        steps += 1
    return event.is_set(), steps


# ---------------------------------------------------------------------------
# Section 1 -- step() and advance() refuse from a lock-holding background thread
# ---------------------------------------------------------------------------
def section1_refusal():
    print("Section 1: step()/advance() from inside the lock raise RuntimeError")

    for fname, call in (("step", lambda: mcrfpy.step(STEP_SECONDS)),
                        ("advance", lambda: mcrfpy.advance(16))):
        done = threading.Event()
        result = {}

        def worker():
            try:
                with mcrfpy.lock():
                    # Read the clock INSIDE the lock, immediately before and after the
                    # refused call, so section 3's side-effect check is taken at the
                    # barrier rather than merely somewhere in the process.
                    m0 = mcrfpy.get_metrics()
                    result["before"] = (m0["simulation_time_ms"], m0["current_frame"])
                    try:
                        call()
                        result["outcome"] = "returned"
                    except RuntimeError as exc:
                        result["outcome"] = "RuntimeError"
                        result["message"] = str(exc)
                    except BaseException as exc:  # noqa: BLE001
                        result["outcome"] = f"{type(exc).__name__}"
                        result["message"] = str(exc)
                    m1 = mcrfpy.get_metrics()
                    result["after"] = (m1["simulation_time_ms"], m1["current_frame"])
                    # (4) the lock is still usable: this assignment happens after the
                    # refusal, still inside the same block.
                    probe.x = 77.0
            except BaseException as exc:  # noqa: BLE001
                result["outer"] = repr(exc)
            finally:
                done.set()

        t = threading.Thread(target=worker, name=f"b7-{fname}", daemon=True)
        t.start()
        fired, steps = drive_until(done)
        t.join(timeout=2.0)

        check_true(f"{fname}(): worker finished within the deadline "
                   f"({steps} main-thread frames driven)", fired)
        check_true(f"{fname}(): no exception escaped the `with` block "
                   f"({result.get('outer')})", "outer" not in result)
        check(f"{fname}(): outcome from inside the lock", result.get("outcome"),
              "RuntimeError")
        msg = result.get("message", "")
        check_true(f"{fname}(): the message names mcrfpy.lock() (got {msg!r})",
                   "mcrfpy.lock()" in msg)
        check_true(f"{fname}(): the message names the offending call "
                   f"(mcrfpy.{fname}())", f"mcrfpy.{fname}()" in msg)

        # (3) side-effect-free refusal, measured at the barrier.
        check(f"{fname}(): simulation clock unchanged across the refused call",
              result.get("after", (None,))[0], result.get("before", (None,))[0])
        check(f"{fname}(): current_frame unchanged across the refused call",
              result.get("after", (None, None))[1], result.get("before", (None, None))[1])
        check(f"{fname}(): the block's later mutation still landed", probe.x, 77.0)
        probe.x = 0.0


# ---------------------------------------------------------------------------
# Section 2 -- the holder counter is balanced, and it is a COUNTER not a flag
# ---------------------------------------------------------------------------
def section2_depth_accounting():
    print("Section 2: nesting, and the holder count is balanced on release")

    done = threading.Event()
    result = {"outcomes": []}

    def outcome_of(call):
        try:
            call()
            return "returned"
        except RuntimeError as exc:
            return refusal_kind(exc)
        except BaseException as exc:  # noqa: BLE001
            return type(exc).__name__

    def worker():
        try:
            with mcrfpy.lock():
                result["outcomes"].append(("depth1",
                                           outcome_of(lambda: mcrfpy.step(STEP_SECONDS))))
                with mcrfpy.lock():
                    result["outcomes"].append(("depth2",
                                               outcome_of(lambda: mcrfpy.step(STEP_SECONDS))))
                # Back to depth 1 after the inner block exits. A FLAG cleared by the
                # inner release would report this thread as no longer holding, and
                # this step() would sail through and re-enter the frame.
                result["outcomes"].append(("depth1-again",
                                           outcome_of(lambda: mcrfpy.step(STEP_SECONDS))))
            # Depth 0: outside every block, on a background thread. The lock rule no
            # longer applies -- if it still did, the depth counter leaked. Since #411 the
            # call is still refused, because the main thread drives the clock, but for
            # the OTHER reason: the message is what proves the depth reached 0.
            result["outcomes"].append(("depth0",
                                       outcome_of(lambda: mcrfpy.step(STEP_SECONDS))))
            # And the lock is re-acquirable afterwards, which is the same property
            # from the other side.
            with mcrfpy.lock():
                probe.x = 99.0
            result["reacquired"] = True
        except BaseException as exc:  # noqa: BLE001
            result["outer"] = repr(exc)
        finally:
            done.set()

    t = threading.Thread(target=worker, name="b7-nest", daemon=True)
    t.start()
    fired, steps = drive_until(done)
    t.join(timeout=2.0)

    check_true(f"nesting worker finished within the deadline ({steps} frames)", fired)
    check_true(f"no exception escaped ({result.get('outer')})", "outer" not in result)
    check("outcomes at each depth", result["outcomes"],
          [("depth1", "refused:lock"), ("depth2", "refused:lock"),
           ("depth1-again", "refused:lock"), ("depth0", "refused:clock")])
    check_true("the lock is re-acquirable after the refusals",
               result.get("reacquired") is True)
    check("the post-refusal locked mutation landed", probe.x, 99.0)


# ---------------------------------------------------------------------------
# Section 3 -- the MAIN thread is unaffected
# ---------------------------------------------------------------------------
def section3_main_thread_unaffected():
    print("Section 3: main-thread `with mcrfpy.lock(): mcrfpy.step()` still works")

    before = mcrfpy.get_metrics()["current_frame"]
    with mcrfpy.lock():
        dt = mcrfpy.step(STEP_SECONDS)
        mcrfpy.advance(16)
    after = mcrfpy.get_metrics()["current_frame"]

    check_true(f"step() inside a main-thread lock returned a real dt (got {dt!r})",
               isinstance(dt, float) and dt > 0.0)
    check_true(f"the frames actually ran ({before} -> {after})", after > before)

    # Non-vacuity for section 1: the SAME two calls, on the SAME engine, in the SAME
    # process, succeed on the main thread and raise on a background holder. The only
    # variable is which thread holds the lock. Without this, section 1 would be
    # satisfied by a step() that raised RuntimeError unconditionally.
    print("  (this is section 1's single-variable control: same calls, main thread)")


# ---------------------------------------------------------------------------
# Section 4 -- the deadlock itself
# ---------------------------------------------------------------------------
def section4_the_deadlock():
    """The three-thread arrangement that literally hangs pre-fix.

    Holder H acquires the lock. Waiter W then blocks in acquire(). H calls step().
    Pre-fix: the re-entered frame's closeWindow() waits for active == 0, but H's own
    hold IS the active count, and the main thread is parked in the outer frame's
    closeWindow() on the same count -- three threads, none able to move, no timeout
    anywhere. Post-fix H's step() raises, H's block exits, W proceeds, everything
    drains.

    The deadline is what makes a regression a reported FAILURE rather than a suite
    that never returns.
    """
    print("Section 4: the actual B7 deadlock arrangement completes instead of hanging")

    holder_in = threading.Event()      # H is inside the lock
    holder_done = threading.Event()
    waiter_done = threading.Event()
    result = {}

    # Both threads are started BEFORE the main loop begins driving frames. The holder
    # cannot wait for the waiter and the main thread cannot start the waiter after the
    # holder is in: once the holder is inside the lock, the main thread is parked in
    # closeWindow() and executes no Python at all until the holder releases. The
    # ordering is therefore established entirely between the two background threads,
    # via holder_in, which both can see with the GIL free.
    def holder():
        try:
            with mcrfpy.lock():
                holder_in.set()
                # Give W time to reach acquire() and register as `waiting`. That is
                # the precondition for the hang: with nobody waiting, hasWaiting()
                # short-circuits the safe window and the re-entered frame returns.
                time.sleep(0.15)
                try:
                    mcrfpy.step(STEP_SECONDS)
                    result["holder"] = "returned"
                except RuntimeError:
                    result["holder"] = "RuntimeError"
                except BaseException as exc:  # noqa: BLE001
                    result["holder"] = type(exc).__name__
        except BaseException as exc:  # noqa: BLE001
            result["holder_outer"] = repr(exc)
        finally:
            holder_done.set()

    def waiter():
        try:
            # Only queue up once the holder is demonstrably inside the lock, so this
            # thread is genuinely `waiting` when the holder re-enters the frame.
            if not holder_in.wait(5.0):
                result["waiter"] = "holder never entered the lock"
                return
            time.sleep(0.02)
            with mcrfpy.lock():
                probe.y = 55.0
            result["waiter"] = "ok"
        except BaseException as exc:  # noqa: BLE001
            result["waiter"] = repr(exc)
        finally:
            waiter_done.set()

    th = threading.Thread(target=holder, name="b7-holder", daemon=True)
    tw = threading.Thread(target=waiter, name="b7-waiter", daemon=True)
    th.start()
    tw.start()

    both = threading.Event()

    def watch():
        holder_done.wait(DEADLINE)
        waiter_done.wait(DEADLINE)
        both.set()

    threading.Thread(target=watch, daemon=True).start()
    fired, steps = drive_until(both, DEADLINE)

    th.join(timeout=2.0)
    tw.join(timeout=2.0)

    check_true(f"holder and waiter both finished within {DEADLINE}s "
               f"({steps} main-thread frames driven) -- pre-fix this hangs", fired)
    check_true(f"holder thread is not still parked ({th.is_alive()=})",
               not th.is_alive())
    check_true(f"waiter thread is not still parked ({tw.is_alive()=})",
               not tw.is_alive())
    check("holder's step() outcome", result.get("holder"), "RuntimeError")
    check("waiter got through the barrier", result.get("waiter"), "ok")
    check("the waiter's locked mutation landed", probe.y, 55.0)
    check_true(f"no exception escaped the holder's block "
               f"({result.get('holder_outer')})", "holder_outer" not in result)


# ---------------------------------------------------------------------------
# Section 5 -- the holder count is PER-THREAD, not global
# ---------------------------------------------------------------------------
def section5_per_thread_not_global():
    """A thread that holds nothing must not be refused because someone else holds.

    Sections 1-4 all pass if the holder count is a single process-wide counter rather
    than a per-thread one. Nothing there can tell the difference, and the reason is
    structural: the barrier guarantees `active == 0` whenever the MAIN thread is
    between frames, so the main thread can never observe another thread's hold at the
    moment it enters step(). A global counter is therefore invisible to every
    main-thread-driven assertion in this file. (Confirmed by mutation: replacing the
    thread_local with a plain static survived every other section.)

    The one construction that distinguishes them: thread H holds the lock and sleeps;
    thread B, holding nothing, calls step(). Per-thread -> B is allowed. Global -> B
    is refused, and a handler on any other thread breaks whenever a peer is inside a
    lock block.

    Since #411, B's call is refused anyway -- the main thread drives the clock, and only
    the clock's owner may run frames. The observable is now WHICH refusal B gets: a
    per-thread count yields the clock-ownership message, a global count the lock one.
    """
    print("Section 5: the holder count is per-thread, not process-wide")

    holder_in = threading.Event()
    holder_release = threading.Event()
    probe_done = threading.Event()
    result = {}

    def holder():
        try:
            with mcrfpy.lock():
                holder_in.set()
                # Hold long enough for B to make its call while this hold is live.
                holder_release.wait(3.0)
        except BaseException as exc:  # noqa: BLE001
            result["holder"] = repr(exc)

    def prober():
        try:
            if not holder_in.wait(5.0):
                result["probe"] = "holder never entered"
                return
            # B holds nothing. Under a per-thread counter this is allowed.
            try:
                mcrfpy.step(STEP_SECONDS)
                result["probe"] = "returned"
            except RuntimeError as exc:
                result["probe"] = refusal_kind(exc)
                result["probe_msg"] = str(exc)
            except BaseException as exc:  # noqa: BLE001
                result["probe"] = type(exc).__name__
        finally:
            holder_release.set()
            probe_done.set()

    th = threading.Thread(target=holder, name="b7-p-holder", daemon=True)
    tp = threading.Thread(target=prober, name="b7-prober", daemon=True)
    th.start()
    tp.start()
    fired, steps = drive_until(probe_done, DEADLINE)
    th.join(timeout=2.0)
    tp.join(timeout=2.0)

    check_true(f"probe finished within the deadline ({steps} frames)", fired)
    check_true(f"the holder raised nothing ({result.get('holder')})",
               "holder" not in result)
    check("a NON-holding thread is not refused for the lock while a PEER holds it "
          "(a global holder count would say 'lock' here; #411 refuses it for the clock)",
          result.get("probe"), "refused:clock")


section1_refusal()
section2_depth_accounting()
section3_main_thread_unaffected()
section4_the_deadlock()
section5_per_thread_not_global()

if failures:
    print(f"\n{len(failures)} FAILURE(S):")
    for f in failures:
        print(f"  FAILURE: {f}")
    sys.exit(1)

print("\nPASS")
sys.exit(0)
