#!/usr/bin/env python3
"""Unit tests for Grid.apply_threshold and Grid.apply_ranges (#199)

Tests the Grid methods for applying HeightMap data to walkable/transparent properties.
"""

import sys
import mcrfpy


def test_apply_threshold_walkable():
    """apply_threshold sets walkable property correctly"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    # All cells start with default walkable
    grid.apply_threshold(hmap, range=(0.0, 1.0), walkable=True)

    # Check a few cells
    assert grid.at((5, 5)).walkable == True
    assert grid.at((0, 0)).walkable == True
    assert grid.at((9, 9)).walkable == True
    print("PASS: test_apply_threshold_walkable")


def test_apply_threshold_transparent():
    """apply_threshold sets transparent property correctly"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid.apply_threshold(hmap, range=(0.0, 1.0), transparent=False)

    assert grid.at((5, 5)).transparent == False
    print("PASS: test_apply_threshold_transparent")


def test_apply_threshold_both():
    """apply_threshold sets both walkable and transparent"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid.apply_threshold(hmap, range=(0.0, 1.0), walkable=True, transparent=True)

    point = grid.at((5, 5))
    assert point.walkable == True
    assert point.transparent == True
    print("PASS: test_apply_threshold_both")


def test_apply_threshold_out_of_range():
    """apply_threshold doesn't affect cells outside range"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    # Set initial state
    grid.at((5, 5)).walkable = False
    grid.at((5, 5)).transparent = False

    # Apply threshold with range that excludes 0.5
    grid.apply_threshold(hmap, range=(0.0, 0.4), walkable=True, transparent=True)

    # Cell should remain unchanged
    assert grid.at((5, 5)).walkable == False
    assert grid.at((5, 5)).transparent == False
    print("PASS: test_apply_threshold_out_of_range")


def test_apply_threshold_returns_self():
    """apply_threshold returns self for chaining"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    result = grid.apply_threshold(hmap, range=(0.0, 1.0), walkable=True)
    assert result is grid, "apply_threshold should return self"
    print("PASS: test_apply_threshold_returns_self")


def test_apply_threshold_size_mismatch():
    """apply_threshold raises ValueError for size mismatch"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    hmap = mcrfpy.HeightMap((20, 20), fill=0.5)

    try:
        grid.apply_threshold(hmap, range=(0.0, 1.0), walkable=True)
        print("FAIL: test_apply_threshold_size_mismatch - should have raised ValueError")
        sys.exit(1)
    except ValueError as e:
        assert "size" in str(e).lower()

    print("PASS: test_apply_threshold_size_mismatch")


def test_apply_threshold_invalid_source():
    """apply_threshold raises TypeError for non-HeightMap source"""
    grid = mcrfpy.Grid(grid_size=(10, 10))

    try:
        grid.apply_threshold("not a heightmap", range=(0.0, 1.0), walkable=True)
        print("FAIL: test_apply_threshold_invalid_source - should have raised TypeError")
        sys.exit(1)
    except TypeError:
        pass

    print("PASS: test_apply_threshold_invalid_source")


def test_apply_threshold_none_values():
    """apply_threshold with None values leaves properties unchanged"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    # Set initial state
    grid.at((5, 5)).walkable = True
    grid.at((5, 5)).transparent = False

    # Apply with only walkable=False, transparent should stay unchanged
    grid.apply_threshold(hmap, range=(0.0, 1.0), walkable=False)

    assert grid.at((5, 5)).walkable == False
    assert grid.at((5, 5)).transparent == False  # Unchanged
    print("PASS: test_apply_threshold_none_values")


def test_apply_ranges_basic():
    """apply_ranges applies multiple ranges correctly"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    # Apply a range that covers 0.5
    grid.apply_ranges(hmap, [
        ((0.4, 0.6), {"walkable": True, "transparent": True}),
    ])

    assert grid.at((5, 5)).walkable == True
    assert grid.at((5, 5)).transparent == True
    print("PASS: test_apply_ranges_basic")


def test_apply_ranges_first_match_wins():
    """apply_ranges uses first matching range"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    # Both ranges cover 0.5, first should win
    grid.apply_ranges(hmap, [
        ((0.0, 0.6), {"walkable": True}),
        ((0.4, 1.0), {"walkable": False}),
    ])

    assert grid.at((5, 5)).walkable == True  # First match wins
    print("PASS: test_apply_ranges_first_match_wins")


def test_apply_ranges_returns_self():
    """apply_ranges returns self for chaining"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    result = grid.apply_ranges(hmap, [
        ((0.0, 1.0), {"walkable": True}),
    ])
    assert result is grid, "apply_ranges should return self"
    print("PASS: test_apply_ranges_returns_self")


def test_apply_ranges_size_mismatch():
    """apply_ranges raises ValueError for size mismatch"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    hmap = mcrfpy.HeightMap((5, 5), fill=0.5)

    try:
        grid.apply_ranges(hmap, [
            ((0.0, 1.0), {"walkable": True}),
        ])
        print("FAIL: test_apply_ranges_size_mismatch - should have raised ValueError")
        sys.exit(1)
    except ValueError as e:
        assert "size" in str(e).lower()

    print("PASS: test_apply_ranges_size_mismatch")


def test_apply_ranges_empty_list():
    """apply_ranges with empty list doesn't change anything"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid.at((5, 5)).walkable = True
    grid.at((5, 5)).transparent = False

    grid.apply_ranges(hmap, [])

    # Should remain unchanged
    assert grid.at((5, 5)).walkable == True
    assert grid.at((5, 5)).transparent == False
    print("PASS: test_apply_ranges_empty_list")


def test_apply_ranges_no_match():
    """apply_ranges leaves cells unchanged when no range matches"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid.at((5, 5)).walkable = True
    grid.at((5, 5)).transparent = True

    # Ranges that don't include 0.5
    grid.apply_ranges(hmap, [
        ((0.0, 0.4), {"walkable": False}),
        ((0.6, 1.0), {"transparent": False}),
    ])

    # Should remain unchanged
    assert grid.at((5, 5)).walkable == True
    assert grid.at((5, 5)).transparent == True
    print("PASS: test_apply_ranges_no_match")


def test_apply_ranges_invalid_format():
    """apply_ranges raises TypeError for invalid format"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    # Invalid: not a list
    try:
        grid.apply_ranges(hmap, "not a list")
        print("FAIL: should have raised TypeError for non-list")
        sys.exit(1)
    except TypeError:
        pass

    # Invalid: entry not a tuple
    try:
        grid.apply_ranges(hmap, ["not a tuple"])
        print("FAIL: should have raised TypeError for non-tuple entry")
        sys.exit(1)
    except TypeError:
        pass

    # Invalid: range not a tuple
    try:
        grid.apply_ranges(hmap, [
            ([0.0, 1.0], {"walkable": True}),  # list instead of tuple for range
        ])
        print("FAIL: should have raised TypeError for non-tuple range")
        sys.exit(1)
    except TypeError:
        pass

    # Invalid: props not a dict
    try:
        grid.apply_ranges(hmap, [
            ((0.0, 1.0), "not a dict"),
        ])
        print("FAIL: should have raised TypeError for non-dict props")
        sys.exit(1)
    except TypeError:
        pass

    print("PASS: test_apply_ranges_invalid_format")


def test_chaining():
    """Methods can be chained together"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    hmap = mcrfpy.HeightMap((10, 10))

    # Chain multiple operations
    hmap.fill(0.5)

    result = (grid
              .apply_threshold(hmap, range=(0.0, 0.4), walkable=False)
              .apply_threshold(hmap, range=(0.6, 1.0), transparent=False)
              .apply_ranges(hmap, [
                  ((0.4, 0.6), {"walkable": True, "transparent": True}),
              ]))

    assert result is grid
    print("PASS: test_chaining")


def run_all_tests():
    """Run all tests"""
    print("Running Grid apply method tests...")
    print()

    test_apply_threshold_walkable()
    test_apply_threshold_transparent()
    test_apply_threshold_both()
    test_apply_threshold_out_of_range()
    test_apply_threshold_returns_self()
    test_apply_threshold_size_mismatch()
    test_apply_threshold_invalid_source()
    test_apply_threshold_none_values()
    test_apply_ranges_basic()
    test_apply_ranges_first_match_wins()
    test_apply_ranges_returns_self()
    test_apply_ranges_size_mismatch()
    test_apply_ranges_empty_list()
    test_apply_ranges_no_match()
    test_apply_ranges_invalid_format()
    test_chaining()

    print()
    print("All Grid apply method tests PASSED!")


# Run tests directly
run_all_tests()
sys.exit(0)
