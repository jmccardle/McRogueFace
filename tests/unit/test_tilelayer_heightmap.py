#!/usr/bin/env python3
"""Unit tests for TileLayer HeightMap methods (#200)

Tests TileLayer.apply_threshold() and TileLayer.apply_ranges() methods.
"""

import sys
import mcrfpy


def test_apply_threshold_basic():
    """apply_threshold sets tiles in range"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    # Create a grid and get a tile layer
    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('tile', z_index=0)
    layer.fill(-1)  # Clear all tiles

    # Apply threshold - all cells should get tile 5
    result = layer.apply_threshold(hmap, (0.4, 0.6), 5)

    # Verify result is the layer (chaining)
    assert result is layer, "apply_threshold should return self"

    # Verify tiles were set
    assert layer.at(0, 0) == 5, f"Expected tile 5, got {layer.at(0, 0)}"
    assert layer.at(5, 5) == 5, f"Expected tile 5, got {layer.at(5, 5)}"
    print("PASS: test_apply_threshold_basic")


def test_apply_threshold_partial():
    """apply_threshold only affects cells in range"""
    hmap = mcrfpy.HeightMap((10, 10))
    # Fill with different values in different areas
    hmap.fill(0.0)  # Start with 0

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('tile', z_index=0)
    layer.fill(-1)

    # Apply threshold for range that doesn't match (0.5-1.0 when values are 0.0)
    layer.apply_threshold(hmap, (0.5, 1.0), 10)

    # Should still be -1 since 0.0 is not in [0.5, 1.0]
    assert layer.at(0, 0) == -1, f"Expected -1, got {layer.at(0, 0)}"
    print("PASS: test_apply_threshold_partial")


def test_apply_threshold_preserves_outside():
    """apply_threshold doesn't modify cells outside range"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('tile', z_index=0)
    layer.fill(99)  # Fill with marker value

    # Apply threshold for range that doesn't include 0.5
    layer.apply_threshold(hmap, (0.6, 1.0), 10)

    # Should still be 99
    assert layer.at(0, 0) == 99, f"Expected 99, got {layer.at(0, 0)}"
    print("PASS: test_apply_threshold_preserves_outside")


def test_apply_threshold_invalid_range():
    """apply_threshold rejects min > max"""
    hmap = mcrfpy.HeightMap((10, 10))

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('tile', z_index=0)

    try:
        layer.apply_threshold(hmap, (1.0, 0.0), 5)  # min > max
        print("FAIL: test_apply_threshold_invalid_range - should have raised ValueError")
        sys.exit(1)
    except ValueError as e:
        assert "min" in str(e).lower()

    print("PASS: test_apply_threshold_invalid_range")


def test_apply_threshold_size_mismatch():
    """apply_threshold rejects mismatched HeightMap size"""
    hmap = mcrfpy.HeightMap((5, 5))  # Different size

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('tile', z_index=0)

    try:
        layer.apply_threshold(hmap, (0.0, 1.0), 5)
        print("FAIL: test_apply_threshold_size_mismatch - should have raised ValueError")
        sys.exit(1)
    except ValueError as e:
        assert "size" in str(e).lower()

    print("PASS: test_apply_threshold_size_mismatch")


def test_apply_ranges_basic():
    """apply_ranges sets multiple tile ranges"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('tile', z_index=0)
    layer.fill(-1)

    # Apply ranges - 0.5 falls in the second range
    result = layer.apply_ranges(hmap, [
        ((0.0, 0.3), 1),   # Won't match
        ((0.3, 0.7), 2),   # Will match (0.5 is in here)
        ((0.7, 1.0), 3),   # Won't match
    ])

    assert result is layer, "apply_ranges should return self"
    assert layer.at(0, 0) == 2, f"Expected tile 2, got {layer.at(0, 0)}"
    print("PASS: test_apply_ranges_basic")


def test_apply_ranges_later_wins():
    """apply_ranges: later ranges override earlier ones"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('tile', z_index=0)
    layer.fill(-1)

    # Apply overlapping ranges - later should win
    layer.apply_ranges(hmap, [
        ((0.0, 1.0), 10),  # Matches everything
        ((0.4, 0.6), 20),  # Also matches 0.5, comes later
    ])

    # Later range (20) should win
    assert layer.at(0, 0) == 20, f"Expected tile 20, got {layer.at(0, 0)}"
    print("PASS: test_apply_ranges_later_wins")


def test_apply_ranges_no_match_unchanged():
    """apply_ranges leaves unmatched cells unchanged"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('tile', z_index=0)
    layer.fill(99)

    # Apply ranges that don't match 0.5
    layer.apply_ranges(hmap, [
        ((0.0, 0.2), 1),
        ((0.8, 1.0), 2),
    ])

    # Should still be 99
    assert layer.at(0, 0) == 99, f"Expected 99, got {layer.at(0, 0)}"
    print("PASS: test_apply_ranges_no_match_unchanged")


def test_apply_ranges_invalid_format():
    """apply_ranges rejects invalid range format"""
    hmap = mcrfpy.HeightMap((10, 10))

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('tile', z_index=0)

    # Missing tile index
    try:
        layer.apply_ranges(hmap, [((0.0, 1.0),)])  # Tuple with only one element
        print("FAIL: test_apply_ranges_invalid_format - should have raised TypeError")
        sys.exit(1)
    except TypeError:
        pass

    print("PASS: test_apply_ranges_invalid_format")


def test_apply_threshold_boundary():
    """apply_threshold includes boundary values"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('tile', z_index=0)
    layer.fill(-1)

    # Range includes 0.5 exactly
    layer.apply_threshold(hmap, (0.5, 0.5), 7)

    assert layer.at(0, 0) == 7, f"Expected 7, got {layer.at(0, 0)}"
    print("PASS: test_apply_threshold_boundary")


def test_apply_threshold_accepts_list():
    """apply_threshold accepts list as range"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('tile', z_index=0)
    layer.fill(-1)

    # Use list instead of tuple
    layer.apply_threshold(hmap, [0.4, 0.6], 5)

    assert layer.at(0, 0) == 5
    print("PASS: test_apply_threshold_accepts_list")


def run_all_tests():
    """Run all tests"""
    print("Running TileLayer HeightMap method tests (#200)...")
    print()

    test_apply_threshold_basic()
    test_apply_threshold_partial()
    test_apply_threshold_preserves_outside()
    test_apply_threshold_invalid_range()
    test_apply_threshold_size_mismatch()
    test_apply_ranges_basic()
    test_apply_ranges_later_wins()
    test_apply_ranges_no_match_unchanged()
    test_apply_ranges_invalid_format()
    test_apply_threshold_boundary()
    test_apply_threshold_accepts_list()

    print()
    print("All TileLayer HeightMap method tests PASSED!")


# Run tests directly
run_all_tests()
sys.exit(0)
