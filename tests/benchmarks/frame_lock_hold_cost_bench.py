"""Hold-time-to-frame-time cost of mcrfpy.lock() -- a REPORTED MEASUREMENT (#395, #535).

This was tests/integration/frame_lock_hold_budget_test.py, which gated the numbers below
(slope in [0.6, 1.4], overhead < 2 ms, ...). Those gates asserted machine speed, so they
failed whenever the machine was busy (#535). The properties that are NOT about speed
(a holder is served by the frame that finds it waiting; the main thread is parked exactly
while a holder is inside; at most one service per window) moved to
tests/integration/frame_lock_hold_ordering_test.py and are expressed in counts.

What remains here is the genuinely time-valued claim -- "holding the lock for H ms delays
the frame by about H ms" -- which cannot be tested without a clock. It is a report with no
pass/fail threshold; the numbers in docs/frame-lock.md come from it. It exits 0 unless a
thread hangs (a deadlock is still a failure).

THE EXPERIMENT
==============
Single variable. A background thread performs exactly ONE handler-shaped unit of work
per main-loop iteration, sleeping for H milliseconds:

  treatment arm : the sleep happens INSIDE `with mcrfpy.lock():`
  control arm   : the same sleep OUTSIDE the lock, the lock block empty.

The main thread times each mcrfpy.step() and takes the worst frame of the iteration.

  cd build && ./mcrogueface --headless --exec ../tests/benchmarks/frame_lock_hold_cost_bench.py
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
ITER_DEADLINE = 30.0     # hang detector only: a hang becomes a FAILURE

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

# --- Report (no thresholds) ------------------------------------------------------
# Only liveness is checked: every holder acquired, nothing hung, no thread left parked.
expected_acq = len(HOLDS_MS) * ITERATIONS
hung = (timeouts != 0 or treat_acq != expected_acq or ctrl_acq != expected_acq
        or any(r[5] for r in greedy_rows))
if hung:
    print(f"FAIL: deadlock/hang: acquires treatment={treat_acq} control={ctrl_acq} "
          f"(expected {expected_acq} each), timeouts={timeouts}")
    sys.exit(1)

print("REPORTED (no pass/fail threshold): slopes and overheads above are machine-dependent")
print("PASS")
sys.exit(0)
