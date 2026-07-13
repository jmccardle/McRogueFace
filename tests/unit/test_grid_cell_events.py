#!/usr/bin/env python3
"""Test #142: Grid Cell Mouse Events

#355 follow-up: this file used to treat "zero events fired" as a soft
"PARTIAL" print and still exit(0). That masked the #355 regression (grid
cell click/hover dispatch is entirely dead for mcrfpy.Grid, which is a
UIGridView under the hood) as a passing test suite. Every path below now
hard-asserts; a callback that fails to fire is a test failure, not a
"maybe interactive mode" shrug.

Coordinate math: with an unmodified (default) camera and an explicit
`size=`, UIGridView's default center is exactly size/(2*zoom), which
equals the viewport's own half-width/half-height. That makes grid_space
== local screen-relative position when zoom==1 (the two halves cancel),
so cell = floor(local_offset / cell_pixel_size) with the default 16x16
texture. All screen coordinates below are chosen with that arithmetic,
landing deliberately mid-cell (not on a boundary) to avoid float-edge
ambiguity.
"""
import sys
import mcrfpy
from mcrfpy import automation


def test_properties():
    """Test grid cell event properties exist and work"""
    print("Testing grid cell event properties...")

    test_props = mcrfpy.Scene("test_props")
    ui = test_props.children
    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    ui.append(grid)

    # #230 - cell enter/exit receive (cell_pos: Vector)
    def cell_handler(pos):
        pass

    # Test on_cell_enter
    grid.on_cell_enter = cell_handler
    assert grid.on_cell_enter == cell_handler
    grid.on_cell_enter = None
    assert grid.on_cell_enter is None

    # Test on_cell_exit
    grid.on_cell_exit = cell_handler
    assert grid.on_cell_exit == cell_handler
    grid.on_cell_exit = None
    assert grid.on_cell_exit is None

    # #230 - cell click receives (cell_pos: Vector, button: MouseButton, action: InputState)
    def click_handler(pos, button, action):
        pass

    # Test on_cell_click
    grid.on_cell_click = click_handler
    assert grid.on_cell_click == click_handler
    grid.on_cell_click = None
    assert grid.on_cell_click is None

    # Test hovered_cell
    assert grid.hovered_cell is None

    print("  - Properties: PASS")


def test_cell_hover():
    """Test cell hover events fire with the correct cells, across a boundary."""
    print("Testing cell hover events...")

    test_hover = mcrfpy.Scene("test_hover")
    ui = test_hover.children
    test_hover.activate()

    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    ui.append(grid)

    enter_events = []
    exit_events = []

    # #230 - cell enter/exit receive (cell_pos: Vector)
    def on_enter(pos):
        enter_events.append((pos.x, pos.y))

    def on_exit(pos):
        exit_events.append((pos.x, pos.y))

    grid.on_cell_enter = on_enter
    grid.on_cell_exit = on_exit

    # local=(40,40) -> cell (2,2); local=(56,40) -> cell (3,2) (adjacent, same row)
    automation.moveTo((140, 140))
    mcrfpy.step(0.05)
    automation.moveTo((156, 140))
    mcrfpy.step(0.05)

    print(f"  Enter events: {enter_events}, Exit events: {exit_events}")
    print(f"  Hovered cell: {grid.hovered_cell}")

    assert (2, 2) in enter_events, \
        f"expected on_cell_enter to fire for cell (2,2); got {enter_events}"
    assert (3, 2) in enter_events, \
        f"expected on_cell_enter to fire for cell (3,2) after crossing the boundary; got {enter_events}"
    assert (2, 2) in exit_events, \
        f"expected on_cell_exit to fire for cell (2,2) when leaving it; got {exit_events}"
    assert grid.hovered_cell is not None, "grid.hovered_cell should be set after hovering"
    # hovered_cell is an (x, y) tuple (see its docstring / api_surface golden).
    assert tuple(grid.hovered_cell) == (3, 2), \
        f"expected grid.hovered_cell == (3,2), got {grid.hovered_cell}"

    print("  - Hover: PASS")


def test_cell_click():
    """Test cell click events fire with the correct cell."""
    print("Testing cell click events...")

    test_click = mcrfpy.Scene("test_click")
    ui = test_click.children
    test_click.activate()

    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    ui.append(grid)

    click_events = []

    # #230 - cell click receives (cell_pos: Vector, button: MouseButton, action: InputState)
    def on_click(pos, button, action):
        click_events.append((pos.x, pos.y, button, action))

    grid.on_cell_click = on_click

    # local=(36,52) -> cell (2,3)
    automation.click((136, 152))
    mcrfpy.step(0.05)

    print(f"  Click events: {click_events}")

    assert len(click_events) >= 1, \
        "expected on_cell_click to fire at least once for a click inside the grid"
    cx, cy, button, action = click_events[0]
    assert (cx, cy) == (2, 3), f"expected cell (2,3), got ({cx},{cy})"
    assert button == mcrfpy.MouseButton.LEFT, f"expected LEFT button, got {button}"

    print("  - Click: PASS")


if __name__ == "__main__":
    try:
        test_properties()
        test_cell_hover()
        test_cell_click()

        print("\n=== All grid cell event tests passed! ===")
        sys.exit(0)
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
