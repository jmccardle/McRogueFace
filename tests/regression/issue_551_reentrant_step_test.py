"""#551: mcrfpy.step()/advance() from inside a running frame raise RuntimeError.

A Timer callback that called step() ran a nested frame whose timer pass erased the stopped
timer out from under the outer pass's iterator (segfault; without stop() it recursed). A frame
cannot be re-entered, from any callback that runs inside one: raise, and say so.

Each scenario runs in a child engine; a crash or hang is a failure, caught by a fixed
subprocess timeout that is only a failure detector.
"""
import subprocess
import sys

DETECTOR_TIMEOUT = 300  # seconds; never a speed assertion
failures = []


def check(cond, msg, detail=""):
    # detail (a child's stderr) is shown only on failure: it may hold tracebacks the
    # scenario causes on purpose, and the runner treats any traceback in the output as a fail.
    print(("ok: " if cond else "FAIL: ") + msg + ("" if cond else detail))
    if not cond:
        failures.append(msg)


def run(label, source):
    try:
        r = subprocess.run([sys.executable, "--headless", "-c", source],
                           capture_output=True, text=True, timeout=DETECTOR_TIMEOUT)
    except subprocess.TimeoutExpired:
        check(False, "%s: hung" % label)
        return None
    check(r.returncode == 0, "%s: exits 0 (rc=%d)" % (label, r.returncode), "\n" + r.stderr[-600:])
    return r


# The reproducer from the issue, with the nested call caught.
r = run("timer callback", r'''
import mcrfpy, sys
seen = []
def cb(timer, runtime):
    timer.stop()
    for fn, arg in ((mcrfpy.step, 0.1), (mcrfpy.advance, 10)):
        try:
            fn(arg)
            seen.append("%s ran" % fn.__name__)
        except RuntimeError as e:
            seen.append("%s: %s" % (fn.__name__, e))
mcrfpy.Timer("t", cb, 10)
mcrfpy.step(0.1)
for s in seen: print("SEEN", s)
print("done")
sys.exit(0)
''')
if r:
    seen = [l for l in r.stdout.splitlines() if l.startswith("SEEN ")]
    check(len(seen) == 2 and all("already in progress" in l for l in seen),
          "timer: step() and advance() both refused: %r" % seen)
    check("done" in r.stdout, "timer: the outer step() returned normally")

# Uncaught: the traceback is the callback error; the engine survives it.
r = run("uncaught in timer", r'''
import mcrfpy, sys
def cb(timer, runtime):
    timer.stop()
    mcrfpy.step(0.1)
mcrfpy.Timer("t", cb, 10)
mcrfpy.step(0.1)
print("survived")
sys.exit(0)
''')
if r:
    check("survived" in r.stdout and "already in progress" in r.stderr,
          "uncaught: engine survives, error reported on stderr")

# Animation callback and Scene.update() run inside the frame too.
r = run("animation + scene update", r'''
import mcrfpy, sys
seen = []
def attempt(tag):
    try:
        mcrfpy.step(0.1)
        seen.append(tag + " ran")
    except RuntimeError as e:
        seen.append(tag + ": " + str(e))
class S(mcrfpy.Scene):
    def update(self, dt): attempt("update")
scene = S("s551")
mcrfpy.current_scene = scene
f = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
scene.children.append(f)
f.animate("x", 50.0, 0.05, mcrfpy.Easing.LINEAR, callback=lambda t, p, v: attempt("anim"))
for _ in range(3): mcrfpy.step(0.1)
for s in sorted(set(seen)): print("SEEN", s)
sys.exit(0)
''')
if r:
    seen = [l for l in r.stdout.splitlines() if l.startswith("SEEN ")]
    check(len(seen) == 2 and all("already in progress" in l for l in seen),
          "animation + update refused: %r" % seen)

# Outside a frame step() still works, including after a refused nested call.
r = run("step still works", r'''
import mcrfpy, sys
n = []
def cb(timer, runtime):
    try: mcrfpy.step(0.1)
    except RuntimeError: n.append(1)
mcrfpy.Timer("t", cb, 10)
mcrfpy.step(0.1); mcrfpy.step(0.1)
assert len(n) >= 2, n
print("ok")
sys.exit(0)
''')

if failures:
    print("FAIL (%d)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
