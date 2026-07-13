#!/usr/bin/env python3
"""Regression test for #355 (prerequisite): UIGridView box/position desync.

UIGridView overrode move()/resize() but NOT onPositionChanged(), so assigning
grid.pos / grid.x / grid.y updated UIDrawable::position while the sf::RectangleShape
`box` -- which render() and get_bounds() and every hit test read -- stayed at the
construction-time origin. A repositioned Grid rendered at the stale spot and its
cell hit testing was meaningless.
"""
import sys
import mcrfpy
from mcrfpy import automation

CELL = 16  # default texture cell size


def fail(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    scene = mcrfpy.Scene("pos_sync")
    scene.activate()
    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    scene.children.append(grid)

    # 1. box follows position
    grid.pos = (300, 50)
    origin, size = grid.bounds  # bounds == (pos: Vector, size: Vector), read from `box`
    if (origin.x, origin.y) != (300, 50):
        fail(f"grid.bounds should follow grid.pos; expected origin (300,50), got ({origin.x},{origin.y})")
    if (size.x, size.y) != (200, 200):
        fail(f"grid.bounds size changed unexpectedly: ({size.x},{size.y})")

    clicks = []
    grid.on_cell_click = lambda pos, button, action: clicks.append((pos.x, pos.y))

    # 2. a click at the NEW location resolves the correct cell.
    # center defaults to size/2 => left_spritepixels == 0 => grid-world == local.
    # local (40, 40) -> cell (2, 2)
    automation.click((340, 90))
    if not clicks:
        fail("on_cell_click did not fire for a click inside the repositioned grid")
    if clicks[0] != (2.0, 2.0):
        fail(f"expected cell (2,2) at the new position, got {clicks[0]}")

    # 3. a click at the OLD location resolves nothing.
    clicks.clear()
    automation.click((140, 140))
    if clicks:
        fail(f"click at the old (vacated) position should not hit the grid; got {clicks}")

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
