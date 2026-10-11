"""
Regression test for #432 -- automation.scroll(clicks, pos) ignored pos.

The scroll event carried pos, but dispatch hit-tests at the simulated mouse
position, so a scroll aimed away from the cursor landed wherever the cursor was.
Fix: scroll(clicks, pos) moves the simulated mouse to pos first, exactly like
click(pos) does; scroll(clicks) with no pos scrolls at the current position.
"""

import mcrfpy
from mcrfpy import automation
import sys

B = mcrfpy.MouseButton
failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


log = []
scene = mcrfpy.Scene("issue432")
mcrfpy.current_scene = scene

frame = mcrfpy.Frame(pos=(500, 500), size=(100, 100))
frame.on_click = lambda p, b, a: log.append(("frame", b))
grid = mcrfpy.Grid(grid_size=(20, 15), texture=mcrfpy.default_texture,
                   pos=(0, 300), size=(320, 240))
grid.on_click = lambda p, b, a: log.append(("grid", b))
scene.children.append(frame)
scene.children.append(grid)

# Park the cursor over the frame.
automation.moveTo((520, 520))
mcrfpy.step(0.016)

# Aimed at empty space: nothing receives it (pre-fix: the frame under the cursor did).
del log[:]
automation.scroll(1, (40, 40))
mcrfpy.step(0.016)
check(log == [], "scroll at empty space reaches nothing, got %r" % log)
check(tuple(automation.position()) == (40, 40),
      "scroll(pos) moves the simulated mouse to pos, got %r" % (tuple(automation.position()),))

# Aimed at the grid, away from the cursor: the grid receives it.
automation.moveTo((520, 520))
mcrfpy.step(0.016)
del log[:]
automation.scroll(-1, (40, 340))
mcrfpy.step(0.016)
check(log == [("grid", B.SCROLL_DOWN)], "scroll aimed at grid reaches grid, got %r" % log)

# No pos: scrolls at the current mouse position (the grid, after the scroll above).
del log[:]
automation.scroll(1)
mcrfpy.step(0.016)
check(log == [("grid", B.SCROLL_UP)], "scroll() without pos uses current position, got %r" % log)

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
