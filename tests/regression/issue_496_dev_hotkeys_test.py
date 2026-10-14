"""
Regression test for #496 -- windowed builds always swallowed ` (Grave) and F4.

GameEngine consumed Grave (ImGui console) and F4 (scene explorer) before any scene
handler ran, so an app that needs every key (a terminal, an editor) could never see
them. Window.console_key / Window.explorer_key now say which key toggles each tool
(a Key, or None for no hotkey), at runtime. Defaults stay Grave and F4.

Two halves:
  * in this process (headless): the property contract. Headless has no developer tools,
    so there the keys always reach on_key and a hotkey change is not observable.
  * a windowed child process (needs a display, like the rest of the suite): what the
    hotkeys actually do to on_key delivery, driven through the same front door window
    events use (GameEngine::filterDevInput).
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
    r["defaults"] = [W.console_key.name, W.explorer_key.name]
    # Default: Grave toggles the console, so it never reaches the game, and while the
    # console is open it owns the keyboard.
    r["grave_default"] = tap("`")
    r["a_while_console_open"] = tap("a")
    r["grave_close"] = tap("`")
    r["a_after_close"] = tap("a")
    r["f4_default"] = tap("f4")
    r["f4_close"] = tap("f4")
    # No console hotkey: Grave reaches the game
    W.console_key = None
    r["grave_none"] = tap("`")
    # Moved: F12 toggles, Grave is an ordinary key
    W.console_key = K.F12
    r["f12_open"] = tap("f12")
    r["f12_close"] = tap("f12")
    r["grave_after_move"] = tap("`")
    # Explorer off
    W.explorer_key = None
    r["f4_none"] = tap("f4")
    # Back to defaults, then the console disabled outright releases its key
    W.console_key = K.GRAVE
    W.explorer_key = K.F4
    mcrfpy.set_dev_console(False)
    r["grave_console_disabled"] = tap("`")
    r["f4_console_disabled"] = tap("f4")
    mcrfpy.set_dev_console(True)
    r["grave_reenabled"] = tap("`")
    tap("`")
    print("RESULT " + json.dumps(r))
    sys.stdout.flush()
    sys.exit(0)

mcrfpy.Timer("go", go, 100)
'''

# --- property contract (headless) -------------------------------------------------
W = mcrfpy.window
check(W.console_key == K.GRAVE and W.explorer_key == K.F4, "defaults are GRAVE and F4")
W.console_key = K.F12
check(W.console_key == K.F12, "console_key round-trips a Key")
W.console_key = None
check(W.console_key is None, "console_key = None means no hotkey")
W.explorer_key = None
check(W.explorer_key is None, "explorer_key = None means no hotkey")
W.console_key = K.F4
check(W.console_key == K.F4, "a freed key can be reused by the other tool")
raises(ValueError, lambda: setattr(W, "explorer_key", K.F4), "the two tools can't share a key")
raises(ValueError, lambda: setattr(W, "console_key", K.UNKNOWN), "Key.UNKNOWN is rejected (use None)")
raises(ValueError, lambda: setattr(W, "console_key", 999), "an out-of-range key is rejected")
raises(TypeError, lambda: setattr(W, "console_key", 3.5), "a float is not a key")
raises(AttributeError, lambda: delattr(W, "console_key"), "the property can't be deleted")
check(W.console_key == K.F4, "failed assignments change nothing")
W.console_key = K.GRAVE
W.explorer_key = K.F4

# Headless has no developer tools, so Grave/F4 reach on_key (and typewrite("`") works)
seen = []
scene = mcrfpy.Scene("issue496")
scene.on_key = lambda k, s: seen.append(k)
mcrfpy.current_scene = scene
automation.keyDown("`")
automation.keyUp("`")
automation.keyDown("f4")
check(seen == [K.GRAVE, K.GRAVE, K.F4], "headless: Grave and F4 are ordinary keys, got %r" % seen)

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
    check(r["defaults"] == ["GRAVE", "F4"], "child defaults %r" % r["defaults"])
    check(r["grave_default"] == [], "Grave toggles the console and is not delivered, got %r" % r["grave_default"])
    check(r["a_while_console_open"] == [], "the open console owns the keyboard, got %r" % r["a_while_console_open"])
    check(r["grave_close"] == [], "Grave closes it, still not delivered")
    check(r["a_after_close"] == both("A"), "keys flow again once it is closed, got %r" % r["a_after_close"])
    check(r["f4_default"] == [] and r["f4_close"] == [], "F4 toggles the explorer and is not delivered")
    check(r["grave_none"] == both("GRAVE"), "console_key=None: Grave reaches on_key, got %r" % r["grave_none"])
    check(r["f12_open"] == [] and r["f12_close"] == [], "console_key=F12: F12 is the hotkey")
    check(r["grave_after_move"] == both("GRAVE"), "console_key=F12: Grave is an ordinary key")
    check(r["f4_none"] == both("F4"), "explorer_key=None: F4 reaches on_key, got %r" % r["f4_none"])
    check(r["grave_console_disabled"] == both("GRAVE"),
          "set_dev_console(False) releases Grave, got %r" % r["grave_console_disabled"])
    check(r["f4_console_disabled"] == both("F4"), "set_dev_console(False) releases F4 too")
    check(r["grave_reenabled"] == [], "set_dev_console(True) restores the hotkey")

if failures:
    print("FAIL: %d check(s) failed" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
