"""Sustained-load soak for mcrfpy.lock() -- the #219 FrameLock barrier (#395).

The property the simulator embedding needs is "an event handler sits on this barrier
for HOURS against a render loop that must stay smooth". Hours are not available in a
~100 second test suite, so this file runs a bounded soak and gates the things that
DEGRADE over time rather than fail outright: drift in acquire latency, drift in frame
time, and unbounded allocator growth. A slow ratchet shows up in those three long
before it shows up as a hang.

Everything is expressed as a RATIO between the first and last fifth of the run, not
as an absolute, so the gates mean the same thing on a slow machine as on a fast one.

WHY A CHILD PROCESS. This is a standing property of the subject, not a workaround
for any particular bug. FrameLock::acquire() waits on a condition variable with no
timeout, and a wedge there stops the main thread inside mcrfpy.step() and every
Python thread on the GIL -- so no in-process deadline can be checked and no message
can be printed, and a test that cannot report its own failure is not a test. The
workload therefore runs in a child of this same binary,
supervised from outside by a stall detector and a hard deadline. The child's
heartbeat comes from a WATCHDOG THREAD rather than the main loop, because the main
thread parking in closeWindow() is legitimate (it releases the GIL while parked): a
frozen step count with a live heartbeat and a silent heartbeat are different
findings, and the failure text distinguishes them.

SECTIONS
  1  continuous lock traffic from WORKERS threads for the whole soak, against a main
     loop driving frames.
  2  no drift in acquire wait: every worker's acquires are pooled into five equal
     WALL-CLOCK fifths of the soak and each fifth is summarised by its MEAN;
     mean(last fifth) / mean(first fifth) <= WAIT_DRIFT_RATIO. This is what catches
     a starvation ratchet or a slow leak of waiters -- the barrier gets progressively
     less willing to admit a thread. See wait_windows() for why pooled-by-time-and-
     mean, and not the obvious per-worker median, is the statistic being gated.
  3  no drift in frame time: median(last fifth) / median(first fifth) of the wall
     time spent inside mcrfpy.step() <= FRAME_DRIFT_RATIO. step() includes the
     barrier park, so this is the "render loop stays smooth" measurement.
  4  no unbounded resource growth: sys.getallocatedblocks() across the soak, after a
     warmup and a gc.collect(). Blocks, not RSS -- a real ~320 KB leak hides
     comfortably under a 4096 KB RSS threshold, whereas one leaked object per
     acquire is one block per acquire and cannot hide here at all.
  5  progress gates: acquires, frames and elapsed wall all asserted to be meaningful,
     so a soak that did almost nothing cannot pass sections 2-4 vacuously.
  6  clean shutdown: after the soak the main loop keeps stepping while it joins, so
     a worker parked in acquire() can drain. A thread still alive at the deadline is
     a FAILURE that names it, not a hang.

FIXTURE NOTE. The workers mutate Frame.x. They deliberately do NOT touch
Entity.cell_pos and do NOT call mcrfpy.get_metrics() inside the measured region:
measured on this build, `entity.cell_pos = (x, y)` leaks exactly 1 allocator block
per assignment and `mcrfpy.get_metrics()` leaks ~10 blocks per call (confirmed
linear over 20000 iterations, with and without frames interleaved, after
gc.collect()). Either one inside the loop would swamp section 4 -- a fixture leak
is indistinguishable from a barrier leak once it is in the sample. Frame.x
assignment measured 0.0001 blocks/iteration, i.e. clean.

WHAT THIS COVERAGE FOUND (#412, fixed). At the shipped WORKERS=3 this soak wedged
the engine on its first run. FrameLock::acquire() used to take its mutex while
holding the GIL and to hold that mutex across Py_END_ALLOW_THREADS (cv.wait re-locks
before returning), so a thread woken from cv.wait() held `mtx` and blocked on the
GIL while any second thread entering acquire() held the GIL and blocked on `mtx` --
an ABBA inversion that took the whole interpreter down with it. Two concurrent
background lock users were enough; one never tripped it, which is why it survived
#219 and #398. acquire() now releases the GIL before taking `mtx`. Fixed as #412;
the full diagnosis is in tests/integration/frame_lock_stress_test.py.

MEASUREMENTS behind the thresholds (this machine, build/mcrogueface post-#412,
2026-07-27), 30 runs at the shipped WORKERS=3, 3.0 s soak, 2 ms gap, with
allocation-free preallocated bookkeeping:

    acquires (total)             1225 - 1360        (per worker 380 - 460)
    frames                       4.4M - 5.1M
    allocator block growth       47 - 55            (FLAT in the acquire count)
    acquire wait ms              mean 0.073 - 0.101, max 0.415 - 1.430
    frame-time drift ratio       0.936 - 1.076   mean 1.006  sd 0.033  (window MEDIAN)
    acquire-wait drift ratio     0.640 - 1.542   mean 0.966  sd 0.213  (pooled MEAN)

  and, on the same runs, the statistics that were REJECTED for the wait gate:
    per-worker index windows, MEDIAN          0.167 - 6.048   (per worker-run)
    pooled-by-time windows,   MEDIAN          0.502 - 1.960
    pooled-by-time windows,   5% TRIMMED MEAN 0.612 - 1.287
  The trimmed mean tracking the plain mean to within 3% is the evidence that the
  chosen statistic is not outlier-driven. See wait_windows() for the reasoning.

  WAIT_DRIFT_RATIO = 3.0, i.e. 1.95x the worst of 30 runs and mean + 9.5 sd. BE
    HONEST ABOUT WHAT THIS DETECTS: the run-to-run noise on this statistic is 22%
    of its own mean with a fat tail (worst observation sits at mean + 2.7 sd), so
    the gate catches a ratchet -- an unbounded, compounding growth in admission
    latency, which is the #398/#412 failure shape -- and does NOT catch a clean 2x
    degradation, which would land at ~1.9 and pass. A 2x-sensitive gate would need
    more samples per window, i.e. a longer soak than a ~100 s suite can afford.
    Tightening the NUMBER would not fix that; only a longer run would. Note also
    that the rejected per-worker-median formulation reached 6.048, so it would have
    flaked against any threshold that detected anything at all -- the first fix here
    was the statistic, not the number.
  FRAME_DRIFT_RATIO = 1.5, i.e. 1.39x the worst of 30 runs and mean + 15 sd. This
    statistic is 6x quieter than the wait ratio (sd 3.3% of mean), so it can be
    gated much closer: it detects a >=50% growth in median frame time across three
    seconds of steady load. This is the gate with real teeth of the two.
  MAX_BLOCK_GROWTH = 150. Measured 47-55 blocks, and FLAT in the acquire count
    (i.e. a fixed cost of the watchdog thread, not a per-acquire leak). One leaked
    object per acquire would be +1 block per acquire: at the gated minimum of 400
    acquires that is +400 (2.7x over the gate) and at the measured ~1300 it is
    +1300 (8.7x over). So the gate is provably finer than the effect it must
    detect, while sitting 2.7x above the observed noise.
  MIN_TOTAL_ACQUIRES = 400 (measured 1225-1360, 3.1x margin),
  MIN_ACQUIRES_PER_WORKER = 100 (measured 380-460, 3.8x margin).
  MIN_FRAMES = 1000. Measured ~4.5 million; three orders of margin, and still
    impossible for a wedged main loop.

THE ALLOCATOR GATE WAS VERIFIED TO FAIL on the fixed engine, by mutating a scratch
copy (never the shipped file) to append one object() to a list per acquire -- the
exact effect size the threshold claims to detect. Literal output is in the report
accompanying this change.

Run: ./mcrogueface --headless --exec ../tests/integration/frame_lock_soak_test.py
"""

import json
import os
import subprocess
import sys
import threading
import time

# ---- workload shape -------------------------------------------------------
WORKERS = 3
SOAK_SECONDS = 3.0
GAP_SECONDS = 0.002       # between acquires; sets the ~460-acquires-per-worker rate
WARMUP_SECONDS = 0.3      # before the allocator baseline is taken
FRAME_SAMPLE_SECONDS = 0.0005  # time-based sampling of frame wall time, so the
                               # samples span the WHOLE soak instead of just the
                               # first few milliseconds of a multi-million-step loop
WINDOWS = 5

# ---- gates ----------------------------------------------------------------
WAIT_DRIFT_RATIO = 3.0
FRAME_DRIFT_RATIO = 1.5
MAX_BLOCK_GROWTH = 150
MIN_TOTAL_ACQUIRES = 400
MIN_ACQUIRES_PER_WORKER = 100
MIN_FRAMES = 1000
MIN_WALL_FRACTION = 0.8   # of SOAK_SECONDS

# ---- supervision ----------------------------------------------------------
# Scaled by the suite's own slow-run knob so the alternate-build suites
# (valgrind-test, asan-test, ...) do not trip the supervisor on their own latency.
# SOAK_SECONDS itself is NOT scaled: it is the workload, not a deadline.
_SLOW = float(os.environ.get("MCRF_TIMEOUT_MULTIPLIER", "1") or "1")
STALL_SECONDS = 1.5 * _SLOW
HARD_DEADLINE = SOAK_SECONDS + 3.0 * _SLOW

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)
    return condition


def child_source(body, **consts):
    header = "".join("%s = %r\n" % (k, v) for k, v in sorted(consts.items()))
    return header + body


SOAK_BODY = r'''
import gc, json, sys, threading, time
from array import array
import mcrfpy

CAP = 40000

scene = mcrfpy.Scene("frame_lock_soak")
mcrfpy.current_scene = scene
targets = []
for r in range(WORKERS):
    f = mcrfpy.Frame(pos=(0, r * 4), size=(4, 4))
    scene.children.append(f)
    targets.append(f)

# Preallocated, so the harness itself allocates nothing inside the measured region
# and section 4 measures the engine rather than the bookkeeping.
waits = [array('d', bytes(8 * CAP)) for _ in range(WORKERS)]
stamps = [array('d', bytes(8 * CAP)) for _ in range(WORKERS)]
wn = [0] * WORKERS
frame_times = array('d', bytes(8 * CAP))
fn = [0]

stop = threading.Event()
started = threading.Barrier(WORKERS + 1)
errors = []
steps_box = [0]


def worker(r):
    target = targets[r]
    try:
        started.wait()
        i = 0
        while not stop.is_set():
            t0 = time.perf_counter()
            with mcrfpy.lock():
                t1 = time.perf_counter()
                target.x = float(i % 50 + 1)
            if wn[r] < CAP:
                waits[r][wn[r]] = t1 - t0
                stamps[r][wn[r]] = t1   # wall-clock instant, so the parent can bucket
                wn[r] += 1              # every worker's acquires into common windows
            i += 1
            time.sleep(GAP_SECONDS)
    except BaseException as exc:
        errors.append("worker %d: %r" % (r, exc))


def heartbeat():
    while not stop.is_set():
        print("HB %d %d" % (steps_box[0], sum(wn)), flush=True)
        time.sleep(0.05)


threads = [threading.Thread(target=worker, args=(r,), name="soak-%d" % r, daemon=True)
           for r in range(WORKERS)]
for t in threads:
    t.start()
started.wait()
threading.Thread(target=heartbeat, name="hb", daemon=True).start()

warmup_end = time.perf_counter() + WARMUP_SECONDS
while time.perf_counter() < warmup_end:
    mcrfpy.step(0.016)
    steps_box[0] += 1

gc.collect()
blocks_before = sys.getallocatedblocks()
frame_before = mcrfpy.get_metrics()["current_frame"]

t_start = time.perf_counter()
soak_end = t_start + SOAK_SECONDS
next_sample = t_start
while True:
    now = time.perf_counter()
    if now >= soak_end:
        break
    s = time.perf_counter()
    mcrfpy.step(0.016)
    e = time.perf_counter()
    steps_box[0] += 1
    if e >= next_sample and fn[0] < CAP:
        frame_times[fn[0]] = e - s
        fn[0] += 1
        next_sample = e + FRAME_SAMPLE_SECONDS
wall = time.perf_counter() - t_start
frame_after = mcrfpy.get_metrics()["current_frame"]

gc.collect()
blocks_after = sys.getallocatedblocks()

# Section 6 -- clean shutdown. A worker parked in acquire() only gets out if frames
# keep coming, so the drain loop keeps stepping while it joins, under its own
# deadline. Anything still alive afterwards is named, not waited on.
stop.set()
drain_end = time.perf_counter() + 1.0
while time.perf_counter() < drain_end and any(t.is_alive() for t in threads):
    mcrfpy.step(0.016)
    steps_box[0] += 1
for t in threads:
    t.join(timeout=0.2)
alive = [t.name for t in threads if t.is_alive()]

print("RESULT " + json.dumps({
    "wall": wall,
    "steps": steps_box[0],
    "frames": frame_after - frame_before,
    "acquires": list(wn),
    "total_acquires": sum(wn),
    "blocks_before": blocks_before,
    "blocks_after": blocks_after,
    "block_growth": blocks_after - blocks_before,
    "waits_ms": [[waits[r][i] * 1000.0 for i in range(wn[r])] for r in range(WORKERS)],
    "stamps": [[stamps[r][i] for i in range(wn[r])] for r in range(WORKERS)],
    "soak_t0": t_start,
    "soak_t1": t_start + wall,
    "frame_ms": [frame_times[i] * 1000.0 for i in range(fn[0])],
    "errors": errors,
    "alive": alive,
}), flush=True)
sys.exit(0)
'''


def run_child(label, source, hard_deadline, stall_seconds=STALL_SECONDS):
    """Returns (verdict, result_or_None, info). Never waits without a bound."""
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
    elapsed = time.monotonic() - t0
    try:
        stderr = proc.stderr.read() or ""
    except (ValueError, OSError):
        stderr = ""
    # run_tests.py scores any output containing this marker as a failure; a child
    # traceback quoted verbatim would hijack the parent's verdict.
    stderr = stderr.replace("Traceback (most recent call last)", "Traceback[child]")

    heartbeats = [ln for ln in lines if ln.startswith("HB ")]
    result_lines = [ln for ln in lines if ln.startswith("RESULT ")]
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
    if verdict == "stalled" and not info["steps_advanced"]:
        why = ("the watchdog thread went silent with the main loop still at step %s, "
               "so the GIL itself is wedged: FrameLock::acquire() takes its mutex "
               "while holding the GIL and holds it across Py_END_ALLOW_THREADS, so a "
               "woken holder and an entering thread deadlock GIL-against-mtx and take "
               "the engine with them (the shape of the #412 inversion). Last "
               "heartbeat %r, %d heartbeats total"
               % (info["last_steps"], info["last_heartbeat"], info["heartbeats"]))
    elif verdict == "stalled":
        why = ("the child stopped producing output after %r; the main loop HAD been "
               "advancing, so the wedge arrived partway through the soak rather than "
               "at the start" % (info["last_heartbeat"],))
    elif verdict == "timeout":
        why = ("the child was still running at the %.1fs hard deadline; last "
               "heartbeat %r" % (HARD_DEADLINE, info["last_heartbeat"]))
    elif verdict == "exit":
        why = ("the child exited (rc=%s) without printing a RESULT line; last "
               "heartbeat %r, stderr tail %r"
               % (info["returncode"], info["last_heartbeat"], info["stderr_tail"]))
    else:
        why = "the child could not be started: %r" % (info.get("detail"),)
    return "%s child did not complete (%s after %.2fs): %s" % (
        label, verdict, info["elapsed"], why)


def median(values):
    if not values:
        return None
    ordered = sorted(values)
    n = len(ordered)
    return ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2.0


def mean(values):
    return sum(values) / float(len(values)) if values else None


def wait_windows(result):
    """Pool EVERY worker's acquire waits into WINDOWS equal WALL-CLOCK slices of the
    soak, and summarise each slice by its MEAN.

    Both halves of that were chosen by measurement, not taste (30 runs, WORKERS=3):

      per-worker windows by sample index, summarised by MEDIAN   ratio 0.167 - 6.048
      pooled by wall clock,               summarised by MEDIAN   ratio 0.502 - 1.960
      pooled by wall clock,               summarised by MEAN     ratio 0.640 - 1.278
      pooled by wall clock,               summarised by 5% TRIMMED MEAN  0.612 - 1.287

    Acquire wait is bimodal -- near zero if the safe window is already open, up to a
    frame-service latency if it is not -- so a median over ~85 per-worker samples flips
    between the two modes and is not a gateable statistic at any threshold that would
    still detect anything. Pooling by wall clock triples the samples per window
    (~222) and puts every worker on one time base; the mean then integrates both
    modes. The trimmed mean tracks the plain mean to within 3%, which is the evidence
    that the mean is not being driven by outliers, so the plain mean is used."""
    t0 = result.get("soak_t0")
    t1 = result.get("soak_t1")
    if t0 is None or t1 is None or t1 <= t0:
        return [], None
    span = (t1 - t0) / float(WINDOWS)
    buckets = [[] for _ in range(WINDOWS)]
    for worker_waits, worker_stamps in zip(result["waits_ms"], result["stamps"]):
        for value, stamp in zip(worker_waits, worker_stamps):
            index = int((stamp - t0) // span)
            buckets[min(WINDOWS - 1, max(0, index))].append(value)
    if any(not b for b in buckets):
        return [len(b) for b in buckets], None
    means = [mean(b) for b in buckets]
    if not means[0]:
        return means, None
    return means, means[-1] / means[0]


def frame_windows(values):
    """Frame samples are already taken on a fixed wall-clock cadence, so equal-count
    slices ARE equal-time slices. Summarised by MEDIAN: measured 0.936 - 1.076 over
    30 runs, against 0.625 - 1.660 for the mean, which a single slow frame drags."""
    size = len(values) // WINDOWS
    if size == 0:
        return [], None
    medians = [median(values[i * size:(i + 1) * size]) for i in range(WINDOWS)]
    if not medians[0]:
        return medians, None
    return medians, medians[-1] / medians[0]


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

verdict, soak, info = run_child(
    "soak",
    child_source(SOAK_BODY, WORKERS=WORKERS, SOAK_SECONDS=SOAK_SECONDS,
                 GAP_SECONDS=GAP_SECONDS, WARMUP_SECONDS=WARMUP_SECONDS,
                 FRAME_SAMPLE_SECONDS=FRAME_SAMPLE_SECONDS),
    HARD_DEADLINE)

print()
print("soak child: verdict=%s elapsed=%.2fs heartbeats=%d last=%s"
      % (verdict, info["elapsed"], info["heartbeats"], info["last_heartbeat"]))

if verdict != "ok" or soak is None:
    check(False, wedge_message("soak", verdict, info))
else:
    wait_means, wait_ratio = wait_windows(soak)
    frame_medians, frame_ratio = frame_windows(soak["frame_ms"])

    print()
    print("soak (%d workers, %.1fs, %.0f ms gap)" % (WORKERS, SOAK_SECONDS, GAP_SECONDS * 1000))
    print("  wall / steps / frames    : %.3fs / %d / %d"
          % (soak["wall"], soak["steps"], soak["frames"]))
    print("  acquires per worker      : %s  (total %d)"
          % (soak["acquires"], soak["total_acquires"]))
    print("  allocated blocks         : %d -> %d  (growth %d, %.4f per acquire)"
          % (soak["blocks_before"], soak["blocks_after"], soak["block_growth"],
             soak["block_growth"] / float(max(1, soak["total_acquires"]))))
    print("  wait ms by fifth (pooled): %s  last/first = %s"
          % ([round(m, 4) for m in wait_means] if wait_means else None,
             "%.3f" % wait_ratio if wait_ratio is not None else "n/a"))
    print("  frame ms by fifth        : %s  last/first = %s"
          % ([round(m, 5) for m in frame_medians] if frame_medians else None,
             "%.3f" % frame_ratio if frame_ratio is not None else "n/a"))
    print("  frame samples            : %d" % len(soak["frame_ms"]))
    print("  worker errors            : %s" % (soak["errors"],))
    print("  threads alive at exit    : %s" % (soak["alive"],))
    print()

    check(not soak["errors"], "soak workers raised: %s" % (soak["errors"],))

    # 5 -- progress first: sections 2-4 are vacuous without it.
    check(soak["total_acquires"] >= MIN_TOTAL_ACQUIRES,
          "the soak completed only %d acquires (gate %d); the drift and allocator "
          "gates below mean nothing without sustained traffic"
          % (soak["total_acquires"], MIN_TOTAL_ACQUIRES))
    for r, n in enumerate(soak["acquires"]):
        check(n >= MIN_ACQUIRES_PER_WORKER,
              "worker %d completed only %d acquires (gate %d = %d windows x 20 "
              "samples, the minimum for a per-window median to be meaningful)"
              % (r, n, MIN_ACQUIRES_PER_WORKER, WINDOWS))
    check(soak["frames"] >= MIN_FRAMES,
          "current_frame advanced by only %d during the soak (gate %d); the main "
          "loop must really have been driving frames the whole time"
          % (soak["frames"], MIN_FRAMES))
    check(soak["wall"] >= SOAK_SECONDS * MIN_WALL_FRACTION,
          "the soak ran for only %.3fs of the intended %.1fs"
          % (soak["wall"], SOAK_SECONDS))

    # 2 -- acquire-wait drift
    if wait_ratio is None:
        check(False,
              "no usable acquire-wait windows could be formed (%s) -- every "
              "wall-clock fifth of the soak must contain acquires from the workers"
              % (wait_means,))
    else:
        check(wait_ratio <= WAIT_DRIFT_RATIO,
              "the pooled mean acquire wait grew %.2fx from the first wall-clock "
              "fifth of the soak to the last (gate %.1fx): means ms %s -- this is "
              "the shape of a starvation ratchet or a slow leak of waiters"
              % (wait_ratio, WAIT_DRIFT_RATIO, [round(m, 4) for m in wait_means]))

    # 3 -- frame-time drift
    if frame_ratio is None:
        check(False, "no usable frame-time windows (samples %d, medians %s)"
                     % (len(soak["frame_ms"]), frame_medians))
    else:
        check(frame_ratio <= FRAME_DRIFT_RATIO,
              "median frame time grew %.2fx from the first fifth of the soak to the "
              "last (gate %.1fx): medians ms %s -- the render loop must stay smooth "
              "under sustained lock traffic"
              % (frame_ratio, FRAME_DRIFT_RATIO, [round(m, 5) for m in frame_medians]))

    # 4 -- allocator growth
    check(soak["block_growth"] <= MAX_BLOCK_GROWTH,
          "sys.getallocatedblocks() grew by %d across the soak (gate %d) over %d "
          "acquires, i.e. %.4f blocks per acquire; one leaked object per acquire "
          "would be 1.0"
          % (soak["block_growth"], MAX_BLOCK_GROWTH, soak["total_acquires"],
             soak["block_growth"] / float(max(1, soak["total_acquires"]))))

    # 6 -- clean shutdown
    check(not soak["alive"],
          "these worker threads were still running after the drain loop and join "
          "deadline, i.e. still parked in FrameLock::acquire(): %s" % (soak["alive"],))

if failures:
    for message in failures:
        print("FAILURE: %s" % message)
    sys.exit(1)

print("PASS")
sys.exit(0)
