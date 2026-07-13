#!/usr/bin/env python3
"""Regression test for #367: losing window focus stranded hover state (#363's sibling).

#363 fixed the case where the cursor physically LEAVES the window. But alt-tabbing
away strands hover in exactly the same way and for exactly the same reason: while the
window is unfocused no MouseMoved arrives, so the hover walk never runs, so whatever
was hovered when focus was lost stays hovered. on_exit / on_cell_exit never fire and
grid.hovered_cell keeps reporting a cell the user is no longer pointing at -- while
the game sits in the background.

sf::Event::LostFocus was already being produced by every backend (SDL2Renderer even
translates SDL_WINDOWEVENT_FOCUS_LOST into it) and, like MouseLeft before #363, had
NOBODY LISTENING.

The fix routes LostFocus to the same PyScene::do_mouse_leave() that #363 added. That
is the honest response: once unfocused, the engine genuinely does not know where the
pointer is, and "hovering nothing" is the only truthful state. Hover is restored by
the next MouseMoved after focus returns.

automation.loseFocus() injects the event.
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


def case_grid_cell_exit_fires_on_focus_loss():
    scene = mcrfpy.Scene("blur_grid")
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

    # The player alt-tabs away. The cursor may still be physically over the window,
    # but no further MouseMoved will be delivered to us.
    automation.loseFocus()

    check(exits == [(2, 2)],
          f"losing focus must fire on_cell_exit for the hovered cell; got {exits}")
    check(grid.hovered_cell is None,
          f"hovered_cell must be None while the window is unfocused; got {grid.hovered_cell}")
    check(enters == [(2, 2)],
          f"losing focus must not fire any on_cell_enter; got {enters}")


def case_frame_on_exit_fires_on_focus_loss():
    """Like #363, this is an input-layer gap, not a grid one: Frame.on_exit too."""
    scene = mcrfpy.Scene("blur_frame")
    scene.activate()
    frame = mcrfpy.Frame(pos=(50, 50), size=(100, 100))
    scene.children.append(frame)

    entered, exited = [], []
    frame.on_enter = lambda pos: entered.append((pos.x, pos.y))
    frame.on_exit = lambda pos: exited.append((pos.x, pos.y))

    automation.moveTo((100, 100))
    check(len(entered) == 1, f"moving into the frame should fire on_enter; got {entered}")
    check(exited == [], f"nothing should have exited yet; got {exited}")

    automation.loseFocus()
    check(len(exited) == 1, f"losing focus must fire the frame's on_exit; got {exited}")

    # Already unfocused: a second blur has nothing left to exit.
    automation.loseFocus()
    check(len(exited) == 1, f"a redundant focus loss must not fire on_exit twice; got {exited}")


def case_reenter_after_focus_loss():
    """Hover must be genuinely cleared, not merely reported clear.

    Re-entering the SAME cell after focus returns has to fire on_cell_enter again. If
    loseFocus had only nulled the reported value while leaving the internal hovered
    cell set, the incoming cell would compare equal and the enter would be swallowed.
    """
    scene = mcrfpy.Scene("blur_reenter")
    scene.activate()
    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    scene.children.append(grid)

    enters = []
    grid.on_cell_enter = lambda pos: enters.append((pos.x, pos.y))

    target = screen_of_cell(grid, 3, 3)
    automation.moveTo(target)
    automation.loseFocus()

    automation.moveTo(target)
    check(enters == [(3, 3), (3, 3)],
          f"pointing at the same cell after focus returns must fire on_cell_enter again; "
          f"got {enters}")


def main():
    case_grid_cell_exit_fires_on_focus_loss()
    case_frame_on_exit_fires_on_focus_loss()
    case_reenter_after_focus_loss()


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
