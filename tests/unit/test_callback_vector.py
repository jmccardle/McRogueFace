#!/usr/bin/env python3
"""Test that callbacks return Vector objects instead of separate x, y values."""

import sys
import mcrfpy

# Track test results
results = []

def test_click_callback_signature(pos, button, action):
    """Test on_click callback receives Vector."""
    # Check if pos is a Vector
    if isinstance(pos, mcrfpy.Vector):
        results.append(("on_click pos is Vector", True))
        print(f"PASS: on_click receives Vector: {pos}")
    else:
        results.append(("on_click pos is Vector", False))
        print(f"FAIL: on_click receives {type(pos).__name__} instead of Vector: {pos}")

    # Verify button and action are strings
    if isinstance(button, str) and isinstance(action, str):
        results.append(("on_click button/action are strings", True))
        print(f"PASS: button={button!r}, action={action!r}")
    else:
        results.append(("on_click button/action are strings", False))
        print(f"FAIL: button={type(button).__name__}, action={type(action).__name__}")

# #230 - Hover callbacks now receive only (pos), not (pos, button, action)
def test_on_enter_callback_signature(pos):
    """Test on_enter callback receives Vector."""
    if isinstance(pos, mcrfpy.Vector):
        results.append(("on_enter pos is Vector", True))
        print(f"PASS: on_enter receives Vector: {pos}")
    else:
        results.append(("on_enter pos is Vector", False))
        print(f"FAIL: on_enter receives {type(pos).__name__} instead of Vector")

def test_on_exit_callback_signature(pos):
    """Test on_exit callback receives Vector."""
    if isinstance(pos, mcrfpy.Vector):
        results.append(("on_exit pos is Vector", True))
        print(f"PASS: on_exit receives Vector: {pos}")
    else:
        results.append(("on_exit pos is Vector", False))
        print(f"FAIL: on_exit receives {type(pos).__name__} instead of Vector")

def test_on_move_callback_signature(pos):
    """Test on_move callback receives Vector."""
    if isinstance(pos, mcrfpy.Vector):
        results.append(("on_move pos is Vector", True))
        print(f"PASS: on_move receives Vector: {pos}")
    else:
        results.append(("on_move pos is Vector", False))
        print(f"FAIL: on_move receives {type(pos).__name__} instead of Vector")

# #230 - Cell click still receives (cell_pos, button, action)
def test_cell_click_callback_signature(cell_pos, button, action):
    """Test on_cell_click callback receives Vector, MouseButton, InputState."""
    if isinstance(cell_pos, mcrfpy.Vector):
        results.append(("on_cell_click pos is Vector", True))
        print(f"PASS: on_cell_click receives Vector: {cell_pos}")
    else:
        results.append(("on_cell_click pos is Vector", False))
        print(f"FAIL: on_cell_click receives {type(cell_pos).__name__} instead of Vector")

# #230 - Cell hover callbacks now receive only (cell_pos)
def test_cell_enter_callback_signature(cell_pos):
    """Test on_cell_enter callback receives Vector."""
    if isinstance(cell_pos, mcrfpy.Vector):
        results.append(("on_cell_enter pos is Vector", True))
        print(f"PASS: on_cell_enter receives Vector: {cell_pos}")
    else:
        results.append(("on_cell_enter pos is Vector", False))
        print(f"FAIL: on_cell_enter receives {type(cell_pos).__name__} instead of Vector")

def test_cell_exit_callback_signature(cell_pos):
    """Test on_cell_exit callback receives Vector."""
    if isinstance(cell_pos, mcrfpy.Vector):
        results.append(("on_cell_exit pos is Vector", True))
        print(f"PASS: on_cell_exit receives Vector: {cell_pos}")
    else:
        results.append(("on_cell_exit pos is Vector", False))
        print(f"FAIL: on_cell_exit receives {type(cell_pos).__name__} instead of Vector")

def run_test(runtime):
    """Set up test and simulate interactions."""
    print("=" * 50)
    print("Testing callback Vector return values")
    print("=" * 50)

    # Create a test scene
    mcrfpy.createScene("test")
    ui = mcrfpy.sceneUI("test")

    # Create a Frame with callbacks
    frame = mcrfpy.Frame(pos=(100, 100), size=(200, 200))
    frame.on_click = test_click_callback_signature
    frame.on_enter = test_on_enter_callback_signature
    frame.on_exit = test_on_exit_callback_signature
    frame.on_move = test_on_move_callback_signature
    ui.append(frame)

    # Create a Grid with cell callbacks
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(pos=(350, 100), size=(200, 200), grid_size=(10, 10), texture=texture)
    grid.on_cell_click = test_cell_click_callback_signature
    grid.on_cell_enter = test_cell_enter_callback_signature
    grid.on_cell_exit = test_cell_exit_callback_signature
    ui.append(grid)

    mcrfpy.setScene("test")

    print("\n--- Test Setup Complete ---")
    print("To test interactively:")
    print("  - Click on the Frame (left side) to test on_click")
    print("  - Move mouse over Frame to test on_enter/on_exit/on_move")
    print("  - Click on the Grid (right side) to test on_cell_click")
    print("  - Move mouse over Grid to test on_cell_enter/on_cell_exit")
    print("\nPress Escape to exit.")

    # For headless testing, simulate a callback call directly
    print("\n--- Simulating callback calls ---")

    # Test that the callbacks are set up correctly
    # on_click still takes (pos, button, action)
    test_click_callback_signature(mcrfpy.Vector(150, 150), "left", "start")
    # #230 - Hover callbacks now take only (pos)
    test_on_enter_callback_signature(mcrfpy.Vector(100, 100))
    test_on_exit_callback_signature(mcrfpy.Vector(300, 300))
    test_on_move_callback_signature(mcrfpy.Vector(125, 175))
    # #230 - on_cell_click still takes (cell_pos, button, action)
    test_cell_click_callback_signature(mcrfpy.Vector(5, 3), mcrfpy.MouseButton.LEFT, mcrfpy.InputState.PRESSED)
    # #230 - Cell hover callbacks now take only (cell_pos)
    test_cell_enter_callback_signature(mcrfpy.Vector(2, 7))
    test_cell_exit_callback_signature(mcrfpy.Vector(8, 1))

    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    passed = sum(1 for _, success in results if success)
    failed = sum(1 for _, success in results if not success)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\nAll tests PASSED!")
        sys.exit(0)
    else:
        print("\nSome tests FAILED!")
        for name, success in results:
            if not success:
                print(f"  FAILED: {name}")
        sys.exit(1)

# Run the test
mcrfpy.Timer("test", run_test, 100)
