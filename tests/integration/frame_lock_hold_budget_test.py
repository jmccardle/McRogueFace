"""The hold-time-to-frame-time budget for mcrfpy.lock() -- the measurement half of #395.

WHY THIS EXISTS
===============
The rule for background threads is "inside the lock, mutate only -- no I/O, no
blocking wait, no frame advance". That rule is unenforceable if nobody knows what a
violation costs, because the cost does not present as "a handler is misbehaving": the
main thread parks in FrameLock::closeWindow() until every holder releases, so a slow
handler is indistinguishable from engine stutter. This file produces the number, and
it is a test rather than a one-off benchmark so the number cannot rot.

THE EXPERIMENT
==============
Single variable. A background thread performs exactly ONE handler-shaped unit of work
per main-loop iteration, sleeping for H milliseconds:

  treatment arm : the sleep happens INSIDE `with mcrfpy.lock():`
  control arm   : the same thread, the same sleep, the same H, the same one-per-frame
                  handoff -- but the sleep happens OUTSIDE the lock and the lock block
                  is empty.

Both arms hold the GIL identically (time.sleep releases it), do the same number of
acquires, and are driven by the same main loop. The ONLY difference is which side of
the barrier the H milliseconds are spent on. The main thread times each individual
mcrfpy.step() call and takes the worst frame of the iteration -- the frame that served
the holder.

WHAT IT ASSERTS
===============
  1. TREATMENT: cost per millisecond held is ~1:1. Least-squares slope of peak frame
     time against H must land in [0.6, 1.4]. Not "it gets slower" -- the coefficient,
     because the coefficient is the thing a rule can be written against.
  2. CONTROL: the same sleep outside the lock costs the frame nothing. Slope < 0.15.
  3. SEPARATION: treatment slope is at least 5x the control slope. This is what stops
     the treatment result from being "sleeping anywhere slows the engine down".
  4. The barrier's own fixed overhead (the H = 0 intercept) is small -- gated in
     absolute terms so a barrier that became expensive per acquire is caught even
     though the slope would be unchanged.
  5. NON-VACUITY: every arm must actually have acquired the lock the expected number
     of times, and the main loop must actually have run frames. A run where the holder
     never acquired would otherwise report a flat, beautiful, meaningless slope.

The numbers this file prints are the ones documented in docs/frame-lock.md. Re-run it
to regenerate them:

  cd build && ./mcrogueface --headless --exec ../tests/integration/frame_lock_hold_budget_test.py
"""

import statistics
import sys
import threading
import time

import mcrfpy

# Holds in milliseconds. The top of the range is deliberately past a 60 fps frame
# budget (16.67 ms), because the interesting question is not "is a 1 ms hold cheap"
# but "where does a hold start costing whole frames".
HOLDS_MS = [0.0, 1.0, 2.0, 4.0, 8.0, 16.0]
ITERATIONS = 12          # handler invocations measured per (arm, H) cell
STEP_SECONDS = 0.016
ITER_DEADLINE = 2.0      # per-iteration hard deadline; a hang becomes a FAILURE

failures = []


def check_true(label, cond):
    if not cond:
        failures.append(label)
        print(f"  FAILURE: {label}")
    else:
        print(f"  ok  {label}")


scene = mcrfpy.Scene("hold_budget")
mcrfpy.current_scene = scene


def measure(hold_ms, inside_lock):
    """One (arm, H) cell. Returns (median_peak_frame_ms, acquires, frames, timeouts).

    The holder does exactly one acquire per main-loop iteration and signals `ready`
    immediately before calling into the barrier, so the main thread does not spin
    through thousands of empty frames waiting for the OS to schedule it -- that spin
    would put the measurement's noise floor above the effect being measured.
    """
    hold_s = hold_ms / 1000.0
    go = threading.Event()
    ready = threading.Event()
    done = threading.Event()
    stop = threading.Event()
    acquires = [0]

    def holder():
        while True:
            if not go.wait(0.5):
                if stop.is_set():
                    return
                continue
            go.clear()
            if stop.is_set():
                return
            if inside_lock:
                ready.set()
                with mcrfpy.lock():
                    if hold_s:
                        time.sleep(hold_s)
            else:
                if hold_s:
                    time.sleep(hold_s)
                ready.set()
                with mcrfpy.lock():
                    pass
            acquires[0] += 1
            done.set()

    thread = threading.Thread(target=holder, name="hold-budget", daemon=True)
    thread.start()

    peaks = []
    frames = 0
    timeouts = 0
    for _ in range(ITERATIONS):
        done.clear()
        ready.clear()
        go.set()
        # Wait (GIL released) until the holder is at the barrier's door, then give it
        # a moment to actually register as `waiting` so this frame serves it.
        ready.wait(1.0)
        time.sleep(0.002)

        worst = 0.0
        deadline = time.monotonic() + ITER_DEADLINE
        while not done.is_set() and time.monotonic() < deadline:
            t0 = time.perf_counter()
            mcrfpy.step(STEP_SECONDS)
            dt = (time.perf_counter() - t0) * 1000.0
            if dt > worst:
                worst = dt
            frames += 1
        if not done.is_set():
            timeouts += 1
        peaks.append(worst)

    stop.set()
    go.set()
    # Drain: the holder may be parked in acquire(); it needs safe windows to get out.
    for _ in range(50):
        mcrfpy.step(STEP_SECONDS)
    thread.join(timeout=2.0)
    if thread.is_alive():
        timeouts += 100  # forces the non-vacuity gate below to fail, loudly

    return statistics.median(peaks), acquires[0], frames, timeouts


def slope(xs, ys):
    """Least-squares slope of ys against xs. ms of frame time per ms of hold."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den


print("Measuring: one handler invocation per frame, sleep INSIDE vs OUTSIDE the lock")
print()
print("  hold(ms) | treatment: peak frame(ms) | control: peak frame(ms)")
print("  ---------+--------------------------+------------------------")

treat, ctrl = [], []
treat_acq = ctrl_acq = 0
treat_frames = ctrl_frames = 0
timeouts = 0

for h in HOLDS_MS:
    t_peak, t_acq, t_fr, t_to = measure(h, inside_lock=True)
    c_peak, c_acq, c_fr, c_to = measure(h, inside_lock=False)
    treat.append(t_peak)
    ctrl.append(c_peak)
    treat_acq += t_acq
    ctrl_acq += c_acq
    treat_frames += t_fr
    ctrl_frames += c_fr
    timeouts += t_to + c_to
    print(f"  {h:8.1f} | {t_peak:24.3f} | {c_peak:22.3f}")

treat_slope = slope(HOLDS_MS, treat)
ctrl_slope = slope(HOLDS_MS, ctrl)
intercept = treat[0]  # the H = 0 cell: the barrier's own per-acquire cost

print()
print(f"  treatment slope (frame ms per ms held inside the lock) : {treat_slope:.3f}")
print(f"  control   slope (frame ms per ms slept outside)        : {ctrl_slope:.4f}")
print(f"  barrier overhead at H=0 (peak frame ms)                : {intercept:.3f}")
print(f"  acquires: treatment {treat_acq}, control {ctrl_acq} "
      f"(expected {len(HOLDS_MS) * ITERATIONS} each)")
print(f"  frames driven: treatment {treat_frames}, control {ctrl_frames}")
print()
print("  THE BUDGET, stated so a rule can be written against it:")
print("    Time spent inside mcrfpy.lock() is added to the frame that serves it,")
print("    approximately 1:1. At a 60 fps budget (16.67 ms/frame) a handler holding")
print(f"    H ms leaves {16.67:.2f} - H - (this frame's own work) ms of headroom;")
print("    a hold at or above the frame budget drops a frame outright, and it")
print("    presents as engine stutter with nothing pointing at the handler.")
print()

# --- The greedy re-acquire regime (issue #410) ----------------------------------
#
# Everything above assumes what the intended topology actually does: ONE lock block per
# inbound event, with a yield to a frame in between. A thread that releases and
# immediately re-acquires is a different and much worse regime, because
# FrameLock::closeWindow() waits for `waiting == 0` while `safe_window` is still open --
# so a thread that re-enters acquire() at once is served AGAIN inside the same window
# and the window never closes. The barrier places no bound on services per frame.
#
# This block MEASURES that regime so the numbers in docs/frame-lock.md and issue #410
# are re-runnable. It deliberately gates only LIVENESS -- the main loop must still make
# progress and the thread must still shut down -- for two reasons: the magnitude is
# machine-dependent and would be a flaky gate, and #410's eventual fix will move the
# frame count UP, so a gate on the current magnitude would fail on the fix.

GREEDY_SECONDS = 0.6
print("Greedy re-acquire regime (issue #410) -- measurement, liveness-gated only:")
print("  hold(ms) | main frames | median frame(ms) | acquires | served per frame")

greedy_rows = []
for h in (0.0, 1.0):
    stop = threading.Event()
    n = [0]

    def greedy(hold_s=h / 1000.0):
        while not stop.is_set():
            with mcrfpy.lock():
                n[0] += 1
                if hold_s:
                    time.sleep(hold_s)

    gt = threading.Thread(target=greedy, name="greedy", daemon=True)
    gt.start()
    time.sleep(0.05)
    fts = []
    end = time.perf_counter() + GREEDY_SECONDS
    while time.perf_counter() < end:
        t0 = time.perf_counter()
        mcrfpy.step(STEP_SECONDS)
        fts.append((time.perf_counter() - t0) * 1000.0)
    stop.set()
    # Drain: the thread may be parked in acquire() and needs safe windows to leave.
    drain_end = time.monotonic() + 3.0
    while gt.is_alive() and time.monotonic() < drain_end:
        mcrfpy.step(STEP_SECONDS)
    gt.join(timeout=1.0)
    med = statistics.median(fts) if fts else float("nan")
    ratio = n[0] / max(len(fts), 1)
    greedy_rows.append((h, len(fts), med, n[0], ratio, gt.is_alive()))
    print(f"  {h:8.1f} | {len(fts):11} | {med:16.4f} | {n[0]:8} | {ratio:15.1f}")

print("  (see issue #410: one thread with a 1 ms hold can cost the main loop four")
print("   orders of magnitude of frame rate without deadlocking or logging anything)")
print()

# --- Gates ---------------------------------------------------------------------
print("Gates:")

for h, nframes, med, nacq, ratio, still_alive in greedy_rows:
    check_true(f"greedy H={h}ms: the main loop still made progress "
               f"({nframes} frames in {GREEDY_SECONDS}s) -- not a livelock",
               nframes >= 1)
    check_true(f"greedy H={h}ms: the greedy thread really did acquire "
               f"({nacq} acquires) -- non-vacuity", nacq >= 10)
    check_true(f"greedy H={h}ms: the greedy thread shut down and is not parked "
               f"in acquire()", not still_alive)

# (5) non-vacuity first: without these, every slope below is meaningless.
expected_acq = len(HOLDS_MS) * ITERATIONS
check_true(f"treatment acquired the lock {expected_acq} times (got {treat_acq})",
           treat_acq == expected_acq)
check_true(f"control acquired the lock {expected_acq} times (got {ctrl_acq})",
           ctrl_acq == expected_acq)
check_true(f"no iteration hit its deadline and no holder was left parked "
           f"(timeouts={timeouts})", timeouts == 0)
check_true(f"the main loop actually ran frames in both arms "
           f"({treat_frames}, {ctrl_frames})",
           treat_frames >= len(HOLDS_MS) * ITERATIONS and
           ctrl_frames >= len(HOLDS_MS) * ITERATIONS)

# (1) the coefficient.
check_true(f"a millisecond held inside the lock costs the frame ~a millisecond: "
           f"slope {treat_slope:.3f} in [0.6, 1.4]",
           0.6 <= treat_slope <= 1.4)

# (2) the control.
check_true(f"the same sleep OUTSIDE the lock costs the frame nothing: "
           f"slope {ctrl_slope:.4f} < 0.15", ctrl_slope < 0.15)

# (3) separation -- the single-variable claim.
check_true(f"treatment slope is at least 5x the control slope "
           f"({treat_slope:.3f} vs {ctrl_slope:.4f})",
           treat_slope >= 5.0 * max(ctrl_slope, 1e-6))

# (4) the barrier's own fixed cost, absolute.
check_true(f"the barrier's per-acquire overhead is under 2 ms "
           f"(H=0 peak frame {intercept:.3f} ms)", intercept < 2.0)

# The largest hold must actually exceed a 60 fps frame budget, otherwise the
# headline claim ("a hold at the frame budget drops a frame") is asserted over a
# range that never reaches it.
check_true(f"the measured range reaches a 60 fps frame budget: peak at "
           f"H={HOLDS_MS[-1]}ms is {treat[-1]:.3f} ms, gate is > 15.67 ms "
           f"(one ms under the 16.67 ms budget, so the claim is asserted over a "
           f"range that actually reaches it)",
           treat[-1] > 15.67)

if failures:
    print(f"\n{len(failures)} FAILURE(S):")
    for f in failures:
        print(f"  FAILURE: {f}")
    sys.exit(1)

print("\nPASS")
sys.exit(0)
