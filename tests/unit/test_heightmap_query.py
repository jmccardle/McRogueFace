#!/usr/bin/env python3
"""Unit tests for mcrfpy.HeightMap query methods (#196)

Tests the HeightMap query methods: get, get_interpolated, get_slope, get_normal, min_max, count_in_range
"""

import sys
import math
import mcrfpy


def test_get_basic():
    """get() returns correct value at position"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    value = hmap.get((5, 5))
    assert abs(value - 0.5) < 0.001, f"Expected 0.5, got {value}"
    print("PASS: test_get_basic")


def test_get_corners():
    """get() works at all corners"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.25)

    # All corners should have the fill value
    assert abs(hmap.get((0, 0)) - 0.25) < 0.001
    assert abs(hmap.get((9, 0)) - 0.25) < 0.001
    assert abs(hmap.get((0, 9)) - 0.25) < 0.001
    assert abs(hmap.get((9, 9)) - 0.25) < 0.001
    print("PASS: test_get_corners")


def test_get_out_of_bounds():
    """get() raises IndexError for out-of-bounds position"""
    hmap = mcrfpy.HeightMap((10, 10))

    # Test various out-of-bounds positions
    for pos in [(-1, 0), (0, -1), (10, 0), (0, 10), (10, 10)]:
        try:
            hmap.get(pos)
            print(f"FAIL: test_get_out_of_bounds - should have raised IndexError for {pos}")
            sys.exit(1)
        except IndexError:
            pass

    print("PASS: test_get_out_of_bounds")


def test_get_flexible_input():
    """get() accepts tuple, list, Vector, and two args"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    # Tuple works
    assert abs(hmap.get((5, 5)) - 0.5) < 0.001

    # List works
    assert abs(hmap.get([5, 5]) - 0.5) < 0.001

    # Two args work (no tuple needed)
    assert abs(hmap.get(5, 5) - 0.5) < 0.001

    # Vector works
    vec = mcrfpy.Vector(5, 5)
    assert abs(hmap.get(vec) - 0.5) < 0.001

    print("PASS: test_get_flexible_input")


def test_get_interpolated_basic():
    """get_interpolated() returns value at float position"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    value = hmap.get_interpolated((5.5, 5.5))
    # With uniform fill, interpolation should return same value
    assert abs(value - 0.5) < 0.001, f"Expected ~0.5, got {value}"
    print("PASS: test_get_interpolated_basic")


def test_get_interpolated_at_integers():
    """get_interpolated() matches get() at integer positions"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.75)

    int_value = hmap.get((3, 4))
    interp_value = hmap.get_interpolated((3.0, 4.0))

    assert abs(int_value - interp_value) < 0.001, f"Values differ: {int_value} vs {interp_value}"
    print("PASS: test_get_interpolated_at_integers")


def test_get_slope_flat():
    """get_slope() returns 0 for flat terrain"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    slope = hmap.get_slope((5, 5))
    # Flat terrain should have slope near 0
    assert abs(slope) < 0.01, f"Expected ~0 for flat terrain, got {slope}"
    print("PASS: test_get_slope_flat")


def test_get_slope_out_of_bounds():
    """get_slope() raises IndexError for out-of-bounds position"""
    hmap = mcrfpy.HeightMap((10, 10))

    try:
        hmap.get_slope((10, 5))
        print("FAIL: test_get_slope_out_of_bounds - should have raised IndexError")
        sys.exit(1)
    except IndexError:
        pass

    print("PASS: test_get_slope_out_of_bounds")


def test_get_normal_flat():
    """get_normal() returns up vector for flat terrain"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    nx, ny, nz = hmap.get_normal((5.0, 5.0))

    # Flat terrain should have normal pointing up (0, 0, 1)
    assert abs(nx) < 0.01, f"Expected nx~0, got {nx}"
    assert abs(ny) < 0.01, f"Expected ny~0, got {ny}"
    assert abs(nz - 1.0) < 0.01, f"Expected nz~1, got {nz}"
    print("PASS: test_get_normal_flat")


def test_get_normal_with_water_level():
    """get_normal() accepts water_level parameter"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    nx, ny, nz = hmap.get_normal((5.0, 5.0), water_level=0.3)

    # Should still return valid normal
    assert isinstance(nx, float)
    assert isinstance(ny, float)
    assert isinstance(nz, float)
    print("PASS: test_get_normal_with_water_level")


def test_min_max_uniform():
    """min_max() returns correct values for uniform heightmap"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    min_val, max_val = hmap.min_max()

    assert abs(min_val - 0.5) < 0.001, f"Expected min=0.5, got {min_val}"
    assert abs(max_val - 0.5) < 0.001, f"Expected max=0.5, got {max_val}"
    print("PASS: test_min_max_uniform")


def test_min_max_after_operations():
    """min_max() updates after operations"""
    hmap = mcrfpy.HeightMap((10, 10))
    hmap.fill(0.0).add_constant(0.5).scale(2.0)

    min_val, max_val = hmap.min_max()
    expected = 1.0  # 0.0 + 0.5 * 2.0

    assert abs(min_val - expected) < 0.001, f"Expected min={expected}, got {min_val}"
    assert abs(max_val - expected) < 0.001, f"Expected max={expected}, got {max_val}"
    print("PASS: test_min_max_after_operations")


def test_count_in_range_all():
    """count_in_range() returns all cells for uniform map in range"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    count = hmap.count_in_range((0.0, 1.0))

    assert count == 100, f"Expected 100 cells, got {count}"
    print("PASS: test_count_in_range_all")


def test_count_in_range_none():
    """count_in_range() returns 0 when no cells in range"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    count = hmap.count_in_range((0.0, 0.4))

    assert count == 0, f"Expected 0 cells, got {count}"
    print("PASS: test_count_in_range_none")


def test_count_in_range_exact():
    """count_in_range() with exact bounds"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    count = hmap.count_in_range((0.5, 0.5))

    # Should count all cells since fill value is exactly 0.5
    assert count == 100, f"Expected 100 cells at exact value, got {count}"
    print("PASS: test_count_in_range_exact")


def test_count_in_range_accepts_list():
    """count_in_range() accepts list or tuple"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    # Tuple works
    count1 = hmap.count_in_range((0.0, 1.0))
    assert count1 == 100

    # List also works
    count2 = hmap.count_in_range([0.0, 1.0])
    assert count2 == 100

    print("PASS: test_count_in_range_accepts_list")


def test_count_in_range_invalid_range():
    """count_in_range() raises ValueError when min > max"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    try:
        hmap.count_in_range((1.0, 0.0))  # min > max
        print("FAIL: test_count_in_range_invalid_range - should have raised ValueError")
        sys.exit(1)
    except ValueError as e:
        assert "min" in str(e).lower()

    print("PASS: test_count_in_range_invalid_range")


def test_subscript_basic():
    """hmap[x, y] works as shorthand for get()"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.75)

    # Subscript with tuple
    value = hmap[5, 5]
    assert abs(value - 0.75) < 0.001

    print("PASS: test_subscript_basic")


def test_subscript_flexible():
    """hmap[] accepts tuple, list, Vector"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.25)

    # Tuple
    assert abs(hmap[(3, 4)] - 0.25) < 0.001

    # List
    assert abs(hmap[[3, 4]] - 0.25) < 0.001

    # Vector
    vec = mcrfpy.Vector(3, 4)
    assert abs(hmap[vec] - 0.25) < 0.001

    print("PASS: test_subscript_flexible")


def test_subscript_out_of_bounds():
    """hmap[] raises IndexError for out-of-bounds"""
    hmap = mcrfpy.HeightMap((10, 10))

    try:
        _ = hmap[10, 5]
        print("FAIL: test_subscript_out_of_bounds - should have raised IndexError")
        sys.exit(1)
    except IndexError:
        pass

    print("PASS: test_subscript_out_of_bounds")


def run_all_tests():
    """Run all tests"""
    print("Running HeightMap query method tests...")
    print()

    test_get_basic()
    test_get_corners()
    test_get_out_of_bounds()
    test_get_flexible_input()
    test_get_interpolated_basic()
    test_get_interpolated_at_integers()
    test_get_slope_flat()
    test_get_slope_out_of_bounds()
    test_get_normal_flat()
    test_get_normal_with_water_level()
    test_min_max_uniform()
    test_min_max_after_operations()
    test_count_in_range_all()
    test_count_in_range_none()
    test_count_in_range_exact()
    test_count_in_range_accepts_list()
    test_count_in_range_invalid_range()
    test_subscript_basic()
    test_subscript_flexible()
    test_subscript_out_of_bounds()

    print()
    print("All HeightMap query method tests PASSED!")


# Run tests directly
run_all_tests()
sys.exit(0)
