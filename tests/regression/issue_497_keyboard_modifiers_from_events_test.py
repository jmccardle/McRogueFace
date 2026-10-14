"""
Regression test for #497 -- mcrfpy.keyboard.shift/ctrl/alt/system polled the hardware.

They read sf::Keyboard::isKeyPressed(), so a synthesized event (automation) never
changed them, and in a windowed run they could disagree with the event being handled
(focus change, events queued behind a slow frame). Now they report the modifiers
carried by the key event being handled, and keep that value until the next key event
(or until focus is lost).
"""

import mcrfpy
from mcrfpy import automation
import sys

K = mcrfpy.Key
P = mcrfpy.InputState.PRESSED
R = mcrfpy.InputState.RELEASED
failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


seen = []


def on_key(key, state):
    kb = mcrfpy.keyboard
    seen.append((key, state, kb.shift, kb.ctrl, kb.alt, kb.system))


scene = mcrfpy.Scene("issue497")
scene.on_key = on_key
mcrfpy.current_scene = scene


def run(fn):
    del seen[:]
    fn()
    mcrfpy.step(0.016)
    return list(seen)


# --- typewrite("A"): Shift down, A down/up, Shift up -----------------------------
got = run(lambda: automation.typewrite("A"))
check(got == [
    (K.LEFT_SHIFT, P, True, False, False, False),
    (K.A, P, True, False, False, False),
    (K.A, R, True, False, False, False),
    (K.LEFT_SHIFT, R, False, False, False, False),
], "typewrite('A') reports shift=True inside on_key for A, got %r" % got)

# --- after the sequence, nothing is held --------------------------------------
kb = mcrfpy.keyboard
check((kb.shift, kb.ctrl, kb.alt, kb.system) == (False, False, False, False),
      "all modifiers False after release")

# --- ctrl + alt combination, each modifier reported independently --------------
got = run(lambda: automation.hotkey("ctrl", "alt", "x"))
mods_at_x = [g for g in got if g[0] == K.X and g[1] == P]
check(len(mods_at_x) == 1 and mods_at_x[0][2:] == (False, True, True, False),
      "hotkey(ctrl, alt, x): X pressed with ctrl+alt only, got %r" % mods_at_x)
check(got[-1][2:] == (False, False, False, False), "everything released at the end")

# --- right-side modifier, and releasing one of two keeps the other -------------
def two_shifts():
    automation.keyDown("shiftleft")
    automation.keyDown("shiftright")
    automation.keyUp("shiftleft")
    automation.keyDown("a")
    automation.keyUp("a")
    automation.keyUp("shiftright")


got = run(two_shifts)
a_press = [g for g in got if g[0] == K.A and g[1] == P][0]
check(a_press[2] is True, "shift still held after releasing only LEFT_SHIFT of two")
check(got[-1][2] is False, "shift False after the last shift is released")

# --- the value is the event's, not the state of anything else ------------------
# Between events it is held, so a timer/mouse handler sees the last key event's mods.
automation.keyDown("ctrlleft")
mcrfpy.step(0.016)
check(mcrfpy.keyboard.ctrl is True, "ctrl stays True between events while held")
automation.keyUp("ctrlleft")
mcrfpy.step(0.016)
check(mcrfpy.keyboard.ctrl is False, "ctrl False once released")

# --- repr agrees with the properties ------------------------------------------
automation.keyDown("shiftleft")
r = repr(mcrfpy.keyboard)
check("shift=True" in r, "repr agrees with .shift: %s" % r)
automation.keyUp("shiftleft")

if failures:
    print("FAIL: %d check(s) failed" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
