"""Contention stress for mcrfpy.lock() -- the #219 FrameLock barrier (#395).

WHAT THE BARRIER IS. `FrameLock` (src/GameEngine.h, src/GameEngine.cpp) is a frame
barrier, NOT a mutex. A background thread in `with mcrfpy.lock():` blocks in
FrameLock::acquire() until the main thread opens a "safe window" -- once per frame,
after the frame's work and before currentFrame++, in doFrame() (windowed) and
runSimFrame() (headless, driven by mcrfpy.step()/advance()). The main thread then
parks in closeWindow() until every holder is done. So a lock block is mutually
exclusive WITH THE FRAME. It is NOT mutually exclusive with other background
holders: openWindow() is a single wake-all, `active` counts holders, and several
threads can be inside one open window simultaneously. Every gate below is phrased
against that real contract, not against "it behaves like a mutex".

WHY THE WORK RUNS IN A CHILD PROCESS. This is a standing property of the subject,
not a workaround for any particular bug. FrameLock::acquire() waits on a condition
variable with NO timeout, so every failure mode of this barrier is a hang, and a
hang here is total: the main thread blocks inside mcrfpy.step(), and the Python
threads block on the GIL, so no in-process watchdog can fire, no deadline can be
checked and no message can be printed. A test that cannot report its own failure is
not a test. The only way to turn "the engine wedged" into a FAILURE with a message
instead of a hung suite is to run the contended workload in a child process of this
same binary and supervise it from outside.
tests/integration/random_seed_replay_test.py already establishes the child-process
pattern here; this file supervises with a stall detector as well as a hard deadline,
so a wedge is reported in ~1.5s rather than by burning the whole budget.

The child emits a heartbeat from a WATCHDOG THREAD, not from the main loop. That
distinction is diagnostic: the main thread parking in closeWindow() is legitimate
(it releases the GIL while parked, so the watchdog keeps printing), whereas a GIL
wedge silences everything. So "heartbeats stopped entirely" and "heartbeats continued
but the step count froze" are different findings, and the failure text says which.

SECTIONS
  1  torn-state gate. Each worker owns its OWN Frame pair (fa, fb) and, inside the
     lock, sets fa.x, sleeps (releasing the GIL, world momentarily inconsistent),
     then sets fb.x. The main thread scans every pair after each step(). Because the
     safe window only opens INSIDE a frame and closeWindow() will not return until
     active == 0, no scan between step() calls may ever see fa.x != fb.x. Gated at
     exactly 0. Private pairs, not a shared pair: the barrier does not serialize
     background threads against each other, so a shared pair would tear legitimately
     whenever two holders were in the same window, and the gate would be measuring
     thread interleaving rather than the frame boundary.
  1b unlocked control. Section 1 is worthless if the scan cannot see tearing at all,
     so the identical workload is re-run with `with mcrfpy.lock():` removed and
     nothing else changed. That run must tear. (Measured: ~700000 torn scans out of
     ~704000 -- see MEASUREMENTS.)
  2  starvation gate (the #398 class). Every worker must complete ALL its iterations,
     and no single acquire may exceed MAX_ACQUIRE_WAIT_MS.
  3  main-thread progress. current_frame must advance by MIN_FRAMES during the
     stress, so a "pass" in which the main loop was wedged and only the workers ran
     is impossible.
  4  non-vacuity. Total mutations must equal WORKERS * ITERATIONS exactly, and every
     worker must have observed at least MIN_DISTINCT_FRAMES distinct current_frame
     values from inside the lock (i.e. really crossed frame boundaries).
  5  nesting. `with mcrfpy.lock(): with mcrfpy.lock(): ...` from a background thread
     must work -- the inner acquire succeeds while the window is already open -- and
     frames must keep advancing after the outer release.

WHAT THIS COVERAGE FOUND (#412, fixed). The first run of this file at WORKERS=8
wedged the engine outright. FrameLock::acquire() used to take its mutex WHILE
HOLDING THE GIL:

    void FrameLock::acquire() {
        waiting++;
        std::unique_lock<std::mutex> lock(mtx);   // <-- GIL still held here
        Py_BEGIN_ALLOW_THREADS
        cv.wait(lock, [this]{ return safe_window; });
        Py_END_ALLOW_THREADS                      // <-- mtx still held here

so a thread woken from cv.wait() held `mtx` and blocked re-acquiring the GIL, while
any second thread entering acquire() held the GIL and blocked on `mtx` -- an ABBA
inversion between the GIL and FrameLock::mtx that wedged the whole interpreter (the
main thread then blocked on `mtx` in closeWindow(), and every Python thread blocked
on the GIL). Confirmed by backtrace: one thread parked in take_gil() under
FrameLock::acquire(), another in pthread_mutex_lock() under FrameLock::acquire().
It needed exactly TWO concurrent background lock users and triggered within
milliseconds; measured at 2, 3, 4 and 8 workers, at gaps of 0, 1 and 5 ms. One lock
user never tripped it, which is why it survived #219 and #398 -- neither had
contention coverage. acquire() now releases the GIL BEFORE taking `mtx` and
re-acquires it only after `mtx` is dropped. Filed and fixed as #412.

MEASUREMENTS behind the thresholds (this machine, build/mcrogueface post-#412,
2026-07-27), 20 runs at the shipped WORKERS=8, ITERATIONS=40, 1 ms gap:

    overall acquire wait ms      max 0.516 - 0.937      median 0.071 - 0.200
    per-worker SUM  wait ratio   1.165 - 1.660   mean 1.373  sd 0.163
    per-worker MAX  wait ratio   1.272 - 1.912
    per-worker MEDIAN    ratio   1.476 - 13.983
    main-loop frames             ~144000 - 175000 during a ~0.27 s stress
    distinct frames per worker   40 of 40 iterations, every worker, every run
    unlocked control (1b)        ~700000 torn scans of ~704000

  MAX_ACQUIRE_WAIT_MS = 50 (scaled by MCRF_TIMEOUT_MULTIPLIER). Observed max
    0.937 ms, so 53x the measurement. It is deliberately not tighter: Python's
    default GIL switch interval is 5 ms, and with 8 threads a fair-but-loaded
    acquire can legitimately queue behind several switch intervals, so a gate near
    the measurement would be gating GIL scheduling rather than the barrier. What it
    does catch is STARVATION -- the #398/#412 failure shape, where a wait is
    unbounded rather than merely large. It is not, and does not claim to be, an
    acquire-latency regression gate.
  FAIRNESS_RATIO = 3.0 on the per-worker SUM of acquire waits, i.e. 1.8x the worst
    of 20 runs and mean + 10 sd. The statistic matters more than the number here:
    the per-worker MEDIAN ratio ranged 1.476-13.983 over the same runs and is not
    gateable at any threshold that would still detect anything, because acquire wait
    is bimodal (near zero if the safe window is already open, a frame-service
    latency if not) and a median over 40 samples flips between the two modes. The
    sum integrates all 40 and has sd = 12% of its own mean, so it can be gated close
    enough to catch a worker being starved 3x relative to its peers.
  MIN_FRAMES = 100. Measured ~150000. Three decimal orders of margin, and still
    impossible to satisfy with a wedged main loop.
  MIN_DISTINCT_FRAMES = 2. Measured 40 (one per iteration, because the 1 ms gap lets
    the window close between iterations). 2 is the minimum that proves a boundary was
    crossed at all.

THE GATES WERE VERIFIED TO FAIL on the fixed engine, by mutating scratch copies
(never the shipped file) -- literal outputs in the report accompanying this change:
  - a worker that skips `with mcrfpy.lock():` entirely -> the torn-state gate fires.
  - a main loop that stops calling mcrfpy.step() partway (and a drain that does not
    step either) -> the completion, total-mutations and still-alive gates fire, and
    the run EXITS rather than hanging.
Nothing else was changed in either mutant.

Run: ./mcrogueface --headless --exec ../tests/integration/frame_lock_stress_test.py
"""

import json
import os
import subprocess
import sys
import threading
import time

# ---- workload shape -------------------------------------------------------
WORKERS = 8
ITERATIONS = 40
GAP_SECONDS = 0.001      # between iterations: lets the safe window close, so each
                         # iteration crosses a real frame boundary (measured: 40
                         # distinct frames for 40 iterations)
TORN_SECONDS = 0.0002    # inside the lock, between the two writes: releases the GIL
                         # so the inconsistent state is genuinely observable

# ---- gates ----------------------------------------------------------------
MAX_ACQUIRE_WAIT_MS = 50.0   # scaled by _SLOW below
FAIRNESS_RATIO = 3.0
MIN_FRAMES = 100
MIN_DISTINCT_FRAMES = 2

# ---- supervision ----------------------------------------------------------
# Scaled by the suite's own slow-run knob so the alternate-build suites
# (valgrind-test, asan-test, ...) do not trip the supervisor on their own latency.
_SLOW = float(os.environ.get("MCRF_TIMEOUT_MULTIPLIER", "1") or "1")
STALL_SECONDS = 1.5 * _SLOW   # no output at all from the child for this long => wedged
HARD_DEADLINE = 3.0 * _SLOW   # absolute cap on any one child
NEST_DEADLINE = 2.5 * _SLOW
# A latency gate on a machine the suite has already declared N times slower has to
# scale with it, or valgrind-test would fail this on its own overhead.
MAX_ACQUIRE_WAIT_MS = MAX_ACQUIRE_WAIT_MS * _SLOW

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)
    return condition


# ---------------------------------------------------------------------------
# Child programs. Built by prepending literal constants, so the bodies below are
# plain source with no format-escaping to get wrong.
# ---------------------------------------------------------------------------

def child_source(body, **consts):
    header = "".join("%s = %r\n" % (k, v) for k, v in sorted(consts.items()))
    return header + body


STRESS_BODY = r'''
import json, sys, threading, time
import mcrfpy

scene = mcrfpy.Scene("frame_lock_stress")
mcrfpy.current_scene = scene

# One Frame PAIR per worker. Frame.x is used rather than Entity.cell_pos because
# assigning cell_pos leaks one allocator block per assignment on this build, and a
# leak in the fixture would be indistinguishable from a leak in the barrier if this
# workload is ever reused under an allocation gate (the soak test relies on that).
A, B = [], []
for r in range(WORKERS):
    fa = mcrfpy.Frame(pos=(0, r * 4), size=(4, 4))
    fb = mcrfpy.Frame(pos=(0, r * 4), size=(4, 4))
    scene.children.append(fa)
    scene.children.append(fb)
    A.append(fa)
    B.append(fb)

waits = [[] for _ in range(WORKERS)]
counts = [0] * WORKERS
frames_seen = [set() for _ in range(WORKERS)]
self_torn = [0] * WORKERS
others_torn = [0] * WORKERS
errors = []
start = threading.Barrier(WORKERS + 1)
all_done = threading.Event()
finished = [0]
finished_lock = threading.Lock()
steps_box = [0]


def worker(r):
    fa, fb = A[r], B[r]
    try:
        start.wait()
        for i in range(ITERATIONS):
            value = float(i % 50 + 1)
            t0 = time.perf_counter()
            if LOCKED:
                with mcrfpy.lock():
                    t1 = time.perf_counter()
                    # Section 1, worker side: my own pair must be consistent on entry.
                    if fa.x != fb.x:
                        self_torn[r] += 1
                    # Diagnostic only, never gated: how often another holder is
                    # mid-mutation in the same open window. The barrier is not a
                    # mutex, so a non-zero value here is CORRECT, not a defect.
                    for q in range(WORKERS):
                        if q != r and A[q].x != B[q].x:
                            others_torn[r] += 1
                            break
                    frames_seen[r].add(mcrfpy.get_metrics()["current_frame"])
                    fa.x = value
                    time.sleep(TORN_SECONDS)
                    fb.x = value
            else:
                t1 = time.perf_counter()
                fa.x = value
                time.sleep(TORN_SECONDS)
                fb.x = value
            waits[r].append(t1 - t0)
            counts[r] += 1
            time.sleep(GAP_SECONDS)
    except BaseException as exc:
        errors.append("worker %d: %r" % (r, exc))
    finally:
        with finished_lock:
            finished[0] += 1
            if finished[0] == WORKERS:
                all_done.set()


def heartbeat():
    # Runs on its own thread on purpose: the main thread parks in closeWindow() with
    # the GIL RELEASED, so this keeps printing through a legitimate park and goes
    # silent only if the GIL itself is wedged. The parent uses that distinction.
    while not all_done.is_set():
        print("HB %d %d" % (steps_box[0], sum(counts)), flush=True)
        time.sleep(0.05)


threads = [threading.Thread(target=worker, args=(r,), name="w%d" % r, daemon=True)
           for r in range(WORKERS)]
for t in threads:
    t.start()
start.wait()
threading.Thread(target=heartbeat, name="hb", daemon=True).start()

frame0 = mcrfpy.get_metrics()["current_frame"]
t_start = time.perf_counter()
scans = 0
torn_main = 0
while not all_done.is_set() and time.perf_counter() - t_start < CHILD_BUDGET:
    mcrfpy.step(0.016)
    steps_box[0] += 1
    scans += 1
    # Section 1, main-thread side: between step() calls the safe window is shut and
    # closeWindow() has already drained every holder, so no pair may be torn here.
    for r in range(WORKERS):
        if A[r].x != B[r].x:
            torn_main += 1
            break
wall = time.perf_counter() - t_start
frame1 = mcrfpy.get_metrics()["current_frame"]

# Drain: workers may still be parked in acquire(), and they only get out if frames
# keep coming. Keep stepping while joining, with a deadline of our own.
drain_end = time.perf_counter() + 1.0
while time.perf_counter() < drain_end and any(t.is_alive() for t in threads):
    mcrfpy.step(0.016)
    steps_box[0] += 1
for t in threads:
    t.join(timeout=0.2)

print("RESULT " + json.dumps({
    "locked": bool(LOCKED),
    "wall": wall,
    "steps": steps_box[0],
    "frames": frame1 - frame0,
    "scans": scans,
    "torn_main": torn_main,
    "self_torn": self_torn,
    "others_torn": others_torn,
    "counts": counts,
    "total": sum(counts),
    "expected": WORKERS * ITERATIONS,
    "distinct_frames": [len(s) for s in frames_seen],
    "waits_ms": [[w * 1000.0 for w in waits[r]] for r in range(WORKERS)],
    "errors": errors,
    "alive": [t.name for t in threads if t.is_alive()],
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
         "outer_frame": None, "inner_frame": None}
errors = []
done = threading.Event()
running = threading.Event()
running.set()


def nester():
    try:
        for i in range(NEST_ROUNDS):
            with mcrfpy.lock():
                state["outer"] = True
                state["outer_frame"] = mcrfpy.get_metrics()["current_frame"]
                with mcrfpy.lock():
                    # The inner acquire must succeed while the window is already
                    # open; if it blocked, the outer holder would never release and
                    # closeWindow() would never return -- a self-deadlock.
                    state["inner"] = True
                    state["inner_frame"] = mcrfpy.get_metrics()["current_frame"]
                    target.x = float(i + 1)
                state["value"] = target.x
            time.sleep(0.001)
    except BaseException as exc:
        errors.append(repr(exc))
    finally:
        done.set()


def heartbeat():
    while running.is_set():
        print("HB nest", flush=True)
        time.sleep(0.05)


threading.Thread(target=heartbeat, daemon=True).start()
t = threading.Thread(target=nester, name="nester", daemon=True)
t.start()

t_start = time.perf_counter()
steps = 0
while not done.is_set() and time.perf_counter() - t_start < CHILD_BUDGET:
    mcrfpy.step(0.016)
    steps += 1
t.join(timeout=0.5)

# The outer release must leave the barrier in a state where frames still advance.
frame_before = mcrfpy.get_metrics()["current_frame"]
for _ in range(200):
    mcrfpy.step(0.016)
frame_after = mcrfpy.get_metrics()["current_frame"]
running.clear()

print("RESULT " + json.dumps({
    "outer": state["outer"],
    "inner": state["inner"],
    "value": state["value"],
    "same_frame": state["outer_frame"] == state["inner_frame"],
    "steps": steps,
    "frames_after_release": frame_after - frame_before,
    "errors": errors,
    "alive": t.is_alive(),
}), flush=True)
sys.exit(0)
'''


# ---------------------------------------------------------------------------
# Supervisor: stall detector + hard deadline. Never waits without a bound.
# ---------------------------------------------------------------------------

def run_child(label, source, hard_deadline, stall_seconds=STALL_SECONDS):
    """Returns (verdict, result_dict_or_None, info). verdict in
    {"ok", "stalled", "timeout", "exit", "spawn"}."""
    if not os.path.exists(sys.executable):
        return "spawn", None, {"detail": "sys.executable %r does not exist" % sys.executable}
    try:
        proc = subprocess.Popen(
            [sys.executable, "--headless", "-c", source],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except OSError as exc:
        return "spawn", None, {"detail": repr(exc)}

    lines = []
    last_output = [time.monotonic()]

    def pump():
        for line in proc.stdout:
            lines.append(line.rstrip("\n"))
            last_output[0] = time.monotonic()

    pump_thread = threading.Thread(target=pump, name="pump-" + label, daemon=True)
    pump_thread.start()

    # stderr is drained as it comes, too: a child whose stderr outgrows the pipe
    # buffer (a sanitizer's exit report under make asan-test) blocks writing it and
    # looks exactly like a wedge (#468).
    err_chunks = []

    def pump_err():
        for chunk in proc.stderr:
            err_chunks.append(chunk)

    err_thread = threading.Thread(target=pump_err, name="pump-err-" + label, daemon=True)
    err_thread.start()

    t0 = time.monotonic()
    verdict = "ok"
    while True:
        if proc.poll() is not None:
            break
        now = time.monotonic()
        if now - last_output[0] > stall_seconds:
            verdict = "stalled"
            break
        if now - t0 > hard_deadline:
            verdict = "timeout"
            break
        time.sleep(0.01)

    if verdict != "ok":
        proc.kill()
    try:
        proc.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        pass
    pump_thread.join(timeout=1.0)
    err_thread.join(timeout=1.0)
    elapsed = time.monotonic() - t0
    stderr = "".join(err_chunks)
    # De-fang: run_tests.py scores any output containing this marker as a failure,
    # and a child traceback quoted verbatim would hijack the parent's verdict.
    stderr = stderr.replace("Traceback (most recent call last)", "Traceback[child]")

    heartbeats = [ln for ln in lines if ln.startswith("HB ")]
    result_lines = [ln for ln in lines if ln.startswith("RESULT ")]
    # Did the child's MAIN loop advance while the watchdog thread was alive? The
    # heartbeat carries the main loop's step count, so "heartbeats kept coming but
    # the step count froze" (main thread parked forever inside step()) is a
    # different finding from "heartbeats stopped" (the GIL itself is wedged).
    step_counts = []
    for ln in heartbeats:
        parts = ln.split()
        if len(parts) >= 2 and parts[1].isdigit():
            step_counts.append(int(parts[1]))
    info = {
        "elapsed": elapsed,
        "returncode": proc.returncode,
        "heartbeats": len(heartbeats),
        "last_heartbeat": heartbeats[-1] if heartbeats else None,
        "steps_advanced": bool(step_counts) and step_counts[-1] > step_counts[0],
        "last_steps": step_counts[-1] if step_counts else None,
        "stderr_tail": stderr.strip().splitlines()[-3:],
    }
    if verdict == "ok" and not result_lines:
        verdict = "exit"
    result = json.loads(result_lines[0][len("RESULT "):]) if result_lines else None
    return verdict, result, info


def wedge_message(label, verdict, info):
    """One failure string that names the mechanism, for any non-ok child."""
    if verdict == "stalled" and not info["steps_advanced"]:
        why = ("the watchdog thread went silent with the main loop still at step %s, "
               "so the GIL itself is wedged: this is the ABBA inversion between the "
               "GIL and FrameLock::mtx described in this file's docstring "
               "(FrameLock::acquire takes mtx while holding the GIL, then holds mtx "
               "across Py_END_ALLOW_THREADS, so a woken holder and an entering "
               "thread deadlock on GIL-vs-mtx and take the engine with them). "
               "Last heartbeat %r, %d heartbeats total"
               % (info["last_steps"], info["last_heartbeat"], info["heartbeats"]))
    elif verdict == "stalled":
        why = ("the child stopped producing output after %r; the main loop HAD been "
               "advancing, so this is a wedge that reached the GIL later rather than "
               "immediately" % (info["last_heartbeat"],))
    elif verdict == "timeout":
        why = ("the child was still running at the %.1fs hard deadline; last heartbeat "
               "%r" % (HARD_DEADLINE, info["last_heartbeat"]))
    elif verdict == "exit":
        why = ("the child exited (rc=%s) without printing a RESULT line; last heartbeat "
               "%r, stderr tail %r"
               % (info["returncode"], info["last_heartbeat"], info["stderr_tail"]))
    else:
        why = "the child could not be started: %r" % (info.get("detail"),)
    return "%s child did not complete (%s after %.2fs): %s" % (
        label, verdict, info["elapsed"], why)


def percentile(sorted_values, fraction):
    if not sorted_values:
        return None
    return sorted_values[min(len(sorted_values) - 1, int(len(sorted_values) * fraction))]


def median(values):
    if not values:
        return None
    ordered = sorted(values)
    n = len(ordered)
    return ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2.0


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

common = dict(WORKERS=WORKERS, ITERATIONS=ITERATIONS,
              GAP_SECONDS=GAP_SECONDS, TORN_SECONDS=TORN_SECONDS,
              CHILD_BUDGET=HARD_DEADLINE - 0.5)

locked_verdict, locked, locked_info = run_child(
    "locked-stress", child_source(STRESS_BODY, LOCKED=True, **common), HARD_DEADLINE)
control_verdict, control, control_info = run_child(
    "unlocked-control", child_source(STRESS_BODY, LOCKED=False, **common), HARD_DEADLINE)
nest_verdict, nest, nest_info = run_child(
    "nesting", child_source(NEST_BODY, NEST_ROUNDS=8, CHILD_BUDGET=NEST_DEADLINE - 0.5),
    NEST_DEADLINE)

# ---- report ---------------------------------------------------------------
print()
print("child             | verdict  | elapsed | heartbeats | last heartbeat")
print("------------------+----------+---------+------------+---------------")
for label, verdict, info in (("locked-stress", locked_verdict, locked_info),
                             ("unlocked-control", control_verdict, control_info),
                             ("nesting", nest_verdict, nest_info)):
    print("%-17s | %-8s | %6.2fs | %10d | %s"
          % (label, verdict, info["elapsed"], info["heartbeats"], info["last_heartbeat"]))
print()

if locked:
    all_waits = sorted(w for row in locked["waits_ms"] for w in row)
    per_worker_max = [max(row) if row else None for row in locked["waits_ms"]]
    print("locked stress (%d workers x %d iterations)" % (WORKERS, ITERATIONS))
    print("  wall / steps / frames        : %.3fs / %d / %d"
          % (locked["wall"], locked["steps"], locked["frames"]))
    print("  mutations                    : %d of %d expected"
          % (locked["total"], locked["expected"]))
    print("  per-worker counts            : %s" % (locked["counts"],))
    print("  main-thread scans / torn     : %d / %d" % (locked["scans"], locked["torn_main"]))
    print("  worker self-torn (gated 0)   : %s" % (locked["self_torn"],))
    print("  other-pair torn (diagnostic) : %s" % (locked["others_torn"],))
    print("  distinct frames per worker   : %s" % (locked["distinct_frames"],))
    if all_waits:
        print("  acquire wait ms              : med %.4f  p90 %.4f  p99 %.4f  max %.4f"
              % (median(all_waits), percentile(all_waits, 0.90),
                 percentile(all_waits, 0.99), all_waits[-1]))
        print("  per-worker max wait ms       : %s"
              % ([round(x, 4) if x is not None else None for x in per_worker_max],))
        print("  per-worker total wait ms     : %s"
              % ([round(sum(row), 3) for row in locked["waits_ms"]],))
    print("  worker errors                : %s" % (locked["errors"],))
if control:
    print("unlocked control                : %d torn scans out of %d"
          % (control["torn_main"], control["scans"]))
if nest:
    print("nesting                         : outer=%s inner=%s value=%s "
          "same_frame=%s frames_after_release=%d errors=%s"
          % (nest["outer"], nest["inner"], nest["value"], nest["same_frame"],
             nest["frames_after_release"], nest["errors"]))
print()

# ---- gates ----------------------------------------------------------------

# Section 1 / 2 / 3 / 4 all live in the locked child.
if locked_verdict != "ok" or locked is None:
    check(False, wedge_message("locked-stress", locked_verdict, locked_info))
else:
    check(not locked["errors"],
          "locked workers raised: %s" % (locked["errors"],))
    check(not locked["alive"],
          "locked workers still running after drain+join: %s" % (locked["alive"],))

    # 1 -- torn state
    check(locked["torn_main"] == 0,
          "the main thread observed %d torn pairs out of %d scans between step() "
          "calls; outside a frame the safe window is shut and closeWindow() has "
          "drained every holder, so this must be exactly 0"
          % (locked["torn_main"], locked["scans"]))
    check(sum(locked["self_torn"]) == 0,
          "workers found their own pair inconsistent on entering the lock %s times; "
          "a worker is the only writer of its own pair, so this must be 0"
          % (locked["self_torn"],))

    # 2 -- no starvation
    check(locked["counts"] == [ITERATIONS] * WORKERS,
          "not every worker completed all %d iterations: %s -- a thread left behind "
          "is the #398 starvation shape" % (ITERATIONS, locked["counts"]))
    per_worker_max = [max(row) if row else None for row in locked["waits_ms"]]
    for r, worst in enumerate(per_worker_max):
        if worst is None:
            check(False, "worker %d recorded no acquire waits at all" % r)
        else:
            check(worst <= MAX_ACQUIRE_WAIT_MS,
                  "worker %d waited %.3f ms for a single acquire, over the %.0f ms "
                  "starvation gate (measured max across 20 runs: 0.937 ms)"
                  % (r, worst, MAX_ACQUIRE_WAIT_MS))
    # Fairness is gated on each worker's TOTAL time spent waiting at the barrier, not
    # on its median wait. Measured over 20 runs at WORKERS=8:
    #     max/min of per-worker SUM     1.165 - 1.660   (sd 12% of its own mean)
    #     max/min of per-worker MAX     1.272 - 1.912
    #     max/min of per-worker MEDIAN  1.476 - 13.983   <-- ungateable
    # The wait distribution is bimodal (near zero if the safe window is already open,
    # a frame-service latency if not), so a median over 40 samples flips between the
    # two modes; the sum integrates all 40 and is the statistic that actually answers
    # "is any thread being starved relative to its peers".
    sums = [sum(row) for row in locked["waits_ms"] if row]
    if len(sums) == WORKERS and min(sums) > 0:
        ratio = max(sums) / min(sums)
        check(ratio <= FAIRNESS_RATIO,
              "the worker that waited most spent %.2fx as long at the barrier as the "
              "worker that waited least (gate %.1fx, measured 1.165-1.660 over 20 "
              "runs): per-worker total wait ms %s"
              % (ratio, FAIRNESS_RATIO, [round(s, 3) for s in sums]))

    # 3 -- main thread kept making progress
    check(locked["frames"] >= MIN_FRAMES,
          "current_frame advanced by only %d during the stress (gate %d); a run in "
          "which the main loop was wedged and only the workers ran must not pass"
          % (locked["frames"], MIN_FRAMES))

    # 4 -- non-vacuity
    check(locked["total"] == locked["expected"],
          "total mutations %d != %d expected (%d workers x %d iterations); threads "
          "that died silently must not be able to pass this test"
          % (locked["total"], locked["expected"], WORKERS, ITERATIONS))
    for r, distinct in enumerate(locked["distinct_frames"]):
        check(distinct >= MIN_DISTINCT_FRAMES,
              "worker %d saw only %d distinct current_frame values from inside the "
              "lock (gate %d); it never crossed a real frame boundary, so its "
              "torn-state result proves nothing"
              % (r, distinct, MIN_DISTINCT_FRAMES))

# 1b -- the mutation check that makes section 1 non-vacuous.
if control_verdict != "ok" or control is None:
    check(False, wedge_message("unlocked-control", control_verdict, control_info))
else:
    check(control["torn_main"] > 0,
          "the unlocked control observed %d torn pairs; it is the SAME workload with "
          "only `with mcrfpy.lock():` removed, so a 0 here would mean the main-thread "
          "scan cannot see tearing at all and section 1's gate is vacuous"
          % control["torn_main"])
    check(control["total"] == control["expected"],
          "unlocked control performed %d of %d mutations"
          % (control["total"], control["expected"]))

# 5 -- nesting
if nest_verdict != "ok" or nest is None:
    check(False, wedge_message("nesting", nest_verdict, nest_info))
else:
    check(not nest["errors"], "nesting thread raised: %s" % (nest["errors"],))
    check(nest["outer"], "the outer `with mcrfpy.lock():` never entered")
    check(nest["inner"],
          "the inner `with mcrfpy.lock():` never entered -- a nested acquire must "
          "succeed while the safe window is already open, or the outer holder can "
          "never release and closeWindow() never returns")
    check(nest["same_frame"],
          "the nested acquire reported a different current_frame than the outer one "
          "(%s); both are inside one open window, so they are one barrier instant"
          % (nest["same_frame"],))
    check(nest["value"] == 8.0,
          "the mutation made inside the nested block did not land (value=%s, "
          "expected 8.0)" % (nest["value"],))
    check(nest["frames_after_release"] >= 100,
          "only %d frames advanced after the outer release; the outer release must "
          "leave the barrier able to complete frames"
          % nest["frames_after_release"])
    check(not nest["alive"], "the nesting thread is still running")

if failures:
    for message in failures:
        print("FAILURE: %s" % message)
    sys.exit(1)

print("PASS")
sys.exit(0)
