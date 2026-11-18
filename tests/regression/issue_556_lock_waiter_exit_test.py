"""#556: exit must not hang when a non-daemon thread is blocked in mcrfpy.lock().

CPython joins non-daemon threads at exit, but the frame loop has stopped, so the lock's
window never opens again. Once shutdown begins the lock stops blocking: waiters wake and
lock() raises RuntimeError("engine is shutting down") in their thread; later lock() calls
raise at once. It never grants the lock (the main thread is no longer parked).

The child runs in a subprocess; a hang is caught by the fixed timeout, which is only a
failure detector.
"""
import os
import shutil
import subprocess
import sys
import tempfile

DETECTOR_TIMEOUT = 300
failures = []


def check(cond, msg, detail=""):
    # detail (a child's stderr) is shown only on failure: it may hold tracebacks the
    # scenario causes on purpose, and the runner treats any traceback in the output as a fail.
    print(("ok: " if cond else "FAIL: ") + msg + ("" if cond else detail))
    if not cond:
        failures.append(msg)


WORKER = r'''
import mcrfpy, os, sys, threading, time
def say(s): os.write(1, (s + "\n").encode())

def worker():
    try:
        with mcrfpy.lock():
            say("WORKER granted")
    except RuntimeError as e:
        say("WORKER first: %s" % e)
    try:
        with mcrfpy.lock():
            say("WORKER granted-again")
    except RuntimeError as e:
        say("WORKER later: %s" % e)

def start_and_wait():
    t = threading.Thread(target=worker)   # non-daemon
    t.start()
    while mcrfpy.get_metrics()["lock_waiting"] != 1:
        time.sleep(0.001)
'''

SCRIPTS = {
    # The reproducer: nothing steps after the script ends.
    "headless": WORKER + r'''
mcrfpy.current_scene = mcrfpy.Scene("r556")
start_and_wait()
sys.exit(0)
''',
    # Windowed: the exit happens inside a frame, which unwinds without opening a window.
    "windowed": WORKER + r'''
mcrfpy.Scene("w556").activate()
def cb(timer, runtime):
    timer.stop()
    start_and_wait()
    sys.exit(0)
mcrfpy.Timer("t", cb, 1)
''',
}


def run(label, name, args):
    tmp = tempfile.mkdtemp(prefix="mcrf556_", dir=os.getcwd())
    try:
        path = os.path.join(tmp, "child.py")
        with open(path, "w") as fh:
            fh.write(SCRIPTS[name])
        try:
            r = subprocess.run([sys.executable] + args + ["--exec", path],
                               capture_output=True, text=True, timeout=DETECTOR_TIMEOUT)
        except subprocess.TimeoutExpired:
            check(False, "%s: exit hung with a thread blocked in lock()" % label)
            return
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    check(r.returncode == 0, "%s: exits 0 (rc=%d)" % (label, r.returncode), "\n" + r.stderr[-500:])
    check("WORKER first: engine is shutting down" in r.stdout,
          "%s: the waiter's lock() raised: %r" % (label, r.stdout[-300:]))
    check("WORKER later: engine is shutting down" in r.stdout,
          "%s: a later lock() raises at once" % label)
    check("granted" not in r.stdout, "%s: the lock was never granted" % label)


run("headless", "headless", ["--headless"])
run("windowed", "windowed", [])

if failures:
    print("FAIL (%d)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
