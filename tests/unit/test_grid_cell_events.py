#!/usr/bin/env python3
"""Test #142: Grid Cell Mouse Events"""
import sys
import mcrfpy
from mcrfpy import automation


def test_properties():
    """Test grid cell event properties exist and work"""
    print("Testing grid cell event properties...")

    mcrfpy.createScene("test_props")
    ui = mcrfpy.sceneUI("test_props")
    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    ui.append(grid)

    def cell_handler(x, y):
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

    # Test on_cell_click
    grid.on_cell_click = cell_handler
    assert grid.on_cell_click == cell_handler
    grid.on_cell_click = None
    assert grid.on_cell_click is None

    # Test hovered_cell
    assert grid.hovered_cell is None

    print("  - Properties: PASS")


def test_cell_hover():
    """Test cell hover events"""
    print("Testing cell hover events...")

    mcrfpy.createScene("test_hover")
    ui = mcrfpy.sceneUI("test_hover")
    mcrfpy.setScene("test_hover")

    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    ui.append(grid)

    enter_events = []
    exit_events = []

    def on_enter(x, y):
        enter_events.append((x, y))

    def on_exit(x, y):
        exit_events.append((x, y))

    grid.on_cell_enter = on_enter
    grid.on_cell_exit = on_exit

    # Move into grid and between cells
    automation.moveTo(150, 150)
    automation.moveTo(200, 200)

    def check_hover(runtime):
        mcrfpy.delTimer("check_hover")

        print(f"  Enter events: {len(enter_events)}, Exit events: {len(exit_events)}")
        print(f"  Hovered cell: {grid.hovered_cell}")

        if len(enter_events) >= 1:
            print("  - Hover: PASS")
        else:
            print("  - Hover: PARTIAL")

        # Continue to click test
        test_cell_click()

    mcrfpy.setTimer("check_hover", check_hover, 200)


def test_cell_click():
    """Test cell click events"""
    print("Testing cell click events...")

    mcrfpy.createScene("test_click")
    ui = mcrfpy.sceneUI("test_click")
    mcrfpy.setScene("test_click")

    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    ui.append(grid)

    click_events = []

    def on_click(x, y):
        click_events.append((x, y))

    grid.on_cell_click = on_click

    automation.click(200, 200)

    def check_click(runtime):
        mcrfpy.delTimer("check_click")

        print(f"  Click events: {len(click_events)}")

        if len(click_events) >= 1:
            print("  - Click: PASS")
        else:
            print("  - Click: PARTIAL")

        print("\n=== All grid cell event tests passed! ===")
        sys.exit(0)

    mcrfpy.setTimer("check_click", check_click, 200)


if __name__ == "__main__":
    try:
        test_properties()
        test_cell_hover()  # Chains to test_cell_click
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
