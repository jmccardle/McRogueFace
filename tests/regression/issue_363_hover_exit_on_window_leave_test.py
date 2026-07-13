#!/usr/bin/env python3
"""Regression test for #363: cursor leaving the window never fired exit callbacks.

Hover was driven exclusively by sf::Event::MouseMoved -> PyScene::do_mouse_hover.
Nothing handled sf::Event::MouseLeft, so when the cursor left the window while over
a drawable:

- no further MouseMoved arrived,
- on_exit / on_cell_exit never fired for whatever was hovered, and
- grid.hovered_cell stayed stuck reporting a cell the mouse was nowhere near.

A hover-driven affordance (tile highlight, tooltip, range preview) got stranded in
its hovered visual state until the player re-entered the window AND crossed a
boundary. hovered_cell was a lying read.

The fix routes MouseLeft to PyScene::do_mouse_leave(), which re-runs the ordinary
hover walk with hit_allowed=false at the root -- so every drawable that thinks it is
hovered gets its normal exit path, and no drawable can enter. Exit callbacks receive
the last known cursor position (the same convention the DOM's mouseleave uses).

automation.mouseLeave() injects the event; there was no way to simulate it before.
"""
import sys
import mcrfpy
from mcrfpy import automation

CELL = 16
FAILURES = []


def check(cond, msg):
    if not cond:
        print(f"FAIL: {msg}", file=sys.stderr)
        FAILURES.append(msg)


def screen_of_cell(grid, cx, cy):
    """Screen coords of the center of cell (cx, cy) under the view's camera."""
    left_sp = int(grid.center_x - (grid.w / 2.0))
    top_sp = int(grid.center_y - (grid.h / 2.0))
    return (grid.x + ((cx + 0.5) * CELL - left_sp),
            grid.y + ((cy + 0.5) * CELL - top_sp))


def case_grid_cell_exit_fires_on_leave():
    scene = mcrfpy.Scene("leave_grid")
    scene.activate()
    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    scene.children.append(grid)

    enters, exits = [], []
    grid.on_cell_enter = lambda pos: enters.append((pos.x, pos.y))
    grid.on_cell_exit = lambda pos: exits.append((pos.x, pos.y))

    automation.moveTo(screen_of_cell(grid, 2, 2))
    check(enters == [(2, 2)], f"moving onto cell (2,2) should fire on_cell_enter; got {enters}")
    check(grid.hovered_cell == (2, 2),
          f"hovered_cell should be (2, 2) while hovering; got {grid.hovered_cell}")
    check(exits == [], f"nothing should have exited yet; got {exits}")

    # The cursor leaves the window without any further MouseMoved.
    automation.mouseLeave()

    check(exits == [(2, 2)],
          f"leaving the window must fire on_cell_exit for the hovered cell; got {exits}")
    check(grid.hovered_cell is None,
          f"hovered_cell must be None once the cursor has left the window; "
          f"got {grid.hovered_cell}")
    check(enters == [(2, 2)],
          f"leaving the window must not fire any on_cell_enter; got {enters}")


def case_frame_on_exit_fires_on_leave():
    """#363 is an input-layer gap: Frame.on_exit was stranded the same way."""
    scene = mcrfpy.Scene("leave_frame")
    scene.activate()
    frame = mcrfpy.Frame(pos=(50, 50), size=(100, 100))
    scene.children.append(frame)

    entered, exited = [], []
    frame.on_enter = lambda pos: entered.append((pos.x, pos.y))
    frame.on_exit = lambda pos: exited.append((pos.x, pos.y))

    automation.moveTo((100, 100))
    check(len(entered) == 1, f"moving into the frame should fire on_enter; got {entered}")
    check(exited == [], f"nothing should have exited yet; got {exited}")

    automation.mouseLeave()
    check(len(exited) == 1,
          f"leaving the window must fire the frame's on_exit; got {exited}")

    # A second leave is a no-op: nothing is hovered any more.
    automation.mouseLeave()
    check(len(exited) == 1,
          f"a redundant leave must not fire on_exit twice; got {exited}")


def case_reenter_after_leave():
    """Hover state must be genuinely cleared, not just reported clear."""
    scene = mcrfpy.Scene("leave_reenter")
    scene.activate()
    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    scene.children.append(grid)

    enters = []
    grid.on_cell_enter = lambda pos: enters.append((pos.x, pos.y))

    target = screen_of_cell(grid, 3, 3)
    automation.moveTo(target)
    automation.mouseLeave()

    # Re-entering onto the SAME cell must fire on_cell_enter again -- if the leave
    # had only faked the clear, the cell would compare equal and be swallowed.
    automation.moveTo(target)
    check(enters == [(3, 3), (3, 3)],
          f"re-entering the same cell after a leave must fire on_cell_enter again; "
          f"got {enters}")


def main():
    case_grid_cell_exit_fires_on_leave()
    case_frame_on_exit_fires_on_leave()
    case_reenter_after_leave()


if __name__ == "__main__":
    try:
        main()
        if FAILURES:
            print(f"\n{len(FAILURES)} FAILURE(S)", file=sys.stderr)
            sys.exit(1)
        print("PASS")
        sys.exit(0)
    except SystemExit:
        raise
    except Exception as e:
        print(f"\nTEST CRASHED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
