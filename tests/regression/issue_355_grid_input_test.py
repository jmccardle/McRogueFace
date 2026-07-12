#!/usr/bin/env python3
"""Regression test for #355 - mcrfpy.Grid input is entirely dead.

Since the #252 Grid/GridView split, mcrfpy.Grid(...) constructs a
UIGridView (PyObjectsEnum::UIGRIDVIEW). Every input dispatch site that
matters for grid cell/child/entity interactivity (PyScene::do_mouse_input,
PyScene::do_mouse_hover's processHover, and the subclass-method lookup in
UIGrid::fireCellClick) still gates on derived_type() == UIGRID -- the
*internal* _GridData type nothing user-visible is ever an instance of. As a
result:
  - on_cell_click / on_cell_enter / on_cell_exit never fire on a real Grid.
  - Child drawables appended to grid.children never receive their own
    on_click.
  - A Python subclass of mcrfpy.Grid that overrides on_cell_click as a
    *method* (rather than assigning the on_cell_click property) is doubly
    broken: is_python_subclass/serial_number tracking for that lookup is
    keyed off the internal _GridData wrapper, not the public Grid/GridView
    instance a subclass is actually built from.

Each check below is a hard assertion (sys.exit via unhandled AssertionError
on failure) -- no "PARTIAL" outs.

Coordinate math: with an unmodified camera and an explicit `size=`,
UIGridView's default center is size/(2*zoom) == the viewport's own
half-width/half-height, which cancels the half-width term in the
screen->cell formula, so grid_space == local screen-relative offset
whenever zoom==1. cell = floor(grid_space / cell_pixel_size), with the
16x16 default texture. Case (b) explicitly overrides grid.center/grid.zoom
to non-default values and uses the full formula
(grid_space = (local - half_width) / zoom + center_x) so it is a genuine
discriminator against a fix that reads the wrong (stale, internal
_GridData-owned) camera copy instead of the public Grid/GridView's own
center_x/center_y/zoom.
"""
import sys
import mcrfpy
from mcrfpy import automation


def test_a_plain_cell_click():
    """(a) on_cell_click fires with the correct cell for a click on a plain Grid."""
    print("(a) plain grid cell click...")
    scene = mcrfpy.Scene("issue355_a")
    ui = scene.children
    mcrfpy.current_scene = scene

    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    ui.append(grid)

    clicks = []
    def on_cell_click(cell_pos, button, action):
        clicks.append((cell_pos.x, cell_pos.y, button, action))
    grid.on_cell_click = on_cell_click

    # local=(36,52) -> cell (2,3), see module docstring for the math.
    automation.click((136, 152))
    mcrfpy.step(0.05)

    assert len(clicks) >= 1, f"on_cell_click never fired; clicks={clicks}"
    cx, cy, button, action = clicks[0]
    assert (cx, cy) == (2, 3), f"expected cell (2,3), got ({cx},{cy})"
    assert button == mcrfpy.MouseButton.LEFT
    assert action == mcrfpy.InputState.PRESSED
    print("    OK")


def test_b_panned_zoomed_cell_click():
    """(b) on_cell_click reports the CORRECT cell after grid.center/grid.zoom
    are set to non-default values -- discriminates against a fix that reads
    a stale internal camera copy instead of the public Grid's own."""
    print("(b) panned+zoomed grid cell click...")
    scene = mcrfpy.Scene("issue355_b")
    ui = scene.children
    mcrfpy.current_scene = scene

    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(50, 50), size=(200, 200))
    ui.append(grid)

    grid.zoom = 2.0
    grid.center = (88, 88)  # pixel-space camera center (== tile (5.5,5.5) at 16px cells)
    assert grid.zoom == 2.0
    assert (grid.center.x, grid.center.y) == (88, 88), \
        f"grid.center did not take the assigned value: {grid.center}"

    clicks = []
    def on_cell_click(cell_pos, button, action):
        clicks.append((cell_pos.x, cell_pos.y))
    grid.on_cell_click = on_cell_click

    # local=(60,60); grid_space = (60-100)/2.0 + 88 = 68; cell = floor(68/16) = 4
    automation.click((110, 110))
    mcrfpy.step(0.05)

    assert len(clicks) >= 1, f"on_cell_click never fired under pan/zoom; clicks={clicks}"
    assert clicks[0] == (4, 4), (
        f"expected cell (4,4) under grid.center=(88,88)/grid.zoom=2.0, got {clicks[0]} "
        "(a stale-camera fix would report (3,3) instead)"
    )
    print("    OK")


def test_c_hover_boundary():
    """(c) on_cell_enter / on_cell_exit fire on hover across a cell boundary."""
    print("(c) cell hover enter/exit across a boundary...")
    scene = mcrfpy.Scene("issue355_c")
    ui = scene.children
    mcrfpy.current_scene = scene

    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    ui.append(grid)

    enters = []
    exits = []
    grid.on_cell_enter = lambda pos: enters.append((pos.x, pos.y))
    grid.on_cell_exit = lambda pos: exits.append((pos.x, pos.y))

    # local=(40,40) -> cell (2,2); local=(56,40) -> cell (3,2)
    automation.moveTo((140, 140))
    mcrfpy.step(0.05)
    automation.moveTo((156, 140))
    mcrfpy.step(0.05)

    assert (2, 2) in enters, f"on_cell_enter never fired for (2,2); enters={enters}"
    assert (2, 2) in exits, f"on_cell_exit never fired for (2,2); exits={exits}"
    assert (3, 2) in enters, f"on_cell_enter never fired for (3,2); enters={enters}"
    print("    OK")


def test_d_child_drawable_click():
    """(d) A Frame child of grid.children receives its own on_click when
    clicked, at the screen pixel derived from the grid's camera transform
    (children live in grid-world pixel coordinates, not screen pixels)."""
    print("(d) child drawable click (grid-world pixel coords via camera)...")
    scene = mcrfpy.Scene("issue355_d")
    ui = scene.children
    mcrfpy.current_scene = scene

    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(50, 50), size=(200, 200))
    ui.append(grid)

    # Grid-world pixel box [90,110]x[90,110]. Default camera (center=(100,100),
    # zoom=1) makes grid_space == local, so:
    #   screen (150,150) -> local (100,100) -> world (100,100): INSIDE the frame
    #   screen (120,120) -> local (70,70)   -> world (70,70):   OUTSIDE the frame
    frame = mcrfpy.Frame(pos=(90, 90), size=(20, 20))
    grid.children.append(frame)

    frame_clicks = []
    def on_frame_click(pos, button, action):
        frame_clicks.append((pos.x, pos.y))
    frame.on_click = on_frame_click

    # Miss first: proves the screen point isn't just always hitting the frame.
    automation.click((120, 120))
    mcrfpy.step(0.05)
    assert len(frame_clicks) == 0, (
        f"frame.on_click fired for a screen point outside its grid-world bounds: {frame_clicks}"
    )

    automation.click((150, 150))
    mcrfpy.step(0.05)
    assert len(frame_clicks) >= 1, (
        "frame.on_click never fired for a click on a Frame in grid.children "
        "at the correctly camera-transformed screen pixel"
    )
    print("    OK")


def test_e_subclass_method_override():
    """(e) A Python subclass of mcrfpy.Grid overriding on_cell_click as a
    METHOD (not the property) has that method invoked."""
    print("(e) Grid subclass on_cell_click method override...")

    class ClickCountingGrid(mcrfpy.Grid):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.clicked_cells = []

        def on_cell_click(self, cell_pos, button, action):
            self.clicked_cells.append((cell_pos.x, cell_pos.y))

    scene = mcrfpy.Scene("issue355_e")
    ui = scene.children
    mcrfpy.current_scene = scene

    mg = ClickCountingGrid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    ui.append(mg)

    # local=(36,52) -> cell (2,3), same math as (a).
    automation.click((136, 152))
    mcrfpy.step(0.05)

    assert len(mg.clicked_cells) >= 1, (
        "ClickCountingGrid.on_cell_click (method override) never fired"
    )
    assert mg.clicked_cells[0] == (2, 3), \
        f"expected cell (2,3), got {mg.clicked_cells[0]}"
    print("    OK")


def main():
    test_a_plain_cell_click()
    test_b_panned_zoomed_cell_click()
    test_c_hover_boundary()
    test_d_child_drawable_click()
    test_e_subclass_method_override()
    print("PASS")


if __name__ == "__main__":
    # NOTE: --exec does not turn an unhandled Python exception into a
    # non-zero process exit code (verified empirically), so failures MUST
    # be caught and translated to sys.exit(1) explicitly here -- letting a
    # bare AssertionError propagate would silently "pass" the suite, which
    # is exactly the masking anti-pattern #355 shipped behind.
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
