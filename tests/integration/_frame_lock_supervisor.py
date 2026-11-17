"""Shared supervisor for the FrameLock child-process tests (#395, #535).

WHY A CHILD PROCESS. FrameLock::acquire() waits on a condition variable with no timeout, so
every failure of this barrier is a hang, and a GIL-level wedge (#412) silences every
in-process watchdog. The contended workload therefore runs in a child of this same binary,
supervised from outside.

WHAT "HANG" MEANS HERE. Not "slow". The child prints a heartbeat from a watchdog thread; the
payload is a PROGRESS TOKEN (steps, acquires, admissions ... whatever the child counts). The
child is declared hung only if

  - it printed nothing at all for STALL_SECONDS (the GIL itself is wedged), or
  - the progress token did not change for STALL_SECONDS (the main loop is parked for good).

A machine that is merely loaded keeps changing the token, however slowly, so load can never
produce a verdict. There is deliberately NO total-runtime deadline: how long the workload
takes is machine speed, and the workload is a fixed amount of work. STALL_SECONDS is
generous (tens of seconds) and scaled by MCRF_TIMEOUT_MULTIPLIER like the runner's own
timeout, which run_tests.py SLOW_TESTS keeps above it.
"""

import json
import os
import subprocess
import sys
import threading
import time

SLOW = float(os.environ.get("MCRF_TIMEOUT_MULTIPLIER", "1") or "1")
STALL_SECONDS = 20.0 * SLOW


def child_source(body, **consts):
    header = "".join("%s = %r\n" % (k, v) for k, v in sorted(consts.items()))
    return header + body


def run_child(label, source, stall_seconds=STALL_SECONDS):
    """Returns (verdict, result_or_None, info). verdict in {"ok", "stalled", "exit", "spawn"}."""
    if not os.path.exists(sys.executable):
        return "spawn", None, {"detail": "sys.executable %r does not exist" % sys.executable}
    try:
        proc = subprocess.Popen(
            [sys.executable, "--headless", "-c", source],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except OSError as exc:
        return "spawn", None, {"detail": repr(exc)}

    lines = []
    state = {"last_output": time.monotonic(), "token": None, "token_since": time.monotonic()}

    def pump():
        for line in proc.stdout:
            line = line.rstrip("\n")
            lines.append(line)
            now = time.monotonic()
            state["last_output"] = now
            if line.startswith("HB "):
                if line != state["token"]:
                    state["token"] = line
                    state["token_since"] = now

    pump_thread = threading.Thread(target=pump, name="pump-" + label, daemon=True)
    pump_thread.start()

    # stderr is drained as it comes: a child whose stderr outgrows the pipe buffer (a
    # sanitizer's exit report) blocks writing it and looks exactly like a wedge (#468).
    err_chunks = []

    def pump_err():
        for chunk in proc.stderr:
            err_chunks.append(chunk)

    err_thread = threading.Thread(target=pump_err, name="pump-err-" + label, daemon=True)
    err_thread.start()

    t0 = time.monotonic()
    verdict = "ok"
    why = None
    while True:
        if proc.poll() is not None:
            break
        now = time.monotonic()
        if now - state["last_output"] > stall_seconds:
            verdict, why = "stalled", "silent"
            break
        if state["token"] is not None and now - state["token_since"] > stall_seconds:
            verdict, why = "stalled", "frozen"
            break
        time.sleep(0.05)

    if verdict != "ok":
        proc.kill()
    try:
        proc.wait(timeout=10.0)
    except subprocess.TimeoutExpired:
        pass
    pump_thread.join(timeout=2.0)
    err_thread.join(timeout=2.0)
    elapsed = time.monotonic() - t0
    stderr = "".join(err_chunks)
    # run_tests.py scores any output containing this marker as a failure; a child traceback
    # quoted verbatim would hijack the parent's verdict.
    stderr = stderr.replace("Traceback (most recent call last)", "Traceback[child]")

    heartbeats = [ln for ln in lines if ln.startswith("HB ")]
    result_lines = [ln for ln in lines if ln.startswith("RESULT ")]
    info = {
        "elapsed": elapsed,
        "returncode": proc.returncode,
        "heartbeats": len(heartbeats),
        "last_heartbeat": heartbeats[-1] if heartbeats else None,
        "why": why,
        "stderr_tail": stderr.strip().splitlines()[-3:],
    }
    if verdict == "ok" and not result_lines:
        verdict = "exit"
    result = json.loads(result_lines[0][len("RESULT "):]) if result_lines else None
    return verdict, result, info


def wedge_message(label, verdict, info):
    """One failure string that names the mechanism, for any non-ok child."""
    if verdict == "stalled" and info["why"] == "silent":
        why = ("the watchdog thread went silent, so the GIL itself is wedged (the shape of the "
               "#412 inversion between the GIL and FrameLock::mtx). Last heartbeat %r, %d "
               "heartbeats total" % (info["last_heartbeat"], info["heartbeats"]))
    elif verdict == "stalled":
        why = ("the heartbeat kept coming but its progress token never changed for %.0fs: the "
               "main loop or a worker is parked for good (deadlock). Last heartbeat %r"
               % (STALL_SECONDS, info["last_heartbeat"]))
    elif verdict == "exit":
        why = ("the child exited (rc=%s) without printing a RESULT line; last heartbeat %r, "
               "stderr tail %r" % (info["returncode"], info["last_heartbeat"], info["stderr_tail"]))
    else:
        why = "the child could not be started: %r" % (info.get("detail"),)
    return "%s child: deadlock/hang (%s after %.2fs): %s" % (label, verdict, info["elapsed"], why)
