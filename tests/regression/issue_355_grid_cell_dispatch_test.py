#!/usr/bin/env python3
"""Regression test for #355: grid cell input dispatch (click + hover).

Before #355, cell input was owned by GridData/UIGrid and PyScene gated it on
derived_type() == UIGRID. But mcrfpy.Grid IS a UIGridView (UIGRIDVIEW), so every
one of those gates was dead: on_cell_click / on_cell_enter / on_cell_exit /
hovered_cell never fired for any user-reachable Grid.

Input now lives on UIGridView (the object that owns the camera), dispatched via
the UIDrawable::dispatchCellClick / updateHover virtuals.

automation.click()/moveTo() reach PyScene::do_mouse_input / do_mouse_hover
synchronously in headless mode, so no mcrfpy.step() is needed for dispatch.

NOT covered (deliberately): entity clicks. UIEntity exposes no on_click/sprite
binding, so entity->sprite.click_callable is unreachable from Python. The entity
branch of UIGridView::click_at is implemented but dead until that binding exists.
"""
import sys
import mcrfpy
from mcrfpy import automation

CELL = 16  # default texture cell size (px)
FAILURES = []


def check(cond, msg):
    if not cond:
        print(f"FAIL: {msg}", file=sys.stderr)
        FAILURES.append(msg)


def cell_tuple(hovered):
    """hovered_cell as a comparable tuple; None stays None (never raises)."""
    return None if hovered is None else tuple(hovered)


def screen_of_cell(grid, cx, cy, zoom=1.0):
    """Screen coords of the center of cell (cx, cy), using the view's own camera
    formula: left_spritepixels = center_x - w/(2*zoom); screen = pos + (gw - lsp)*zoom
    """
    ox, oy = grid.x, grid.y
    w, h = grid.w, grid.h
    left_sp = int(grid.center_x - (w / 2.0 / zoom))
    top_sp = int(grid.center_y - (h / 2.0 / zoom))
    gwx = (cx + 0.5) * CELL
    gwy = (cy + 0.5) * CELL
    return (ox + (gwx - left_sp) * zoom, oy + (gwy - top_sp) * zoom)


def case_a_property_click():
    scene = mcrfpy.Scene("a_click")
    scene.activate()
    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    scene.children.append(grid)
    grid.center_camera((2.5, 2.5))

    events = []
    grid.on_cell_click = lambda pos, button, action: events.append((pos.x, pos.y, button, action))

    for cell in [(0, 0), (2, 3), (4, 4)]:
        events.clear()
        automation.click(screen_of_cell(grid, *cell))
        check(len(events) >= 1, f"[a] on_cell_click did not fire for cell {cell}")
        if not events:
            continue
        cx, cy, button, action = events[0]
        check((cx, cy) == (float(cell[0]), float(cell[1])),
              f"[a] expected cell {cell}, got ({cx},{cy})")
        check(button == mcrfpy.MouseButton.LEFT, f"[a] expected LEFT, got {button}")
        check(action == mcrfpy.InputState.PRESSED, f"[a] expected PRESSED first, got {action}")


def case_b_panned_zoomed():
    scene = mcrfpy.Scene("b_zoom")
    scene.activate()
    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(100, 100), size=(200, 200))
    scene.children.append(grid)
    grid.zoom = 2.0
    grid.center = (7 * CELL, 5 * CELL)  # pan the camera off the default

    events = []
    grid.on_cell_click = lambda pos, button, action: events.append((pos.x, pos.y))

    for cell in [(6, 4), (7, 5), (8, 6)]:
        events.clear()
        automation.click(screen_of_cell(grid, *cell, zoom=2.0))
        check(len(events) >= 1, f"[b] on_cell_click did not fire for panned+zoomed cell {cell}")
        if events:
            check(events[0] == (float(cell[0]), float(cell[1])),
                  f"[b] panned+zoomed: expected cell {cell}, got {events[0]}")


def case_c_hover():
    scene = mcrfpy.Scene("c_hover")
    scene.activate()
    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    scene.children.append(grid)

    entered, exited = [], []
    grid.on_cell_enter = lambda pos: entered.append((pos.x, pos.y))
    grid.on_cell_exit = lambda pos: exited.append((pos.x, pos.y))

    A, B = (1, 1), (3, 2)

    automation.moveTo(screen_of_cell(grid, *A))
    check(entered == [(1.0, 1.0)], f"[c] expected one enter for {A}, got {entered}")
    check(cell_tuple(grid.hovered_cell) == A, f"[c] hovered_cell should be {A}, got {grid.hovered_cell}")

    entered.clear()
    automation.moveTo(screen_of_cell(grid, *B))
    check(exited == [(1.0, 1.0)], f"[c] expected exit for {A}, got {exited}")
    check(entered == [(3.0, 2.0)], f"[c] expected enter for {B}, got {entered}")
    check(cell_tuple(grid.hovered_cell) == B, f"[c] hovered_cell should be {B}, got {grid.hovered_cell}")

    entered.clear()
    exited.clear()
    automation.moveTo((10, 10))  # outside the grid
    check(exited == [(3.0, 2.0)], f"[c] expected exit for {B} on leaving grid, got {exited}")
    check(entered == [], f"[c] no enter expected outside the grid, got {entered}")
    check(grid.hovered_cell is None, f"[c] hovered_cell should be None outside, got {grid.hovered_cell}")


def case_d_subclass():
    calls = []

    class MyGrid(mcrfpy.Grid):
        def on_cell_click(self, pos, button, action):
            calls.append(("click", pos.x, pos.y))

        def on_cell_enter(self, pos):
            calls.append(("enter", pos.x, pos.y))

        def on_cell_exit(self, pos):
            calls.append(("exit", pos.x, pos.y))

    scene = mcrfpy.Scene("d_subclass")
    scene.activate()
    grid = MyGrid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    scene.children.append(grid)

    automation.moveTo(screen_of_cell(grid, 1, 1))
    automation.moveTo(screen_of_cell(grid, 2, 2))
    automation.click(screen_of_cell(grid, 2, 2))

    check(("enter", 1.0, 1.0) in calls, f"[d] subclass on_cell_enter(1,1) did not fire: {calls}")
    check(("exit", 1.0, 1.0) in calls, f"[d] subclass on_cell_exit(1,1) did not fire: {calls}")
    check(("enter", 2.0, 2.0) in calls, f"[d] subclass on_cell_enter(2,2) did not fire: {calls}")
    check(("click", 2.0, 2.0) in calls, f"[d] subclass on_cell_click(2,2) did not fire: {calls}")


def case_e_child_consumes_click():
    scene = mcrfpy.Scene("e_child")
    scene.activate()
    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    scene.children.append(grid)

    cell_clicks, frame_clicks = [], []
    grid.on_cell_click = lambda pos, button, action: cell_clicks.append((pos.x, pos.y))

    # #360: grid children are positioned in GRID-WORLD PIXEL coordinates.
    gx, gy = 3, 1
    frame = mcrfpy.Frame(pos=(gx * CELL, gy * CELL), size=(CELL, CELL))
    frame.on_click = lambda pos, button, action: frame_clicks.append((pos.x, pos.y))
    grid.children.append(frame)

    automation.click(screen_of_cell(grid, gx, gy))
    check(len(frame_clicks) >= 1,
          f"[e] grid child's on_click did not fire (grid-world child coords broken?): {frame_clicks}")
    check(cell_clicks == [],
          f"[e] child consumed the click, so on_cell_click must NOT fire; got {cell_clicks}")

    # And a click on a cell NOT covered by the child still reaches on_cell_click.
    automation.click(screen_of_cell(grid, 0, 4))
    check(cell_clicks and cell_clicks[0] == (0.0, 4.0),
          f"[e] cell outside the child should still fire on_cell_click; got {cell_clicks}")


def case_f_two_views_one_griddata():
    scene = mcrfpy.Scene("f_views")
    scene.activate()
    g = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    scene.children.append(g)

    v2 = mcrfpy.GridView(grid=g.grid_data, pos=(400, 100), size=(200, 200))
    scene.children.append(v2)

    g_events, v_events = [], []
    g.on_cell_enter = lambda pos: g_events.append(("enter", pos.x, pos.y))
    g.on_cell_exit = lambda pos: g_events.append(("exit", pos.x, pos.y))
    v2.on_cell_enter = lambda pos: v_events.append(("enter", pos.x, pos.y))
    v2.on_cell_exit = lambda pos: v_events.append(("exit", pos.x, pos.y))

    # Hover over v2 only.
    automation.moveTo(screen_of_cell(v2, 2, 2))
    check(v_events == [("enter", 2.0, 2.0)], f"[f] v2 should have entered (2,2); got {v_events}")
    check(g_events == [], f"[f] hovering v2 must not fire events on g; got {g_events}")
    check(g.hovered_cell is None, f"[f] g.hovered_cell must stay None; got {g.hovered_cell}")
    check(cell_tuple(v2.hovered_cell) == (2, 2), f"[f] v2.hovered_cell should be (2,2); got {v2.hovered_cell}")

    # Move to g: v2 exits, g enters. No spurious cross-talk.
    v_events.clear()
    g_events.clear()
    automation.moveTo(screen_of_cell(g, 1, 3))
    check(v_events == [("exit", 2.0, 2.0)], f"[f] v2 should have exited (2,2); got {v_events}")
    check(g_events == [("enter", 1.0, 3.0)], f"[f] g should have entered (1,3); got {g_events}")
    check(v2.hovered_cell is None, f"[f] v2.hovered_cell should be None now; got {v2.hovered_cell}")
    check(cell_tuple(g.hovered_cell) == (1, 3), f"[f] g.hovered_cell should be (1,3); got {g.hovered_cell}")

    # Back to v2: each view tracks its own hover, no ping-pong on the other.
    v_events.clear()
    g_events.clear()
    automation.moveTo(screen_of_cell(v2, 2, 2))
    check(v_events == [("enter", 2.0, 2.0)], f"[f] v2 re-enter (2,2) expected; got {v_events}")
    check(g_events == [("exit", 1.0, 3.0)], f"[f] g exit (1,3) expected; got {g_events}")


def case_g_child_hover():
    """Hover must reach grid children, exactly as click already does.

    do_mouse_hover used to recurse only into UIFRAME children, so a drawable in
    grid.children could receive on_click but never on_enter/on_exit/on_move, and
    its .hovered flag was stuck False -- callbacks that exist on the API surface
    but can never fire. The hover walk now descends through the view's camera
    (grid-world pixel coords), the same transform click_at uses.
    """
    scene = mcrfpy.Scene("g_child_hover")
    scene.activate()
    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    scene.children.append(grid)

    entered, exited, moved = [], [], []
    gx, gy = 3, 1
    frame = mcrfpy.Frame(pos=(gx * CELL, gy * CELL), size=(CELL, CELL))  # grid-world coords
    frame.on_enter = lambda pos: entered.append((pos.x, pos.y))
    frame.on_exit = lambda pos: exited.append((pos.x, pos.y))
    frame.on_move = lambda pos: moved.append((pos.x, pos.y))
    grid.children.append(frame)

    # Mouse onto the cell the child covers.
    automation.moveTo(screen_of_cell(grid, gx, gy))
    check(len(entered) == 1, f"[g] grid child's on_enter did not fire: {entered}")
    check(frame.hovered is True, f"[g] grid child's .hovered should be True, got {frame.hovered}")
    check(len(moved) == 1, f"[g] grid child's on_move did not fire while inside: {moved}")

    # Mouse to a different cell inside the grid but outside the child.
    automation.moveTo(screen_of_cell(grid, 0, 4))
    check(len(exited) == 1, f"[g] grid child's on_exit did not fire on leaving it: {exited}")
    check(frame.hovered is False, f"[g] grid child's .hovered should be False, got {frame.hovered}")

    # Re-enter, then leave the grid widget entirely: the child must still exit,
    # and must NOT be re-entered by a point outside the view that happens to map
    # into grid-world space over the child.
    entered.clear()
    exited.clear()
    automation.moveTo(screen_of_cell(grid, gx, gy))
    check(len(entered) == 1, f"[g] grid child re-enter expected, got {entered}")
    automation.moveTo((10, 10))  # far outside the grid widget
    check(len(exited) == 1, f"[g] leaving the grid must exit the hovered child: {exited}")
    check(frame.hovered is False, "[g] child still hovered after mouse left the grid")

    # Panning the camera moves the child under a DIFFERENT screen pixel; hover
    # must follow the camera (the whole point of routing through localToGridWorld).
    entered.clear()
    grid.zoom = 2.0
    grid.center = (gx * CELL, gy * CELL)  # child centered in the widget
    automation.moveTo((int(grid.x + grid.w / 2), int(grid.y + grid.h / 2)))
    check(len(entered) == 1,
          f"[g] after pan+zoom, hover did not track the child through the camera: {entered}")
    check(frame.hovered is True, "[g] child not hovered at its new on-screen position")


def main():
    case_a_property_click()
    case_b_panned_zoomed()
    case_c_hover()
    case_d_subclass()
    case_e_child_consumes_click()
    case_f_two_views_one_griddata()
    case_g_child_hover()

    if FAILURES:
        print(f"\n{len(FAILURES)} FAILURE(S)", file=sys.stderr)
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    # --exec does NOT turn an unhandled exception into a non-zero exit code, so a
    # crashing test would otherwise report success. Translate explicitly.
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"\nTEST CRASHED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
