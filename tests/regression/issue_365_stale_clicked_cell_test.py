#!/usr/bin/env python3
"""Regression test for #365: stale last_clicked_cell dispatched for a dataless view.

#355 made UIGridView::last_clicked_cell the channel by which click_at hands the
resolved cell to dispatchCellClick (the point cannot be recomputed later --
click_at works in parent-local space, PyScene only has global coords).

Two halves let a stale cell survive into a later dispatch:

1. click_at stashed the cell (step 3) even when it went on to return nullptr
   because the view had no handlers. Nothing consumed that stash --
   dispatchCellClick only runs on the drawable PyScene got back, and it got
   nullptr. The cell sat there indefinitely.
2. click_at's early return for the no-grid_data case returns `this` (when
   click_callable || is_python_subclass) WITHOUT clearing last_clicked_cell.

So: click a cell on a grid with no handlers, then enable interactivity and drop
grid_data, then click the (now cell-less) view -- and on_cell_click fired with a
cell from a grid that no longer exists. A wrong-data dispatch, not a missing one.

NOTE: the issue as filed described this as "click a cell, set grid = None, click
again," which does NOT reproduce -- dispatchCellClick *consumes*
last_clicked_cell (sets it to nullopt after reading), so a cell that was actually
dispatched cannot survive. The unconsumed no-handler stash is the real path.
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


def case_stale_survives_into_dataless_view():
    scene = mcrfpy.Scene("stale_cell")
    scene.activate()
    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    scene.children.append(grid)
    target = screen_of_cell(grid, 2, 2)

    # 1. Click with NO handlers: click_at resolves cell (2,2), stashes it, then
    #    returns nullptr. PyScene has no target, so nothing consumes the stash.
    automation.click(target)

    # 2. Enable interactivity, then drop the grid data. on_click is what makes
    #    click_at return `this` on the !grid_data path at all.
    cell_clicks, plain_clicks = [], []
    grid.on_cell_click = lambda pos, button, action: cell_clicks.append((pos.x, pos.y))
    grid.on_click = lambda pos, button, action: plain_clicks.append((pos.x, pos.y))
    grid.grid_data = None  # property is `grid_data`; the ctor kwarg is `grid`
    check(grid.grid_data is None, "grid_data should be None after assignment")

    # 3. Click the cell-less view. It must still deliver on_click, but a grid with
    #    no cells cannot produce a cell event.
    automation.click(target)
    check(len(plain_clicks) >= 1,
          f"the dataless view should still deliver on_click; got {plain_clicks}")
    check(cell_clicks == [],
          f"on_cell_click must NOT fire for a view with no grid data "
          f"(stale last_clicked_cell dispatched); got {cell_clicks}")


def case_no_handler_click_leaves_no_stash():
    """The stash itself must not outlive a click that had nowhere to dispatch."""
    scene = mcrfpy.Scene("stale_cell_2")
    scene.activate()
    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    scene.children.append(grid)

    # Click cell (1,1) with no handlers -> nothing may be retained.
    automation.click(screen_of_cell(grid, 1, 1))

    # Now attach a cell handler and click a spot that resolves to NO cell (well
    # outside the grid's cells but still inside the widget box, reached by
    # shrinking the camera so the 5x5 grid does not fill the 200x200 widget).
    cell_clicks = []
    grid.on_cell_click = lambda pos, button, action: cell_clicks.append((pos.x, pos.y))
    grid.zoom = 0.5  # 5*16*0.5 = 40px of content inside a 200px widget
    grid.center = (2.5 * CELL, 2.5 * CELL)

    # Bottom-right corner of the widget: inside the box, outside every cell.
    automation.click((grid.x + grid.w - 3, grid.y + grid.h - 3))
    check(cell_clicks == [],
          f"a click inside the widget but on no cell must not fire on_cell_click "
          f"(stale stash from the earlier handler-less click); got {cell_clicks}")


def main():
    case_stale_survives_into_dataless_view()
    case_no_handler_click_leaves_no_stash()


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
