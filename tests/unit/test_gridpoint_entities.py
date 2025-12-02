#!/usr/bin/env python3
"""
Test GridPoint.entities property (#114)
========================================

Tests the GridPoint.entities property that returns a list of entities
at that grid cell position.
"""

import mcrfpy
import sys

def run_tests():
    """Run GridPoint.entities tests"""
    print("=== GridPoint.entities Tests ===\n")

    # Test 1: Basic entity listing
    print("Test 1: Basic entity listing")
    grid = mcrfpy.Grid(pos=(0, 0), size=(640, 400), grid_size=(40, 25))

    # Add entities at various positions
    e1 = mcrfpy.Entity((5, 5))
    e2 = mcrfpy.Entity((5, 5))  # Same position as e1
    e3 = mcrfpy.Entity((10, 10))
    grid.entities.append(e1)
    grid.entities.append(e2)
    grid.entities.append(e3)

    # Check entities at (5, 5)
    pt = grid.at(5, 5)
    entities_at_5_5 = pt.entities
    assert len(entities_at_5_5) == 2, f"Expected 2 entities at (5,5), got {len(entities_at_5_5)}"
    print(f"  Found {len(entities_at_5_5)} entities at (5, 5)")

    # Check entities at (10, 10)
    pt2 = grid.at(10, 10)
    entities_at_10_10 = pt2.entities
    assert len(entities_at_10_10) == 1, f"Expected 1 entity at (10,10), got {len(entities_at_10_10)}"
    print(f"  Found {len(entities_at_10_10)} entity at (10, 10)")

    # Check empty cell
    pt3 = grid.at(0, 0)
    entities_at_0_0 = pt3.entities
    assert len(entities_at_0_0) == 0, f"Expected 0 entities at (0,0), got {len(entities_at_0_0)}"
    print(f"  Found {len(entities_at_0_0)} entities at (0, 0)")
    print()

    # Test 2: Entity references are valid
    print("Test 2: Entity references are valid")
    for e in pt.entities:
        assert e.x == 5.0, f"Entity x should be 5.0, got {e.x}"
        assert e.y == 5.0, f"Entity y should be 5.0, got {e.y}"
    print("  All entity references have correct positions")
    print()

    # Test 3: Entity movement updates listing
    print("Test 3: Entity movement updates listing")
    e1.x = 20
    e1.y = 20

    # Old position should have one fewer entity
    entities_at_5_5_after = grid.at(5, 5).entities
    assert len(entities_at_5_5_after) == 1, f"Expected 1 entity at (5,5) after move, got {len(entities_at_5_5_after)}"
    print(f"  After moving e1: {len(entities_at_5_5_after)} entity at (5, 5)")

    # New position should have the moved entity
    entities_at_20_20 = grid.at(20, 20).entities
    assert len(entities_at_20_20) == 1, f"Expected 1 entity at (20,20), got {len(entities_at_20_20)}"
    print(f"  After moving e1: {len(entities_at_20_20)} entity at (20, 20)")
    print()

    # Test 4: Multiple grids are independent
    print("Test 4: Multiple grids are independent")
    grid2 = mcrfpy.Grid(pos=(0, 0), size=(640, 400), grid_size=(40, 25))
    e4 = mcrfpy.Entity((5, 5))
    grid2.entities.append(e4)

    # Original grid should not see grid2's entity
    assert len(grid.at(5, 5).entities) == 1, "Original grid should still have 1 entity at (5,5)"
    assert len(grid2.at(5, 5).entities) == 1, "Second grid should have 1 entity at (5,5)"
    print("  Grids maintain independent entity lists")
    print()

    print("=== All GridPoint.entities Tests Passed! ===")
    return True

# Main execution
if __name__ == "__main__":
    try:
        if run_tests():
            print("\nPASS")
            sys.exit(0)
        else:
            print("\nFAIL")
            sys.exit(1)
    except Exception as e:
        print(f"\nFAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
