"""Regression test for #411 - any thread could run a frame, concurrently with another.

A background thread that held nothing could call mcrfpy.step()/advance() and it just
worked: the clock moved and a whole frame body (timers, Scene.update, animations,
transitions) ran on that thread, with nothing stopping the main thread from doing the
same at the same time. mcrfpy.lock() synchronised holders against the frame, not two
threads both driving frames -- and it was a no-op on the main thread even when the main
thread was NOT the one running frames.

Decided behaviour: exactly one thread drives the simulation clock. The first thread to
run a frame claims it (the main thread when the engine's own loop starts); other threads
get RuntimeError; ownership passes on only when the owner exits. lock() is a no-op on
the owner, and a real barrier on every other thread, the main thread included.

This file must start with the clock UNCLAIMED, so the background owner case comes first.
step()/advance() argument validation (NaN, inf, negative, overflow) is gated at the end.
"""
import os
import subprocess
import sys
import tempfile
import threading
import time

import mcrfpy

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def metrics():
    m = mcrfpy.get_metrics()
    return m["simulation_time_ms"], m["current_frame"]


def outcome(call):
    try:
        call()
        return "returned"
    except RuntimeError as exc:
        return "clock" if "does not drive the simulation clock" in str(exc) else "RuntimeError: %s" % exc


scene = mcrfpy.Scene("t411")
scene.activate()

# --- 1. A background thread claims the clock; the main thread is now a guest ---
owner_started = threading.Event()
owner_stop = threading.Event()
owner_frames = []


def owner():
    mcrfpy.step(0.016)           # claims the clock
    owner_started.set()
    while not owner_stop.is_set():
        mcrfpy.step(0.016)
        owner_frames.append(1)
        time.sleep(0.001)        # let the GIL go so the main thread can run


th = threading.Thread(target=owner, name="clock-owner", daemon=True)
th.start()
check(owner_started.wait(5.0), "the background thread claimed the clock and ran a frame")

check(outcome(lambda: mcrfpy.step(0.016)) == "clock",
      "main-thread step() is refused while a background thread drives the clock")
check(outcome(lambda: mcrfpy.advance(16)) == "clock", "main-thread advance() likewise")

# The main thread's lock() is a REAL barrier now: while it holds, no frame completes.
with mcrfpy.lock():
    f0 = metrics()[1]
    time.sleep(0.1)              # the owner is free to try; it must park at the window
    f1 = metrics()[1]
check(f0 == f1, "no frame completes while the (non-owner) main thread holds lock() (%d -> %d)" % (f0, f1))
time.sleep(0.05)
check(metrics()[1] > f1, "the owner resumes once the main thread releases")

# --- 2. Ownership passes on when the owner exits ---
owner_stop.set()
th.join(5.0)
check(not th.is_alive(), "the owner thread exited")
check(outcome(lambda: mcrfpy.step(0.016)) == "returned",
      "after the owner exits, the main thread can claim the clock")

# --- 3. Now the main thread owns it: other threads are refused, and lock() still works ---
res = {}


def guest():
    res["step"] = outcome(lambda: mcrfpy.step(0.016))
    res["advance"] = outcome(lambda: mcrfpy.advance(16))
    with mcrfpy.lock():
        res["locked"] = True


g = threading.Thread(target=guest, daemon=True)
g.start()
end = time.monotonic() + 5.0
while g.is_alive() and time.monotonic() < end:
    mcrfpy.step(0.016)           # the owner drives; the guest's lock() needs its window
g.join(1.0)
check(res.get("step") == "clock" and res.get("advance") == "clock",
      "a non-owner background thread is refused (%r)" % res)
check(res.get("locked") is True, "the non-owner's lock() is served by the owner's frames")
with mcrfpy.lock():
    check(mcrfpy.step(0.016) > 0, "the owner's own lock() stays a no-op (step inside it runs)")

# --- 4. --run-forever refuses to start its loop when a background thread owns the clock ---
# The child's driver thread stays alive across run() (ownership lasts until it exits),
# so the conflict is real when the main loop tries to start.
child = os.path.join(tempfile.mkdtemp(prefix="mcrf411_"), "child.py")
with open(child, "w") as fh:
    fh.write(
        "import mcrfpy, threading, time\n"
        "mcrfpy.Scene('c').activate()\n"
        "claimed = threading.Event()\n"
        "def drive():\n"
        "    mcrfpy.step(0.016); claimed.set(); time.sleep(5)\n"
        "threading.Thread(target=drive, daemon=True).start()\n"
        "claimed.wait(5)\n"
    )
try:
    proc = subprocess.run([sys.executable, "--headless", "--run-forever", "--exec", child],
                          capture_output=True, text=True, timeout=20)
    check(proc.returncode != 0 and "already driving the simulation clock" in proc.stderr,
          "--run-forever refuses to start a second frame driver (rc=%r)" % proc.returncode)
except subprocess.TimeoutExpired:
    check(False, "--run-forever with a background clock owner ran instead of refusing")

# --- 5. step()/advance() argument validation ---
for bad, exc in ((-1.0, ValueError), (float("nan"), ValueError), (float("inf"), ValueError),
                 (1e10, OverflowError)):
    before = metrics()
    try:
        mcrfpy.step(bad)
        check(False, "step(%r) must raise %s" % (bad, exc.__name__))
    except exc:
        check(metrics() == before, "step(%r) raises %s and runs nothing" % (bad, exc.__name__))
try:
    mcrfpy.advance(2**31 - 1)
    check(False, "advance() past the clock's range must raise OverflowError")
except OverflowError:
    check(True, "advance() past the clock's range raises OverflowError")

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
