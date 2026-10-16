"""
Regression test for #506 -- automation.hotkey() pressed each key while it was still
validating the later ones, so hotkey("ctrl", "nokey") raised ValueError but left Ctrl
held (mcrfpy.keyboard.ctrl True, no release ever sent). A bad name must raise before
any key is pressed.
"""
import sys
import mcrfpy
from mcrfpy import automation

failures = []


def check(c, m):
    print(("  ok: " if c else "FAIL: ") + m)
    if not c:
        failures.append(m)


events = []
scene = mcrfpy.Scene("issue506")
scene.on_key = lambda k, s: events.append((k, s))
mcrfpy.current_scene = scene

for args in (("ctrl", "nokey"), ("shift", "ctrl", "nokey"), ("nokey",), ("ctrl", "a", "capslock")):
    try:
        automation.hotkey(*args)
    except ValueError:
        check(True, "hotkey%r raises ValueError" % (args,))
    else:
        check(False, "hotkey%r did not raise" % (args,))
    mcrfpy.step(0.016)
    check(not events, "hotkey%r injected no key events (got %d)" % (args, len(events)))
    check(not (mcrfpy.keyboard.ctrl or mcrfpy.keyboard.shift),
          "hotkey%r left no modifier held" % (args,))
    events.clear()

# A valid combination still presses in order and releases in reverse.
automation.hotkey("ctrl", "a")
mcrfpy.step(0.016)
check(len(events) == 4, "hotkey('ctrl', 'a') delivers 4 events (got %d)" % len(events))
check(not mcrfpy.keyboard.ctrl, "Ctrl is released after a valid hotkey")

if failures:
    print("FAIL: %d" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
