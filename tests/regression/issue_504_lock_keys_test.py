"""
Regression test for #504 -- automation.stringToKey mapped "capslock", "numlock" and
"scrolllock" to LControl, so keyDown("capslock") silently injected a Ctrl press (and
mcrfpy.keyboard.ctrl then read True). The engine's Key enum has no lock keys, so the
names must raise ValueError (Fail Early), never fabricate another key.
"""
import sys
import mcrfpy
from mcrfpy import automation

failures = []


def check(c, m):
    print(("  ok: " if c else "FAIL: ") + m)
    if not c:
        failures.append(m)


names = {n.lower() for n in dir(mcrfpy.Key)}
check(not ({"capslock", "caps_lock", "numlock", "scrolllock"} & names),
      "Key enum has no lock keys (so raising is the only honest answer)")

seen = []
scene = mcrfpy.Scene("issue504")
scene.on_key = lambda k, s: seen.append(k)
mcrfpy.current_scene = scene

for name in ("capslock", "numlock", "scrolllock"):
    for fn in (automation.keyDown, automation.keyUp):
        try:
            fn(name)
        except ValueError:
            check(True, "%s(%r) raises ValueError" % (fn.__name__, name))
        else:
            check(False, "%s(%r) did not raise" % (fn.__name__, name))
    try:
        automation.hotkey("a", name)
    except ValueError:
        check(True, "hotkey('a', %r) raises ValueError" % name)
    else:
        check(False, "hotkey('a', %r) did not raise" % name)

check(not mcrfpy.keyboard.ctrl, "no Ctrl press was fabricated")
check(mcrfpy.Key.LEFT_CONTROL not in seen if hasattr(mcrfpy.Key, "LEFT_CONTROL")
      else all(k.name != "LCONTROL" for k in seen), "no LControl reached on_key")

if failures:
    print("FAIL: %d" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
