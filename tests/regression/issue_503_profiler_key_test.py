"""
Regression test for #503 -- F3 (profiler overlay) was swallowed unconditionally, even
headless where there is no overlay. Window.profiler_key (a Key, or None for no hotkey,
default Key.F3) says which key toggles it, modelled on console_key / explorer_key (#496).

Two halves, like the #496 test:
  * this process (headless): the property contract, plus F3 reaching on_key (headless
    has no overlay to toggle).
  * a windowed child (needs a display): the hotkey is consumed, press and release, and
    moving it / setting None releases F3 to the game.
"""

import json
import os
import subprocess
import sys
import tempfile

import mcrfpy
from mcrfpy import automation

K = mcrfpy.Key
failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def raises(exc, fn, msg):
    try:
        fn()
    except exc:
        check(True, msg)
    except Exception as e:
        check(False, "%s (raised %r)" % (msg, e))
    else:
        check(False, msg + " (did not raise)")


CHILD = r'''
import json, sys
import mcrfpy
from mcrfpy import automation
K = mcrfpy.Key
W = mcrfpy.window
seen = []
scene = mcrfpy.Scene("child")
scene.on_key = lambda k, s: seen.append(k.name)
mcrfpy.current_scene = scene
results = {}

def tap(name):
    del seen[:]
    automation.keyDown(name)
    automation.keyUp(name)
    return list(seen)

def go(timer, runtime):
    timer.stop()
    r = results
    r["default"] = W.profiler_key.name
    r["f3_default"] = tap("f3")
    W.profiler_key = None
    r["f3_none"] = tap("f3")
    W.profiler_key = K.F12
    r["f12_moved"] = tap("f12")
    r["f3_after_move"] = tap("f3")
    # the profiler hotkey is independent of the ImGui console
    W.profiler_key = K.F3
    mcrfpy.set_dev_console(False)
    r["f3_console_disabled"] = tap("f3")
    mcrfpy.set_dev_console(True)
    print("RESULT " + json.dumps(r))
    sys.stdout.flush()
    sys.exit(0)

mcrfpy.Timer("go", go, 100)
'''

# --- property contract (headless) -------------------------------------------------
W = mcrfpy.window
check(W.profiler_key == K.F3, "default is F3")
W.profiler_key = K.F12
check(W.profiler_key == K.F12, "profiler_key round-trips a Key")
W.profiler_key = None
check(W.profiler_key is None, "profiler_key = None means no hotkey")
W.profiler_key = K.F3
raises(ValueError, lambda: setattr(W, "profiler_key", K.F4), "can't share the explorer's key")
raises(ValueError, lambda: setattr(W, "profiler_key", K.GRAVE), "can't share the console's key")
raises(ValueError, lambda: setattr(W, "console_key", K.F3), "console_key can't take the profiler's key")
raises(ValueError, lambda: setattr(W, "explorer_key", K.F3), "explorer_key can't take the profiler's key")
raises(ValueError, lambda: setattr(W, "profiler_key", K.UNKNOWN), "Key.UNKNOWN is rejected (use None)")
raises(ValueError, lambda: setattr(W, "profiler_key", 999), "an out-of-range key is rejected")
raises(TypeError, lambda: setattr(W, "profiler_key", 3.5), "a float is not a key")
raises(AttributeError, lambda: delattr(W, "profiler_key"), "the property can't be deleted")
check(W.profiler_key == K.F3, "failed assignments change nothing")

# Headless has no overlay, so F3 is an ordinary key (press AND release)
seen = []
scene = mcrfpy.Scene("issue503")
scene.on_key = lambda k, s: seen.append(k)
mcrfpy.current_scene = scene
automation.keyDown("f3")
automation.keyUp("f3")
check(seen == [K.F3, K.F3], "headless: F3 reaches on_key, got %r" % seen)

# --- hotkey behaviour (windowed child) ----------------------------------------------
with tempfile.TemporaryDirectory() as d:
    script = os.path.join(d, "child.py")
    with open(script, "w") as f:
        f.write(CHILD)
    env = dict(os.environ, ALSOFT_DRIVERS="null")
    proc = subprocess.run([sys.executable, "--exec", script], capture_output=True, text=True,
                          timeout=90, env=env, cwd=os.path.dirname(sys.executable))
lines = [l for l in proc.stdout.splitlines() if l.startswith("RESULT ")]
if not lines:
    check(False, "windowed child produced no result (exit %s)\nstdout:\n%s\nstderr:\n%s"
          % (proc.returncode, proc.stdout[-1500:], proc.stderr[-1500:]))
else:
    r = json.loads(lines[0][len("RESULT "):])
    both = lambda k: [k, k]
    check(r["default"] == "F3", "child default %r" % r["default"])
    check(r["f3_default"] == [], "F3 toggles the overlay and is not delivered, got %r" % r["f3_default"])
    check(r["f3_none"] == both("F3"), "profiler_key=None: F3 reaches on_key, got %r" % r["f3_none"])
    check(r["f12_moved"] == [], "profiler_key=F12: F12 is the hotkey, got %r" % r["f12_moved"])
    check(r["f3_after_move"] == both("F3"), "profiler_key=F12: F3 is an ordinary key")
    check(r["f3_console_disabled"] == [], "set_dev_console(False) does not touch the profiler hotkey")

if failures:
    print("FAIL: %d check(s) failed" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
