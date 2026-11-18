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

# A subclass hover method (position-only dispatch) raises SystemExit. automation.moveTo
# dispatches it synchronously, inside the timer callback's own Python frame: finalizing there
# ran atexit with that frame still live. Headless and windowed.
HOVER = r'''
from mcrfpy import automation
class H(mcrfpy.Frame):
    def on_enter(self, pos):
        print("FIRST", flush=True)
        sys.exit(CODE)
scene = mcrfpy.Scene("h557"); mcrfpy.current_scene = scene
scene.children.append(H(pos=(0, 0), size=(50, 50)))
def first(timer, runtime):
    timer.stop()
    automation.moveTo((10, 10))
'''
SCRIPTS["hover"] = PRELUDE + HOVER + r'''
mcrfpy.Timer("a", first, 10)
mcrfpy.step(0.1)
print("STEP RETURNED")
sys.exit(99)
'''
SCRIPTS["hover_windowed"] = PRELUDE + HOVER + r'''
mcrfpy.Timer("a", first, 1)
'''

# Every drawable's hover method would fire in one walk: only the first may run.
SCRIPTS["hovers"] = PRELUDE + r'''
from mcrfpy import automation
class H(mcrfpy.Frame):
    def on_enter(self, pos):
        print("FIRST" if not hasattr(H, "ran") else "SECOND", flush=True)
        H.ran = True
        sys.exit(CODE)
scene = mcrfpy.Scene("hs557"); mcrfpy.current_scene = scene
for _ in range(3):
    scene.children.append(H(pos=(0, 0), size=(50, 50)))
def first(timer, runtime):
    timer.stop()
    automation.moveTo((10, 10))
mcrfpy.Timer("a", first, 10)
mcrfpy.step(0.1)
print("STEP RETURNED")
sys.exit(99)
'''

# Grid.step() fires every entity's behaviour callback: only the first may run, and the
# SystemExit comes out of grid.step() into the callback that called it.
SCRIPTS["gridstep"] = PRELUDE + r'''
grid = mcrfpy.Grid(grid_size=(8, 8), pos=(0, 0), size=(100, 100), texture=mcrfpy.default_texture)
scene = mcrfpy.Scene("gs557"); mcrfpy.current_scene = scene; scene.children.append(grid)
seen = []
def on_step(trigger, data):
    print("FIRST" if not seen else "SECOND", flush=True)
    seen.append(1)
    sys.exit(CODE)
for i in range(3):
    e = mcrfpy.Entity(grid_pos=(0, i), grid=grid)
    e.step = on_step
    e.set_behavior(mcrfpy.Behavior.WAYPOINT, waypoints=[(1, i)], turns=1)
def first(timer, runtime):
    timer.stop()
    grid.step()
    print("NOT REACHED")
mcrfpy.Timer("a", first, 10)
mcrfpy.step(0.1)
print("STEP RETURNED")
sys.exit(99)
'''

# scene.activate() from a callback, whose on_enter exits: the SystemExit comes out of
# activate() into the callback that called it (nothing after it runs).
SCRIPTS["activate"] = PRELUDE + r'''
class Target(mcrfpy.Scene):
    def on_enter(self):
        print("FIRST", flush=True)
        sys.exit(CODE)
start = mcrfpy.Scene("start557"); mcrfpy.current_scene = start
target = Target("target557")
def first(timer, runtime):
    timer.stop()
    target.activate()
    print("NOT REACHED")
mcrfpy.Timer("a", first, 10)
mcrfpy.step(0.1)
print("STEP RETURNED")
sys.exit(99)
'''

# `-i` (inspect mode): CPython prints a top-level SystemExit and carries on, and so does a
# callback's. The deferred exit must not _Exit(1) there.
SCRIPTS["inspect"] = PRELUDE + r'''
mcrfpy.Scene("i557").activate()
def first(timer, runtime):
    timer.stop()
    print("FIRST", flush=True)
    sys.exit(CODE)
def second(timer, runtime):
    timer.stop()
    print("SECOND", flush=True)
    mcrfpy.exit()
mcrfpy.Timer("a", first, 1)
mcrfpy.Timer("b", second, 30)
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
    for name in ("step", "anim", "advance", "hover", "hovers", "gridstep", "activate"):
        run("%s/%s code 3" % (name, mode), name, 3, mode, 3)
run("step/c code 0", "step", 0, "c", 0)
run("step/c code None", "step", None, "c", 0)
run("step/c message", "step", "boom", "c", 1, expect_stderr="boom")
# Windowed: the frame loop drives the timer, the exit happens at the top of run(). The
# hover case runs the exit inside the timer callback's own Python frame (see HOVER), which
# is what tells a mid-frame finalization from an unwound one; a bare `sys.exit()` in a
# windowed timer callback can not (no Python frame is live around it either way), so it is
# not tested here.
run("hover windowed code 6", "hover_windowed", 6, "windowed", 6)


def run_special(label, name, code, args, expect_rc, must_have, must_lack=(), stderr_has=()):
    tmp = tempfile.mkdtemp(prefix="mcrf557_", dir=os.getcwd())
    try:
        path = os.path.join(tmp, "child.py")
        with open(path, "w") as fh:
            fh.write("CODE = %r\n" % (code,) + SCRIPTS[name])
        try:
            r = subprocess.run([sys.executable] + args(path), capture_output=True, text=True,
                               timeout=DETECTOR_TIMEOUT, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            check(False, "%s: hung" % label)
            return
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    check(r.returncode == expect_rc, "%s: exit code %d (got %d)" % (label, expect_rc, r.returncode),
          "\n" + r.stderr[-500:])
    for m in must_have:
        check(m in r.stdout, "%s: stdout has %r" % (label, m), "\n" + r.stdout[-300:])
    for m in must_lack:
        check(m not in r.stdout, "%s: stdout lacks %r" % (label, m))
    for m in stderr_has:
        check(m in r.stderr, "%s: stderr has %r" % (label, m), "\n" + r.stderr[-300:])


# Under -i a callback's SystemExit is printed and the program carries on, as CPython does
# for a top-level sys.exit(); the deferred exit used to _Exit(1) here (no atexit, no teardown).
run_special("inspect mode (-i) windowed", "inspect", 5, lambda path: ["-i", path], 0,
            must_have=["FIRST", "SECOND"], stderr_has=["SystemExit: 5"])
# Real input events: six key presses are queued while the frame loop is held in a callback
# (a handshake file, no clock), then the next frame polls all of them. The first handler
# asks to exit; the other five must not run. Needs xdotool and the display the suite runs on.
KEYS = r'''
import os, sys, time, mcrfpy
FLAG = %r
sc = mcrfpy.Scene("k557"); mcrfpy.current_scene = sc
n = [0]
def on_key(key, action):
    if action == mcrfpy.InputState.PRESSED:
        n[0] += 1
        print("KEY %%d" %% n[0], flush=True)
        sys.exit(4)
sc.on_key = on_key
def hold(timer, runtime):
    timer.stop()
    print("READY", flush=True)
    while not os.path.exists(FLAG):   # the test sends the keys, then creates FLAG
        time.sleep(0.01)
mcrfpy.Timer("hold", hold, 1)
'''


def run_keys():
    import shutil as _sh
    if not _sh.which("xdotool") or not os.environ.get("DISPLAY"):
        print("SKIP: dispatch stops after an on_key exit (needs xdotool and a display)")
        return
    tmp = tempfile.mkdtemp(prefix="mcrf557_", dir=os.getcwd())
    try:
        flag = os.path.join(tmp, "flag")
        path = os.path.join(tmp, "child.py")
        with open(path, "w") as fh:
            fh.write(KEYS % (flag,))
        proc = subprocess.Popen([sys.executable, "--exec", path], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)
        import threading
        lines = []
        ready = threading.Event()

        def pump():
            for line in proc.stdout:
                lines.append(line.strip())
                if line.strip() == "READY":
                    ready.set()
        t = threading.Thread(target=pump, daemon=True)
        t.start()
        if not ready.wait(DETECTOR_TIMEOUT):
            proc.kill()
            check(False, "keys: the child never reached READY")
            return
        subprocess.run(["xdotool", "key", "--delay", "0", "a", "b", "c", "d", "e", "f"],
                       check=True, timeout=DETECTOR_TIMEOUT)
        open(flag, "w").close()
        try:
            rc = proc.wait(DETECTOR_TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            check(False, "keys: the child did not exit")
            return
        t.join(10)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    keys = [l for l in lines if l.startswith("KEY")]
    check(rc == 4, "keys: exit code 4 (got %d)" % rc)
    check(keys == ["KEY 1"], "keys: only the first of the queued key events was dispatched: %r" % keys)


run_keys()
# mcrfpy.exit() leaves the windowed loop with _Exit(0), which has never run atexit. It is
# a keeps-working check: it passes before and after this change.
run("mcrfpy.exit() windowed", "mcrfpy_exit", 0, "windowed", 0, atexit_runs=False)

if failures:
    print("FAIL (%d)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
