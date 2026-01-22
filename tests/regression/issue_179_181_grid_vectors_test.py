#!/usr/bin/env python3
"""Test for issues #179 and #181: Grid attributes return Vectors and grid_x/grid_y renamed to grid_w/grid_h"""

import mcrfpy
import sys

def test_grid_vectors():
    """Test that Grid attributes return Vector objects instead of tuples."""
    print("Testing issue #179: Grid attributes should return Vectors...")

    # Create a Grid for testing
    grid = mcrfpy.Grid(pos=(100, 150), size=(400, 300), grid_size=(20, 15))

    # Test grid.size returns a Vector
    size = grid.size
    print(f"  grid.size = {size}")
    assert hasattr(size, 'x'), f"grid.size should have .x attribute, got {type(size)}"
    assert hasattr(size, 'y'), f"grid.size should have .y attribute, got {type(size)}"
    assert size.x == 400.0, f"grid.size.x should be 400.0, got {size.x}"
    assert size.y == 300.0, f"grid.size.y should be 300.0, got {size.y}"
    print("  PASS: grid.size returns Vector")

    # Test grid.grid_size returns a Vector
    grid_size = grid.grid_size
    print(f"  grid.grid_size = {grid_size}")
    assert hasattr(grid_size, 'x'), f"grid.grid_size should have .x attribute, got {type(grid_size)}"
    assert hasattr(grid_size, 'y'), f"grid.grid_size should have .y attribute, got {type(grid_size)}"
    assert grid_size.x == 20.0, f"grid.grid_size.x should be 20.0, got {grid_size.x}"
    assert grid_size.y == 15.0, f"grid.grid_size.y should be 15.0, got {grid_size.y}"
    print("  PASS: grid.grid_size returns Vector")

    # Test grid.center returns a Vector
    grid.center = (50.0, 75.0)  # Set center first
    center = grid.center
    print(f"  grid.center = {center}")
    assert hasattr(center, 'x'), f"grid.center should have .x attribute, got {type(center)}"
    assert hasattr(center, 'y'), f"grid.center should have .y attribute, got {type(center)}"
    assert center.x == 50.0, f"grid.center.x should be 50.0, got {center.x}"
    assert center.y == 75.0, f"grid.center.y should be 75.0, got {center.y}"
    print("  PASS: grid.center returns Vector")

    # Test grid.position returns a Vector
    position = grid.position
    print(f"  grid.position = {position}")
    assert hasattr(position, 'x'), f"grid.position should have .x attribute, got {type(position)}"
    assert hasattr(position, 'y'), f"grid.position should have .y attribute, got {type(position)}"
    assert position.x == 100.0, f"grid.position.x should be 100.0, got {position.x}"
    assert position.y == 150.0, f"grid.position.y should be 150.0, got {position.y}"
    print("  PASS: grid.position returns Vector")

    print("Issue #179 tests PASSED!")


def test_grid_w_h():
    """Test that grid_w and grid_h exist and grid_x/grid_y do not."""
    print("\nTesting issue #181: grid_x/grid_y renamed to grid_w/grid_h...")

    grid = mcrfpy.Grid(grid_size=(25, 18))

    # Test grid_w and grid_h exist and return correct values
    grid_w = grid.grid_w
    grid_h = grid.grid_h
    print(f"  grid.grid_w = {grid_w}")
    print(f"  grid.grid_h = {grid_h}")
    assert grid_w == 25, f"grid.grid_w should be 25, got {grid_w}"
    assert grid_h == 18, f"grid.grid_h should be 18, got {grid_h}"
    print("  PASS: grid.grid_w and grid.grid_h exist and return correct values")

    # Test grid_x and grid_y do NOT exist (AttributeError expected)
    try:
        _ = grid.grid_x
        print("  FAIL: grid.grid_x should not exist but it does!")
        sys.exit(1)
    except AttributeError:
        print("  PASS: grid.grid_x correctly raises AttributeError")

    try:
        _ = grid.grid_y
        print("  FAIL: grid.grid_y should not exist but it does!")
        sys.exit(1)
    except AttributeError:
        print("  PASS: grid.grid_y correctly raises AttributeError")

    print("Issue #181 tests PASSED!")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Grid Vector attributes and grid_w/grid_h rename")
    print("=" * 60)

    try:
        test_grid_vectors()
        test_grid_w_h()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        sys.exit(0)

    except AssertionError as e:
        print(f"\nFAIL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
