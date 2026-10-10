"""
Regression test for #428 -- scrolling over a grid cell delivered MouseButton.X1/X2
to on_cell_click instead of SCROLL_UP/SCROLL_DOWN.

Root cause: the engine's mouse action names ("wheel_up", ...) were converted to
MouseButton by private tables in each dispatcher. UIGridView's mapped the wheel to
3/4 (X1/X2); the others mapped it to 10/11. All of them turned an unknown name
into LEFT, and two fell back to a bare str/int if the enum call failed. Now one
converter (PyMouseButton::from_action_name) serves every dispatcher and an unknown
name is reported, not delivered.

The same audit found that X1/X2 were never registered as actions, so on_click
could not receive the X1/X2 the enum advertises, and that automation's button=
strings were a fourth copy that clicked LEFT for any unknown name.

Checks every dispatch path with every button: Frame.on_click (property), a Frame
subclass's on_click method, GridView.on_cell_click (property), and a GridView
subclass's on_cell_click method.
"""

import mcrfpy
from mcrfpy import automation
import sys

B = mcrfpy.MouseButton
S = mcrfpy.InputState
failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


log = []


class SubFrame(mcrfpy.Frame):
    def on_click(self, pos, button, action):
        log.append(("subframe", button, action))


class SubGrid(mcrfpy.Grid):
    def on_cell_click(self, cell, button, action):
        log.append(("subcell", button, action))


scene = mcrfpy.Scene("issue428")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160))
grid.on_cell_click = lambda c, b, a: log.append(("cell", b, a))
frame = mcrfpy.Frame(pos=(200, 0), size=(100, 100))
frame.on_click = lambda p, b, a: log.append(("frame", b, a))
subframe = SubFrame(pos=(400, 0), size=(100, 100))
subgrid = SubGrid(grid_size=(10, 10), pos=(0, 200), size=(160, 160))
for d in (grid, frame, subframe, subgrid):
    scene.children.append(d)

TARGETS = [("cell", (40, 40)), ("frame", (220, 20)),
           ("subframe", (420, 20)), ("subcell", (40, 240))]


def events_at(pos, action):
    del log[:]
    automation.moveTo(pos)
    action(pos)
    mcrfpy.step(0.01)
    return list(log)


for name, pos in TARGETS:
    got = events_at(pos, lambda p: automation.scroll(1, p))
    check(got == [(name, B.SCROLL_UP, S.PRESSED)],
          "%s: scroll up -> SCROLL_UP, got %r" % (name, got))
    got = events_at(pos, lambda p: automation.scroll(-1, p))
    check(got == [(name, B.SCROLL_DOWN, S.PRESSED)],
          "%s: scroll down -> SCROLL_DOWN, got %r" % (name, got))
    for btn, member in (("left", B.LEFT), ("right", B.RIGHT), ("middle", B.MIDDLE),
                        ("x1", B.X1), ("x2", B.X2)):
        got = events_at(pos, lambda p: automation.click(p, button=btn))
        check(got == [(name, member, S.PRESSED), (name, member, S.RELEASED)],
              "%s: click %s -> %r pressed+released, got %r" % (name, btn, member, got))

# Every delivered value is the enum member, never a fallback str/int.
check(all(type(b) is B and type(a) is S for _, b, a in log), "enum types delivered")

# automation's button= names: an unknown one raises instead of clicking LEFT.
for bad in ("bogus", "LEFT", "wheel_up"):
    del log[:]
    try:
        automation.click((220, 20), button=bad)
        raised = False
    except ValueError:
        raised = True
    mcrfpy.step(0.01)
    check(raised and log == [], "automation.click(button=%r) raises ValueError, clicks nothing" % bad)

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
