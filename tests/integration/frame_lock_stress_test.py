"""Contention stress for mcrfpy.lock() -- the #219 FrameLock barrier (#395, #535).

WHAT THE BARRIER IS. `FrameLock` (src/GameEngine.h, src/GameEngine.cpp) is a frame
barrier, NOT a mutex. A background thread in `with mcrfpy.lock():` blocks in
FrameLock::acquire() until the main thread opens a "safe window" -- once per frame, in
doFrame() (windowed) and runSimFrame() (headless, driven by mcrfpy.step()/advance()) -- and
the main thread parks in closeWindow() until every holder is done. A lock block is
mutually exclusive WITH THE FRAME; it is not exclusive with other background holders, and
every holder of one window is inside it at once. Every non-nested lock() waits for the NEXT
window (#410/#535), so each acquire is served by exactly one frame.

NO MACHINE SPEED IN ANY GATE (#535). This file used to bound acquire waits in
milliseconds, compare per-worker wait TIMES for fairness, require a minimum frame count in
a wall-clock budget, and use sleeps to widen race windows; all of that failed on a loaded
machine without anything being wrong. The same properties, in counts and ordering:

  1  torn-state gate. Each worker owns a Frame pair (fa, fb). Inside the lock it sets fa.x,
     then PARKS until a releaser thread lets it go (an event handshake, not a sleep: the
     world is inconsistent for as long as the holder stays inside), then sets fb.x. The
     main thread scans every pair after each step(). closeWindow() cannot return until
     every holder has left, so no scan may ever see fa.x != fb.x. Gated at exactly 0.
  1b unlocked control. The scan must be able to see tearing at all, so the identical
     two-write workload runs with the lock removed and a Barrier in place of the sleep:
     the main thread scans while every worker is provably between its writes, so EVERY
     round must show a tear. Deterministic: the scan sees all of them or the scanner is
     blind.
  2  no starvation, no double service, exact fairness. Rendezvous: the main thread waits
     until all W workers are blocked in lock() (get_metrics 'lock_waiting' == W), then runs
     ONE frame. That frame must admit every worker exactly once ('lock_admissions' +W,
     'lock_windows' +1) and complete their blocks before step() returns: per-worker counts
     are all equal to the round number after each step. This replaces the old wall-clock
     "max acquire wait" and "ratio of per-worker wait times" gates: "served by the first
     window after being seen waiting" is the count-valued form of "not starved".
  3  progress. ITERATIONS rounds x WORKERS admissions, exactly; a run in which the main
     loop wedged and only the workers ran cannot produce those counts.
  4  non-vacuity. Every worker saw ITERATIONS distinct current_frame values from inside
     the lock (one window per acquire, #410).
  5  nesting. `with lock(): with lock(): ...` from a background thread works -- the inner
     acquire is admitted at once -- and frames keep advancing after the outer release.

WHY A CHILD PROCESS and what "hang" means: see tests/integration/_frame_lock_supervisor.py.
A hang is "no progress for STALL_SECONDS", never a performance bound.

WHAT THIS COVERAGE FOUND (#412, fixed). The first run of this file at WORKERS=8 wedged the
engine: FrameLock::acquire() took its mutex WHILE HOLDING THE GIL, so a thread woken from
cv.wait() held `mtx` and blocked on the GIL while any second thread entering acquire()
held the GIL and blocked on `mtx` -- an ABBA inversion that stopped the interpreter. Two
concurrent background lock users were enough. acquire() now releases the GIL BEFORE taking
`mtx`.

The time-valued numbers this file once gated (acquire-wait distribution, fairness of wait
times) are reported, with no threshold, by tests/benchmarks/frame_lock_soak_bench.py.

Run: ./mcrogueface --headless --exec ../tests/integration/frame_lock_stress_test.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _frame_lock_supervisor as sup

WORKERS = 8
ITERATIONS = 40

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)
    return condition


STRESS_BODY = r'''
import json, queue, sys, threading, time
import mcrfpy

scene = mcrfpy.Scene("frame_lock_stress")
mcrfpy.current_scene = scene

# One Frame PAIR per worker (Frame.x, not Entity.cell_pos: see the soak test's fixture note).
A, B = [], []
for r in range(WORKERS):
    fa = mcrfpy.Frame(pos=(0, r * 4), size=(4, 4))
    fb = mcrfpy.Frame(pos=(0, r * 4), size=(4, 4))
    scene.children.append(fa)
    scene.children.append(fb)
    A.append(fa)
    B.append(fb)

counts = [0] * WORKERS
frames_seen = [set() for _ in range(WORKERS)]
self_torn = [0] * WORKERS
errors = []
steps_box = [0]
stop_hb = threading.Event()

# LOCKED: a holder parks between its two writes until the releaser lets it go.
parked = queue.Queue()
release = [threading.Event() for _ in range(WORKERS)]
# not LOCKED: two Barriers stand in for the lock. Workers write fa, meet the main thread
# (which scans), then write fb.
mid = threading.Barrier(WORKERS + 1)
after_scan = threading.Barrier(WORKERS + 1)


def releaser():
    while True:
        r = parked.get()
        if r is None:
            return
        release[r].set()


def worker(r):
    fa, fb = A[r], B[r]
    try:
        for i in range(ITERATIONS):
            value = float(i % 50 + 1)
            if LOCKED:
                with mcrfpy.lock():
                    # Section 1, worker side: my own pair must be consistent on entry.
                    if fa.x != fb.x:
                        self_torn[r] += 1
                    frames_seen[r].add(mcrfpy.get_metrics()["current_frame"])
                    fa.x = value
                    release[r].clear()
                    parked.put(r)
                    release[r].wait()       # inconsistent world, for as long as we stay
                    fb.x = value
                    counts[r] += 1          # inside the block: step() returning implies it
            else:
                fa.x = value
                mid.wait()                  # main scans now: every pair is between writes
                after_scan.wait()
                fb.x = value
                counts[r] += 1
    except BaseException as exc:
        errors.append("worker %d: %r" % (r, exc))


def heartbeat():
    # Its own thread on purpose: the main thread parks in closeWindow() with the GIL
    # released, so this keeps printing through a legitimate park and goes silent only if
    # the GIL itself is wedged. The payload is the progress token the supervisor watches.
    while not stop_hb.is_set():
        m = mcrfpy.get_metrics()
        print("HB steps=%d counts=%d adm=%d waiting=%d" % (
            steps_box[0], sum(counts), m["lock_admissions"], m["lock_waiting"]), flush=True)
        time.sleep(0.05)


def spin_until(pred):
    while not pred():
        time.sleep(0.0005)      # the supervisor's progress token is the hang detector


threading.Thread(target=heartbeat, name="hb", daemon=True).start()
rel_t = threading.Thread(target=releaser, name="releaser", daemon=True)
rel_t.start()
threads = [threading.Thread(target=worker, args=(r,), name="w%d" % r, daemon=True)
           for r in range(WORKERS)]
for t in threads:
    t.start()

torn_main = 0
scans = 0
fair_violations = []
round_violations = []
if LOCKED:
    for rnd in range(ITERATIONS):
        spin_until(lambda: mcrfpy.get_metrics()["lock_waiting"] == WORKERS)
        before = mcrfpy.get_metrics()
        mcrfpy.step(0.016)
        steps_box[0] += 1
        after = mcrfpy.get_metrics()
        adm = after["lock_admissions"] - before["lock_admissions"]
        win = after["lock_windows"] - before["lock_windows"]
        if adm != WORKERS or win != 1:
            round_violations.append("round %d: admissions +%d (want %d), windows +%d (want 1)"
                                    % (rnd, adm, WORKERS, win))
        if counts != [rnd + 1] * WORKERS:
            fair_violations.append("round %d: counts %r" % (rnd, counts))
        # Section 1, main-thread side: closeWindow() has drained every holder.
        scans += 1
        for r in range(WORKERS):
            if A[r].x != B[r].x:
                torn_main += 1
                break
else:
    for rnd in range(ITERATIONS):
        mid.wait()
        scans += 1
        torn_pairs = sum(1 for r in range(WORKERS) if A[r].x != B[r].x)
        if torn_pairs == WORKERS:
            torn_main += 1
        steps_box[0] += 1
        after_scan.wait()

for t in threads:
    t.join()
parked.put(None)
stop_hb.set()
rel_t.join()

print("RESULT " + json.dumps({
    "locked": bool(LOCKED),
    "steps": steps_box[0],
    "scans": scans,
    "torn_main": torn_main,
    "self_torn": self_torn,
    "counts": counts,
    "total": sum(counts),
    "expected": WORKERS * ITERATIONS,
    "distinct_frames": [len(s) for s in frames_seen],
    "round_violations": round_violations,
    "fair_violations": fair_violations,
    "errors": errors,
}), flush=True)
sys.exit(0)
'''


NEST_BODY = r'''
import json, sys, threading, time
import mcrfpy

scene = mcrfpy.Scene("frame_lock_nest")
mcrfpy.current_scene = scene
target = mcrfpy.Frame(pos=(0, 0), size=(4, 4))
scene.children.append(target)

state = {"outer": False, "inner": False, "value": None,
         "outer_frame": None, "inner_frame": None, "rounds": 0}
errors = []
stop_hb = threading.Event()
steps_box = [0]


def nester():
    try:
        for i in range(NEST_ROUNDS):
            with mcrfpy.lock():
                state["outer"] = True
                state["outer_frame"] = mcrfpy.get_metrics()["current_frame"]
                with mcrfpy.lock():
                    # Admitted at once: if it waited for a NEXT window, the outer holder
                    # would never release and closeWindow() would never return.
                    state["inner"] = True
                    state["inner_frame"] = mcrfpy.get_metrics()["current_frame"]
                    target.x = float(i + 1)
                state["value"] = target.x
                state["rounds"] += 1
    except BaseException as exc:
        errors.append(repr(exc))


def heartbeat():
    while not stop_hb.is_set():
        print("HB nest steps=%d rounds=%d" % (steps_box[0], state["rounds"]), flush=True)
        time.sleep(0.05)


threading.Thread(target=heartbeat, daemon=True).start()
t = threading.Thread(target=nester, name="nester", daemon=True)
t.start()

for rnd in range(NEST_ROUNDS):
    while mcrfpy.get_metrics()["lock_waiting"] != 1:
        time.sleep(0.0005)
    mcrfpy.step(0.016)
    steps_box[0] += 1
t.join()

# The outer release must leave the barrier in a state where frames still advance.
frame_before = mcrfpy.get_metrics()["current_frame"]
for _ in range(200):
    mcrfpy.step(0.016)
frame_after = mcrfpy.get_metrics()["current_frame"]
stop_hb.set()

print("RESULT " + json.dumps({
    "outer": state["outer"],
    "inner": state["inner"],
    "value": state["value"],
    "rounds": state["rounds"],
    "same_frame": state["outer_frame"] == state["inner_frame"],
    "frames_after_release": frame_after - frame_before,
    "errors": errors,
    "alive": t.is_alive(),
}), flush=True)
sys.exit(0)
'''


common = dict(WORKERS=WORKERS, ITERATIONS=ITERATIONS)

locked_verdict, locked, locked_info = sup.run_child(
    "locked-stress", sup.child_source(STRESS_BODY, LOCKED=True, **common))
control_verdict, control, control_info = sup.run_child(
    "unlocked-control", sup.child_source(STRESS_BODY, LOCKED=False, **common))
NEST_ROUNDS = 8
nest_verdict, nest, nest_info = sup.run_child(
    "nesting", sup.child_source(NEST_BODY, NEST_ROUNDS=NEST_ROUNDS))

print()
print("child             | verdict  | heartbeats | last heartbeat")
print("------------------+----------+------------+---------------")
for label, verdict, info in (("locked-stress", locked_verdict, locked_info),
                             ("unlocked-control", control_verdict, control_info),
                             ("nesting", nest_verdict, nest_info)):
    print("%-17s | %-8s | %10d | %s" % (label, verdict, info["heartbeats"], info["last_heartbeat"]))
print()

if locked:
    print("locked stress (%d workers x %d iterations)" % (WORKERS, ITERATIONS))
    print("  mutations                    : %d of %d expected" % (locked["total"], locked["expected"]))
    print("  per-worker counts            : %s" % (locked["counts"],))
    print("  main-thread scans / torn     : %d / %d" % (locked["scans"], locked["torn_main"]))
    print("  worker self-torn (gated 0)   : %s" % (locked["self_torn"],))
    print("  distinct frames per worker   : %s" % (locked["distinct_frames"],))
    print("  worker errors                : %s" % (locked["errors"],))
if control:
    print("unlocked control                : %d fully-torn scans out of %d" % (control["torn_main"], control["scans"]))
if nest:
    print("nesting                         : outer=%s inner=%s value=%s same_frame=%s "
          "frames_after_release=%d errors=%s"
          % (nest["outer"], nest["inner"], nest["value"], nest["same_frame"],
             nest["frames_after_release"], nest["errors"]))
print()

if locked_verdict != "ok" or locked is None:
    check(False, sup.wedge_message("locked-stress", locked_verdict, locked_info))
else:
    check(not locked["errors"], "locked workers raised: %s" % (locked["errors"],))
    # 1 -- torn state
    check(locked["torn_main"] == 0,
          "the main thread observed %d torn pairs out of %d scans between step() calls; "
          "closeWindow() has drained every holder by then, so this must be exactly 0"
          % (locked["torn_main"], locked["scans"]))
    check(sum(locked["self_torn"]) == 0,
          "workers found their own pair inconsistent on entering the lock %s times; a "
          "worker is the only writer of its own pair, so this must be 0" % (locked["self_torn"],))
    # 2 -- exactly one service per worker per window, for every worker, every round
    check(not locked["round_violations"],
          "a frame did not admit exactly one holder per worker in one window: %s"
          % (locked["round_violations"][:3],))
    check(not locked["fair_violations"],
          "after a frame, some worker had been served a different number of times than its "
          "peers (starved or served twice): %s" % (locked["fair_violations"][:3],))
    # 3 -- progress, exact
    check(locked["counts"] == [ITERATIONS] * WORKERS,
          "not every worker completed exactly %d iterations: %s" % (ITERATIONS, locked["counts"]))
    check(locked["total"] == locked["expected"],
          "total mutations %d != %d expected" % (locked["total"], locked["expected"]))
    # 4 -- one window per acquire
    for r, distinct in enumerate(locked["distinct_frames"]):
        check(distinct == ITERATIONS,
              "worker %d saw %d distinct current_frame values for %d acquires: it was "
              "re-admitted within a window that had already served it (#410)"
              % (r, distinct, ITERATIONS))

# 1b -- the mutation check that makes section 1 non-vacuous.
if control_verdict != "ok" or control is None:
    check(False, sup.wedge_message("unlocked-control", control_verdict, control_info))
else:
    check(not control["errors"], "control workers raised: %s" % (control["errors"],))
    check(control["torn_main"] == ITERATIONS,
          "the unlocked control showed a tear in %d of %d rounds; every worker was provably "
          "between its two writes at every scan, so anything but %d means the main-thread "
          "scan cannot see tearing and section 1's gate is vacuous"
          % (control["torn_main"], ITERATIONS, ITERATIONS))
    check(control["total"] == control["expected"],
          "unlocked control performed %d of %d mutations" % (control["total"], control["expected"]))

# 5 -- nesting
if nest_verdict != "ok" or nest is None:
    check(False, sup.wedge_message("nesting", nest_verdict, nest_info))
else:
    check(not nest["errors"], "nesting thread raised: %s" % (nest["errors"],))
    check(nest["outer"], "the outer `with mcrfpy.lock():` never entered")
    check(nest["inner"], "the inner `with mcrfpy.lock():` never entered")
    check(nest["rounds"] == NEST_ROUNDS,
          "the nesting thread completed %d of %d rounds, each served by one frame"
          % (nest["rounds"], NEST_ROUNDS))
    check(nest["same_frame"],
          "the nested acquire reported a different current_frame than the outer one; both are "
          "inside one open window, so they are one barrier instant")
    check(nest["value"] == float(NEST_ROUNDS),
          "the mutation made inside the nested block did not land (value=%s)" % (nest["value"],))
    check(nest["frames_after_release"] == 200,
          "%d of 200 frames advanced after the outer release" % nest["frames_after_release"])
    check(not nest["alive"], "the nesting thread is still running")

if failures:
    for message in failures:
        print("FAILURE: %s" % message)
    sys.exit(1)

print("PASS")
sys.exit(0)
