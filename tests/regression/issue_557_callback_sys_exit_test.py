"""#557: sys.exit() inside a callback must not finalize the interpreter mid-frame.

A SystemExit raised in a Timer / animation / input callback reached Py_Exit through
PyErr_Print inside the frame loop: finalization ran while the frame's C++ and Python
frames were live (LeakSanitizer reports under `make asan-test`). Now the exit is recorded,
the rest of the frame's callbacks do not run, the frame unwinds, and the exit happens at the
top with the code a top-level sys.exit() would give, through the same atexit/#468 teardown.

The observable for "unwound": an atexit handler registered by the script sees no live Python
frame above it (pre-fix, the script's <module> frame that called step() was still live).
Each scenario runs in a child engine; the timeout is only a hang detector.
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


PRELUDE = r'''
import atexit, mcrfpy, os, sys
def _at_exit():
    f = sys._getframe().f_back
    os.write(1, (b"ATEXIT frames_above=%d\n" % (0 if f is None else 1)))
atexit.register(_at_exit)
'''

SCRIPTS = {}

# Headless: step() drives the frame. The second timer must not run once the first exited.
SCRIPTS["step"] = PRELUDE + r'''
def first(timer, runtime):
    timer.stop()
    print("FIRST", flush=True)
    sys.exit(CODE)
    print("NOT REACHED")
def second(timer, runtime):
    timer.stop()
    print("SECOND", flush=True)
mcrfpy.Timer("a", first, 10)
mcrfpy.Timer("b", second, 10)
mcrfpy.step(0.1)
print("STEP RETURNED")
sys.exit(99)
'''

# Animation callback.
SCRIPTS["anim"] = PRELUDE + r'''
scene = mcrfpy.Scene("s557"); mcrfpy.current_scene = scene
f = mcrfpy.Frame(pos=(0, 0), size=(10, 10)); scene.children.append(f)
def done(t, p, v):
    print("FIRST", flush=True)
    sys.exit(CODE)
f.animate("x", 5.0, 0.01, mcrfpy.Easing.LINEAR, callback=done)
mcrfpy.step(0.1)
print("STEP RETURNED")
sys.exit(99)
'''

# advance() walks several frames: none may run after the exit.
SCRIPTS["advance"] = PRELUDE + r'''
def first(timer, runtime):
    print("FIRST", flush=True)
    sys.exit(CODE)
mcrfpy.Timer("a", first, 10)
mcrfpy.advance(1000)
print("ADVANCE RETURNED")
sys.exit(99)
'''

# Windowed: the real frame loop drives the timer.
SCRIPTS["windowed"] = PRELUDE + r'''
def first(timer, runtime):
    timer.stop()
    print("FIRST", flush=True)
    sys.exit(CODE)
def second(timer, runtime):
    print("SECOND", flush=True)
mcrfpy.Scene("w557").activate()
mcrfpy.Timer("a", first, 1)
mcrfpy.Timer("b", second, 1)
'''

# mcrfpy.exit() keeps working from a callback.
SCRIPTS["mcrfpy_exit"] = PRELUDE + r'''
def first(timer, runtime):
    print("FIRST", flush=True)
    mcrfpy.exit()
mcrfpy.Scene("e557").activate()
mcrfpy.Timer("a", first, 1)
'''


def run(label, name, code, mode, expect_rc, expect_stderr=None, atexit_runs=True):
    tmp = tempfile.mkdtemp(prefix="mcrf557_", dir=os.getcwd())
    try:
        path = os.path.join(tmp, "child.py")
        with open(path, "w") as fh:
            fh.write("CODE = %r\n" % (code,) + SCRIPTS[name])
        if mode == "c":
            with open(path) as fh:
                src = fh.read()
            cmd = [sys.executable, "--headless", "-c", src]
        elif mode == "exec":
            cmd = [sys.executable, "--headless", "--exec", path]
        else:
            cmd = [sys.executable, "--exec", path]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=DETECTOR_TIMEOUT)
        except subprocess.TimeoutExpired:
            check(False, "%s: hung" % label)
            return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    out = r.stdout
    check(r.returncode == expect_rc, "%s: exit code %d (got %d)" % (label, expect_rc, r.returncode), "\n" + r.stderr[-500:])
    check("FIRST" in out, "%s: the callback ran" % label)
    check("SECOND" not in out and "NOT REACHED" not in out and "RETURNED" not in out,
          "%s: nothing runs after the exit: %r" % (label, out[-200:]))
    if atexit_runs:
        check("ATEXIT" in out, "%s: atexit handlers ran" % label)
        check("ATEXIT frames_above=0" in out,
              "%s: the interpreter exits with no frame live above the handler" % label)
    if expect_stderr:
        check(expect_stderr in r.stderr, "%s: stderr has %r" % (label, expect_stderr))
    return r


for mode in ("c", "exec"):
    for name in ("step", "anim", "advance"):
        run("%s/%s code 3" % (name, mode), name, 3, mode, 3)
run("step/c code 0", "step", 0, "c", 0)
run("step/c code None", "step", None, "c", 0)
run("step/c message", "step", "boom", "c", 1, expect_stderr="boom")
run("windowed code 4", "windowed", 4, "windowed", 4)
# mcrfpy.exit() leaves the windowed loop with _Exit(0), which has never run atexit.
run("mcrfpy.exit() windowed", "mcrfpy_exit", 0, "windowed", 0, atexit_runs=False)

if failures:
    print("FAIL (%d)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
