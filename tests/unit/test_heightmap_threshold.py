#!/usr/bin/env python3
"""Unit tests for mcrfpy.HeightMap threshold operations (#197)

Tests the HeightMap threshold methods: threshold, threshold_binary, inverse
These methods return NEW HeightMap objects, preserving the original.
"""

import sys
import mcrfpy


def test_threshold_basic():
    """threshold() returns new HeightMap with values in range"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    result = hmap.threshold((0.4, 0.6))

    # Result should have values (all 0.5 are in range)
    assert abs(result[5, 5] - 0.5) < 0.001, f"Expected 0.5, got {result[5, 5]}"
    print("PASS: test_threshold_basic")


def test_threshold_preserves_original():
    """threshold() does not modify original"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    original_value = hmap[5, 5]

    _ = hmap.threshold((0.0, 0.3))  # Range excludes 0.5

    # Original should be unchanged
    assert abs(hmap[5, 5] - original_value) < 0.001, "Original was modified!"
    print("PASS: test_threshold_preserves_original")


def test_threshold_returns_new():
    """threshold() returns a different object"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    result = hmap.threshold((0.0, 1.0))

    assert result is not hmap, "threshold should return a new HeightMap"
    print("PASS: test_threshold_returns_new")


def test_threshold_out_of_range():
    """threshold() sets values outside range to 0.0"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    result = hmap.threshold((0.6, 1.0))  # Excludes 0.5

    # All values should be 0.0 since 0.5 is not in [0.6, 1.0]
    assert abs(result[5, 5]) < 0.001, f"Expected 0.0, got {result[5, 5]}"
    print("PASS: test_threshold_out_of_range")


def test_threshold_preserves_values():
    """threshold() preserves original values (not just 1.0)"""
    hmap = mcrfpy.HeightMap((10, 10))

    # Set different values manually using scalar ops
    hmap.fill(0.0)

    # We can't set individual values, so let's test with uniform map
    # and verify the value is preserved, not converted to 1.0
    hmap2 = mcrfpy.HeightMap((10, 10), fill=0.75)
    result = hmap2.threshold((0.5, 1.0))

    assert abs(result[5, 5] - 0.75) < 0.001, f"Expected 0.75, got {result[5, 5]}"
    print("PASS: test_threshold_preserves_values")


def test_threshold_invalid_range():
    """threshold() raises ValueError for invalid range"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    try:
        hmap.threshold((1.0, 0.0))  # min > max
        print("FAIL: test_threshold_invalid_range - should have raised ValueError")
        sys.exit(1)
    except ValueError as e:
        assert "min" in str(e).lower()

    print("PASS: test_threshold_invalid_range")


def test_threshold_accepts_list():
    """threshold() accepts list as range"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    result = hmap.threshold([0.4, 0.6])  # List instead of tuple

    assert abs(result[5, 5] - 0.5) < 0.001
    print("PASS: test_threshold_accepts_list")


def test_threshold_binary_basic():
    """threshold_binary() sets uniform value in range"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    result = hmap.threshold_binary((0.4, 0.6))

    # Default value is 1.0
    assert abs(result[5, 5] - 1.0) < 0.001, f"Expected 1.0, got {result[5, 5]}"
    print("PASS: test_threshold_binary_basic")


def test_threshold_binary_custom_value():
    """threshold_binary() uses custom value"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    result = hmap.threshold_binary((0.4, 0.6), value=0.8)

    assert abs(result[5, 5] - 0.8) < 0.001, f"Expected 0.8, got {result[5, 5]}"
    print("PASS: test_threshold_binary_custom_value")


def test_threshold_binary_out_of_range():
    """threshold_binary() sets 0.0 for values outside range"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    result = hmap.threshold_binary((0.6, 1.0))

    # 0.5 is not in [0.6, 1.0], so result should be 0.0
    assert abs(result[5, 5]) < 0.001, f"Expected 0.0, got {result[5, 5]}"
    print("PASS: test_threshold_binary_out_of_range")


def test_threshold_binary_preserves_original():
    """threshold_binary() does not modify original"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    _ = hmap.threshold_binary((0.0, 1.0), value=0.0)

    assert abs(hmap[5, 5] - 0.5) < 0.001, "Original was modified!"
    print("PASS: test_threshold_binary_preserves_original")


def test_threshold_binary_invalid_range():
    """threshold_binary() raises ValueError for invalid range"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    try:
        hmap.threshold_binary((1.0, 0.0))  # min > max
        print("FAIL: test_threshold_binary_invalid_range - should have raised ValueError")
        sys.exit(1)
    except ValueError as e:
        assert "min" in str(e).lower()

    print("PASS: test_threshold_binary_invalid_range")


def test_inverse_basic():
    """inverse() returns (1.0 - value) for each cell"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.3)
    result = hmap.inverse()

    expected = 1.0 - 0.3
    assert abs(result[5, 5] - expected) < 0.001, f"Expected {expected}, got {result[5, 5]}"
    print("PASS: test_inverse_basic")


def test_inverse_preserves_original():
    """inverse() does not modify original"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.3)
    _ = hmap.inverse()

    assert abs(hmap[5, 5] - 0.3) < 0.001, "Original was modified!"
    print("PASS: test_inverse_preserves_original")


def test_inverse_returns_new():
    """inverse() returns a different object"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    result = hmap.inverse()

    assert result is not hmap, "inverse should return a new HeightMap"
    print("PASS: test_inverse_returns_new")


def test_inverse_zero():
    """inverse() of 0.0 is 1.0"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.0)
    result = hmap.inverse()

    assert abs(result[5, 5] - 1.0) < 0.001, f"Expected 1.0, got {result[5, 5]}"
    print("PASS: test_inverse_zero")


def test_inverse_one():
    """inverse() of 1.0 is 0.0"""
    hmap = mcrfpy.HeightMap((10, 10), fill=1.0)
    result = hmap.inverse()

    assert abs(result[5, 5]) < 0.001, f"Expected 0.0, got {result[5, 5]}"
    print("PASS: test_inverse_one")


def test_inverse_half():
    """inverse() of 0.5 is 0.5"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    result = hmap.inverse()

    assert abs(result[5, 5] - 0.5) < 0.001, f"Expected 0.5, got {result[5, 5]}"
    print("PASS: test_inverse_half")


def test_double_inverse():
    """double inverse() returns to original value"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.7)
    result = hmap.inverse().inverse()

    assert abs(result[5, 5] - 0.7) < 0.001, f"Expected 0.7, got {result[5, 5]}"
    print("PASS: test_double_inverse")


def test_size_preserved():
    """threshold operations preserve HeightMap size"""
    hmap = mcrfpy.HeightMap((15, 20), fill=0.5)

    result1 = hmap.threshold((0.0, 1.0))
    result2 = hmap.threshold_binary((0.0, 1.0))
    result3 = hmap.inverse()

    assert result1.size == (15, 20), f"threshold size mismatch: {result1.size}"
    assert result2.size == (15, 20), f"threshold_binary size mismatch: {result2.size}"
    assert result3.size == (15, 20), f"inverse size mismatch: {result3.size}"
    print("PASS: test_size_preserved")


def run_all_tests():
    """Run all tests"""
    print("Running HeightMap threshold operation tests (#197)...")
    print()

    test_threshold_basic()
    test_threshold_preserves_original()
    test_threshold_returns_new()
    test_threshold_out_of_range()
    test_threshold_preserves_values()
    test_threshold_invalid_range()
    test_threshold_accepts_list()
    test_threshold_binary_basic()
    test_threshold_binary_custom_value()
    test_threshold_binary_out_of_range()
    test_threshold_binary_preserves_original()
    test_threshold_binary_invalid_range()
    test_inverse_basic()
    test_inverse_preserves_original()
    test_inverse_returns_new()
    test_inverse_zero()
    test_inverse_one()
    test_inverse_half()
    test_double_inverse()
    test_size_preserved()

    print()
    print("All HeightMap threshold operation tests PASSED!")


# Run tests directly
run_all_tests()
sys.exit(0)
