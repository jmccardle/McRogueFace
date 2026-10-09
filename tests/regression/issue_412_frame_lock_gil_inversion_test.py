"""Regression #412: two background threads on mcrfpy.lock() deadlocked the interpreter.

THE DEFECT
==========
`FrameLock::acquire()` used to take its mutex while holding the GIL, and then hold that
mutex across `Py_END_ALLOW_THREADS` -- `cv.wait` re-locks the mutex before returning.
With two background threads that is a textbook ABBA inversion:

    thread A : woken from cv.wait, HOLDS mtx, blocks acquiring the GIL
    thread B : HOLDS the GIL, blocks acquiring mtx

Neither can proceed, and because B holds the GIL the whole interpreter stops with them:
the main thread, every timer, every other thread. Nothing times out -- FrameLock's
condition variable has no deadline, deliberately (#398). Confirmed by backtrace on the
wedged process, not by inspection.

ONE thread never hit it. It needed exactly two, and entirely ordinary usage. It survived
because nothing in the suite had ever put two threads on this barrier at once, which is
the whole of #395's point.

Fixed by releasing the GIL BEFORE taking the mutex and re-acquiring it only after the
mutex is dropped, so no thread ever holds the mutex while blocking on the GIL.

WHY THIS RUNS IN A CHILD PROCESS
================================
A wedged GIL cannot be detected from inside the process it has wedged. An in-process
deadline is Python code, and no Python code runs once the GIL is held by a thread that
will never release it -- the deadline would simply never be evaluated. So the load runs
in a separate process of this same binary and the PARENT enforces the timeout. That is
the only construction in which this regression reports a failure rather than hanging.

WHAT THIS GATES
===============
  1. N = 2 completes. Two is the minimum that reproduced the deadlock, so it is the
     assertion that maps onto the defect exactly.
  2. N = 8 completes. Contention well past the minimum.
  3. N = 1 completes -- the PRE-FIX CONTROL. One thread passed before the fix too, so
     this arm proves the difference between (1) and the old behaviour is the thread
     count and not the harness.
  4. Every worker completes ALL its iterations, and no thread is left alive. A child
     that exits having done nothing must not pass.
  5. The main thread ran frames. A child in which the main loop never ran would satisfy
     everything above vacuously.

Run: ./mcrogueface --headless --exec ../tests/regression/issue_412_frame_lock_gil_inversion_test.py
"""

import json
import os
import subprocess
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CHILD = os.path.join(THIS_DIR, "_frame_lock_contention_child.py")

ITERATIONS = 200
CHILD_TIMEOUT = 30.0   # generous: the child's own wall deadline is 20 s

failures = []


def check_true(label, cond):
    if not cond:
        failures.append(label)
        print(f"  FAILURE: {label}")
    else:
        print(f"  ok  {label}")


def run_child(nthreads):
    """Run the contention load in a fresh process. Returns a parsed RESULT dict or None."""
    env = os.environ.copy()
    env["MCRF_LOCK_THREADS"] = str(nthreads)
    env["MCRF_LOCK_ITERATIONS"] = str(ITERATIONS)
    # sys.executable is the mcrogueface binary itself when running under --exec.
    try:
        proc = subprocess.run(
            [sys.executable, "--headless", "--exec", CHILD],
            capture_output=True, text=True, timeout=CHILD_TIMEOUT, env=env,
        )
    except subprocess.TimeoutExpired:
        return {"timeout": True}
    if proc.returncode != 0:
        return {"rc": proc.returncode, "stderr": proc.stderr[-800:]}
    for line in proc.stdout.splitlines():
        if line.startswith("RESULT "):
            return json.loads(line[len("RESULT "):])
    return {"noresult": proc.stdout[-800:]}


for n in (1, 2, 8):
    label = {1: "N=1 (the pre-fix control: this passed before the fix too)",
             2: "N=2 (the MINIMUM that deadlocked pre-fix)",
             8: "N=8 (contention well past the minimum)"}[n]
    print(f"{label}")
    res = run_child(n)

    if res.get("timeout"):
        check_true(f"  child with {n} thread(s) completed within {CHILD_TIMEOUT}s -- "
                   f"it did NOT: the interpreter is wedged, which is #412 "
                   f"(FrameLock::acquire holding mtx across Py_END_ALLOW_THREADS)",
                   False)
        continue
    if "rc" in res:
        check_true(f"  child with {n} thread(s) exited 0 (got {res['rc']}): "
                   f"{res.get('stderr', '')!r}", False)
        continue
    if "noresult" in res:
        check_true(f"  child with {n} thread(s) printed a RESULT line "
                   f"(tail: {res['noresult']!r})", False)
        continue

    counts = res.get("counts") or []
    print(f"  counts={counts} frames={res.get('frames')} alive={res.get('alive')} "
          f"errors={res.get('errors')}")
    check_true(f"  N={n}: all {n} worker(s) completed all {ITERATIONS} iterations "
               f"(got {counts})",
               len(counts) == n and all(c == ITERATIONS for c in counts))
    check_true(f"  N={n}: no worker thread left alive (got {res.get('alive')})",
               res.get("alive") == 0)
    check_true(f"  N={n}: no worker raised (got {res.get('errors')})",
               res.get("errors") == [])
    # Non-vacuity: a child whose main loop never ran would satisfy nothing meaningful.
    check_true(f"  N={n}: the main thread actually drove frames "
               f"(got {res.get('frames')})",
               isinstance(res.get("frames"), int) and res["frames"] >= 1)

if failures:
    print(f"\n{len(failures)} FAILURE(S)")
    sys.exit(1)

print("\nPASS")
sys.exit(0)
