"""
Regression test for #548 -- the horizontal mouse wheel was dropped.

MouseButton gains SCROLL_LEFT=12 / SCROLL_RIGHT=13, delivered through the same
paths as SCROLL_UP / SCROLL_DOWN (Frame.on_click property and subclass method,
GridView.on_cell_click), with the keyboard modifiers of the last key event.
automation.scroll(clicks, pos, horizontal=True) injects the horizontal wheel;
engine convention (SFML): positive delta = left, negative = right.

The SDL2 diagonal-scroll split (one vertical + one horizontal event) lives in
SDL2Renderer.cpp and is not reachable from a headless test.
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


check(B.SCROLL_LEFT == 12 and B.SCROLL_RIGHT == 13, "enum values 12 / 13")
check(B(12) is B.SCROLL_LEFT and B(13) is B.SCROLL_RIGHT, "ints map back to members")

log = []


class SubFrame(mcrfpy.Frame):
    def on_click(self, pos, button, action):
        log.append(("subframe", button, action, mcrfpy.keyboard.shift))


class SubGrid(mcrfpy.Grid):
    def on_cell_click(self, cell, button, action):
        log.append(("subcell", button, action, mcrfpy.keyboard.shift))


scene = mcrfpy.Scene("issue548")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(10, 10), texture=mcrfpy.default_texture, pos=(0, 0), size=(160, 160))
grid.on_cell_click = lambda c, b, a: log.append(("cell", b, a, mcrfpy.keyboard.shift))
frame = mcrfpy.Frame(pos=(200, 0), size=(100, 100))
frame.on_click = lambda p, b, a: log.append(("frame", b, a, mcrfpy.keyboard.shift))
subframe = SubFrame(pos=(400, 0), size=(100, 100))
subgrid = SubGrid(grid_size=(10, 10), texture=mcrfpy.default_texture, pos=(0, 200), size=(160, 160))
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
    got = events_at(pos, lambda p: automation.scroll(1, p, horizontal=True))
    check(got == [(name, B.SCROLL_LEFT, S.PRESSED, False)],
          "%s: horizontal +1 -> SCROLL_LEFT, got %r" % (name, got))
    got = events_at(pos, lambda p: automation.scroll(-1, p, horizontal=True))
    check(got == [(name, B.SCROLL_RIGHT, S.PRESSED, False)],
          "%s: horizontal -1 -> SCROLL_RIGHT, got %r" % (name, got))
    # vertical unchanged, one event per axis
    got = events_at(pos, lambda p: automation.scroll(1, p))
    check(got == [(name, B.SCROLL_UP, S.PRESSED, False)],
          "%s: vertical still SCROLL_UP, got %r" % (name, got))
    # a diagonal scroll is two events, one per axis
    got = events_at(pos, lambda p: (automation.scroll(1, p), automation.scroll(-1, p, horizontal=True)))
    check([g[1] for g in got] == [B.SCROLL_UP, B.SCROLL_RIGHT],
          "%s: diagonal -> SCROLL_UP then SCROLL_RIGHT, got %r" % (name, got))

# Modifiers are carried, as for vertical scroll.
automation.keyDown("shiftleft")
got = events_at((220, 20), lambda p: automation.scroll(1, p, horizontal=True))
automation.keyUp("shiftleft")
check(got == [("frame", B.SCROLL_LEFT, S.PRESSED, True)],
      "shift held -> modifiers carried on SCROLL_LEFT, got %r" % got)

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
