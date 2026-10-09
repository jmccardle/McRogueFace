"""Regression test for #398: mcrfpy.lock() deadlocked under a headless main loop.

FrameLock's safe window (#219) was opened only from doFrame(), the windowed render
path. runSimFrame() -- the path mcrfpy.step() and mcrfpy.advance() drive -- never
opened it, and FrameLock::acquire() waits on a condition variable with NO timeout.
So a background thread entering `with mcrfpy.lock():` while the main thread advanced
the world headlessly blocked permanently, and the main thread's own step() loop kept
running, which is what made it look like a hung worker rather than a hung engine.

This is the minimal statement of that bug: one background thread, one lock acquire,
one assignment, a step()-driven main loop. It carries no networking, no asyncio and
no socket, so it stays a regression test for the lock and does not quietly become a
second copy of tests/integration/background_thread_network_test.py.

Pre-fix this test reaches its deadline with `acquired` never set and exits 1.

Run: ./mcrogueface --headless --exec ../tests/regression/issue_398_headless_frame_lock_test.py
"""

import sys
import threading
import time

import mcrfpy

STEP_SECONDS = 0.016
DEADLINE_SECONDS = 5.0
SENTINEL_X = 4321.0

scene = mcrfpy.Scene("issue_398")
target = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
scene.children.append(target)
mcrfpy.current_scene = scene

entered = threading.Event()    # worker is about to call acquire()
acquired = threading.Event()   # worker got through acquire() and assigned
worker_error = []


def worker():
    try:
        entered.set()
        with mcrfpy.lock():
            target.x = SENTINEL_X
        acquired.set()
    except BaseException as exc:  # noqa: BLE001 -- reported on the main thread
        worker_error.append(exc)
        entered.set()
        acquired.set()


thread = threading.Thread(target=worker, name="lock-holder", daemon=True)
thread.start()

if not entered.wait(DEADLINE_SECONDS):
    print("FAIL: worker never reached mcrfpy.lock()")
    sys.exit(1)

# The main thread advances the world the way a headless embedder does. Nothing here
# renders, so pre-fix nothing ever signalled the safe window.
steps = 0
deadline = time.monotonic() + DEADLINE_SECONDS
while not acquired.is_set() and time.monotonic() < deadline:
    mcrfpy.step(STEP_SECONDS)
    steps += 1

failures = []

if worker_error:
    failures.append(f"background thread raised {worker_error[0]!r}")

if not acquired.is_set():
    failures.append(
        f"background thread never got through mcrfpy.lock() after {steps} "
        f"mcrfpy.step() calls over {DEADLINE_SECONDS}s -- runSimFrame() is not "
        "opening the #219 safe window (this is #398)")

if target.x != SENTINEL_X:
    failures.append(f"locked mutation did not land (target.x == {target.x}, "
                    f"expected {SENTINEL_X})")

thread.join(timeout=2.0)
if thread.is_alive():
    failures.append("background thread is still parked in FrameLock::acquire()")

print(f"steps to acquire : {steps}")
print(f"locked mutation  : target.x == {target.x}")

if failures:
    for message in failures:
        print(f"FAIL: {message}")
    sys.exit(1)

print("PASS")
sys.exit(0)
