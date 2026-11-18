"""
Regression test for #549 -- a held key's auto-repeat arrived as another PRESSED, so a game
could not tell a new press from a repeat. InputState.REPEATED is the third state, delivered
to on_key for a KeyPressed of a key that is already held. A synthesized second keyDown with
no keyUp in between is exactly that. Held-key tracking is forgotten on focus loss, so a key
released while unfocused is not reported as a repeat forever.
"""
import sys
import mcrfpy
from mcrfpy import automation

S = mcrfpy.InputState
K = mcrfpy.Key
failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


scene = mcrfpy.Scene("t549")
seen = []
scene.on_key = lambda k, s: seen.append((k, s))
mcrfpy.current_scene = scene


def run(fn):
    del seen[:]
    fn()
    return list(seen)


# the enum
check(S.REPEATED == 2 and S.REPEATED.name == "REPEATED", "InputState.REPEATED == 2")
check([m.name for m in S] == ["PRESSED", "RELEASED", "REPEATED"], "members: %s" % [m.name for m in S])
check(S.REPEATED != S.PRESSED and S.REPEATED != S.RELEASED, "REPEATED is distinct")

# press, hold (two repeats), release
def hold():
    automation.keyDown("a"); automation.keyDown("a"); automation.keyDown("a")
    automation.keyUp("a")
check(run(hold) == [(K.A, S.PRESSED), (K.A, S.REPEATED), (K.A, S.REPEATED), (K.A, S.RELEASED)],
      "press, repeat, repeat, release")

# a fresh press after release is PRESSED again
def again():
    automation.keyDown("a"); automation.keyUp("a")
check(run(again) == [(K.A, S.PRESSED), (K.A, S.RELEASED)], "press after release is PRESSED")

# keys are tracked independently
def two():
    automation.keyDown("a"); automation.keyDown("b"); automation.keyDown("a")
    automation.keyDown("b"); automation.keyUp("a"); automation.keyUp("b")
check([s for _, s in run(two)] == [S.PRESSED, S.PRESSED, S.REPEATED, S.REPEATED, S.RELEASED, S.RELEASED],
      "two keys tracked independently")

# focus loss forgets held keys
def unfocused():
    automation.keyDown("c")
    automation.loseFocus()          # c is released while unfocused: no KeyReleased arrives
    automation.keyDown("c")         # next real press
    automation.keyUp("c")
check([s for _, s in run(unfocused)] == [S.PRESSED, S.PRESSED, S.RELEASED],
      "focus loss clears held-key tracking")

# subclass on_key method gets REPEATED too
sub_seen = []
class Sub(mcrfpy.Scene):
    def on_key(self, key, state):
        sub_seen.append(state)
sub = Sub("t549sub")
sub.activate()
automation.keyDown("d"); automation.keyDown("d"); automation.keyUp("d")
check(sub_seen == [S.PRESSED, S.REPEATED, S.RELEASED], "subclass on_key: %s" % sub_seen)

print("FAIL" if failures else "PASS")
sys.exit(1 if failures else 0)
