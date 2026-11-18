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


SCRIPTS["atexit"] = r'''
import atexit, mcrfpy, os, sys
def say(s): os.write(1, (s + "\n").encode())
mcrfpy.current_scene = mcrfpy.Scene("a556")

# The thread that drives the clock (here the main thread, which owns it when nobody else
# does) can always take its own lock: it is a no-op there, and it stayed one after shutdown
# began. Both an atexit handler and a __del__ run after the lock closed.
def at_exit():
    try:
        with mcrfpy.lock():
            say("ATEXIT lock ok")
    except RuntimeError as e:
        say("ATEXIT lock raised: %s" % e)
atexit.register(at_exit)

class Late:
    def __del__(self, _say=say, _lock=mcrfpy.lock):
        try:
            with _lock():
                _say("DEL lock ok")
        except RuntimeError as e:
            _say("DEL lock raised: %s" % e)
late = Late()
sys.exit(0)
'''

# A background thread drives the clock (#411). The exiting main thread is not the clock
# owner, so frames are still being run: a waiter's lock() must keep working, and only when
# the driver thread has finished (nothing can open a window any more) does the lock close.
SCRIPTS["bg_owner"] = r'''
import mcrfpy, os, sys, threading, time
def say(s): os.write(1, (s + "\n").encode())
mcrfpy.current_scene = mcrfpy.Scene("b556")

claimed = threading.Event()
w1_done = threading.Event()
driver_stopped = threading.Event()

def main_exiting():
    # False once threading._shutdown() has run the registered atexit hooks (ours included)
    return threading.main_thread().is_alive()

def driver():
    mcrfpy.step(0.01)           # claims the clock
    claimed.set()
    while not w1_done.is_set():
        mcrfpy.step(0.01)
        time.sleep(0.001)
    driver_stopped.set()        # no step() after this: no window will ever open again

def waiter1():
    while main_exiting():
        time.sleep(0.001)
    try:
        with mcrfpy.lock():
            say("W1 granted")
    except RuntimeError as e:
        say("W1 raised: %s" % e)
    w1_done.set()

def waiter2():
    driver_stopped.wait()
    try:
        with mcrfpy.lock():
            say("W2 granted")
    except RuntimeError as e:
        say("W2 raised: %s" % e)

for fn in (driver, waiter1, waiter2):
    threading.Thread(target=fn).start()    # non-daemon
claimed.wait()
sys.exit(0)
'''


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


def run_plain(label, name, args, expect):
    tmp = tempfile.mkdtemp(prefix="mcrf556_", dir=os.getcwd())
    try:
        path = os.path.join(tmp, "child.py")
        with open(path, "w") as fh:
            fh.write(SCRIPTS[name])
        try:
            r = subprocess.run([sys.executable] + args + ["--exec", path],
                               capture_output=True, text=True, timeout=DETECTOR_TIMEOUT)
        except subprocess.TimeoutExpired:
            check(False, "%s: exit hung" % label)
            return
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    check(r.returncode == 0, "%s: exits 0 (rc=%d)" % (label, r.returncode), "\n" + r.stderr[-500:])
    for m in expect:
        check(m in r.stdout, "%s: stdout has %r" % (label, m), "\n" + r.stdout[-400:])


run_plain("main thread owns the clock: atexit and __del__ keep their lock", "atexit",
          ["--headless"], ["ATEXIT lock ok", "DEL lock ok"])
run_plain("a background thread owns the clock: lock stays usable, then closes", "bg_owner",
          ["--headless"], ["W1 granted", "W2 raised: engine is shutting down"])
run("headless", "headless", ["--headless"])
run("windowed", "windowed", [])

if failures:
    print("FAIL (%d)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
