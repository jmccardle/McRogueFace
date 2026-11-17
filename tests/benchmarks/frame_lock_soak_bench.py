"""Time-valued behaviour of mcrfpy.lock() under sustained load -- a REPORT (#395, #535).

This was tests/integration/frame_lock_soak_test.py. Its gates (acquire-wait drift <= 3.0x,
frame-time drift <= 1.5x, >= 400 acquires and >= 0.8 x 3 s of wall clock, >= 1000 frames
inside a time budget) asserted machine speed, and failed on a loaded machine (5/10 runs).
The load-independent half moved to tests/integration/frame_lock_soak_test.py and is counted
in admissions per window, with a fixed workload and the allocator-growth gate kept.

What stays here is the part that IS a time measurement -- how long an acquire waits, how the
median frame time drifts over a sustained run. It prints the numbers and has no pass/fail
threshold; it fails only if the child hangs or a worker raises.

Run: ./mcrogueface --headless --exec ../tests/benchmarks/frame_lock_soak_bench.py
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


# ---- supervision ----------------------------------------------------------
# Scaled by the suite's own slow-run knob so the alternate-build suites
# (valgrind-test, asan-test, ...) do not trip the supervisor on their own latency.
# SOAK_SECONDS itself is NOT scaled: it is the workload, not a deadline.
_SLOW = float(os.environ.get("MCRF_TIMEOUT_MULTIPLIER", "1") or "1")
STALL_SECONDS = 30.0 * _SLOW                 # hang detector only
HARD_DEADLINE = SOAK_SECONDS + 60.0 * _SLOW  # hang detector only

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
    check(not soak["alive"], "worker threads still parked in acquire(): %s" % (soak["alive"],))
    print("REPORTED (no pass/fail threshold): every ratio above is machine-dependent")

if failures:
    for message in failures:
        print("FAILURE: %s" % message)
    sys.exit(1)

print("PASS")
sys.exit(0)
