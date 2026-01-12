#!/usr/bin/env python3
"""Unit tests for ColorLayer HeightMap methods (#201)

Tests ColorLayer.apply_threshold(), apply_gradient(), and apply_ranges() methods.
"""

import sys
import mcrfpy


def test_apply_threshold_basic():
    """apply_threshold sets colors in range"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('color', z_index=0)
    layer.fill((0, 0, 0, 0))  # Clear all

    # Apply threshold - all cells should get blue
    result = layer.apply_threshold(hmap, (0.4, 0.6), (0, 0, 255))

    # Verify result is the layer (chaining)
    assert result is layer, "apply_threshold should return self"

    # Verify color was set
    c = layer.at(0, 0)
    assert c.r == 0 and c.g == 0 and c.b == 255, f"Expected (0, 0, 255), got ({c.r}, {c.g}, {c.b})"
    print("PASS: test_apply_threshold_basic")


def test_apply_threshold_with_alpha():
    """apply_threshold handles RGBA colors"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('color', z_index=0)

    layer.apply_threshold(hmap, (0.0, 1.0), (100, 150, 200, 128))

    c = layer.at(5, 5)
    assert c.r == 100 and c.g == 150 and c.b == 200 and c.a == 128, \
        f"Expected (100, 150, 200, 128), got ({c.r}, {c.g}, {c.b}, {c.a})"
    print("PASS: test_apply_threshold_with_alpha")


def test_apply_threshold_preserves_outside():
    """apply_threshold doesn't modify cells outside range"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('color', z_index=0)
    layer.fill((255, 0, 0))  # Fill with red

    # Apply threshold for range that doesn't include 0.5
    layer.apply_threshold(hmap, (0.6, 1.0), (0, 0, 255))

    # Should still be red
    c = layer.at(0, 0)
    assert c.r == 255 and c.g == 0 and c.b == 0, \
        f"Expected red, got ({c.r}, {c.g}, {c.b})"
    print("PASS: test_apply_threshold_preserves_outside")


def test_apply_threshold_with_color_object():
    """apply_threshold accepts Color objects"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('color', z_index=0)

    color = mcrfpy.Color(50, 100, 150)
    layer.apply_threshold(hmap, (0.0, 1.0), color)

    c = layer.at(0, 0)
    assert c.r == 50 and c.g == 100 and c.b == 150
    print("PASS: test_apply_threshold_with_color_object")


def test_apply_threshold_size_mismatch():
    """apply_threshold rejects mismatched HeightMap size"""
    hmap = mcrfpy.HeightMap((5, 5))  # Different size

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('color', z_index=0)

    try:
        layer.apply_threshold(hmap, (0.0, 1.0), (255, 0, 0))
        print("FAIL: test_apply_threshold_size_mismatch - should have raised ValueError")
        sys.exit(1)
    except ValueError as e:
        assert "size" in str(e).lower()

    print("PASS: test_apply_threshold_size_mismatch")


def test_apply_gradient_basic():
    """apply_gradient interpolates colors"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('color', z_index=0)

    # Apply gradient from black to white
    result = layer.apply_gradient(hmap, (0.0, 1.0), (0, 0, 0), (255, 255, 255))

    assert result is layer, "apply_gradient should return self"

    # At 0.5 in range [0,1], should be gray (~127-128)
    c = layer.at(0, 0)
    assert 120 < c.r < 135, f"Expected ~127, got r={c.r}"
    assert 120 < c.g < 135, f"Expected ~127, got g={c.g}"
    assert 120 < c.b < 135, f"Expected ~127, got b={c.b}"
    print("PASS: test_apply_gradient_basic")


def test_apply_gradient_full_range():
    """apply_gradient at range endpoints"""
    # Test at minimum of range
    hmap_low = mcrfpy.HeightMap((10, 10), fill=0.0)

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('color', z_index=0)

    layer.apply_gradient(hmap_low, (0.0, 1.0), (100, 0, 0), (200, 255, 0))

    c = layer.at(0, 0)
    # At t=0.0, should be color_low
    assert c.r == 100 and c.g == 0 and c.b == 0, \
        f"Expected (100, 0, 0), got ({c.r}, {c.g}, {c.b})"

    # Test at maximum of range
    hmap_high = mcrfpy.HeightMap((10, 10), fill=1.0)
    layer.apply_gradient(hmap_high, (0.0, 1.0), (100, 0, 0), (200, 255, 0))

    c = layer.at(0, 0)
    # At t=1.0, should be color_high
    assert c.r == 200 and c.g == 255 and c.b == 0, \
        f"Expected (200, 255, 0), got ({c.r}, {c.g}, {c.b})"

    print("PASS: test_apply_gradient_full_range")


def test_apply_gradient_preserves_outside():
    """apply_gradient doesn't modify cells outside range"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('color', z_index=0)
    layer.fill((255, 0, 0))  # Fill with red

    # Apply gradient for range that doesn't include 0.5
    layer.apply_gradient(hmap, (0.6, 1.0), (0, 0, 0), (255, 255, 255))

    # Should still be red
    c = layer.at(0, 0)
    assert c.r == 255 and c.g == 0 and c.b == 0
    print("PASS: test_apply_gradient_preserves_outside")


def test_apply_ranges_fixed_colors():
    """apply_ranges with fixed colors"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('color', z_index=0)
    layer.fill((0, 0, 0))

    result = layer.apply_ranges(hmap, [
        ((0.0, 0.3), (255, 0, 0)),     # Red, won't match
        ((0.3, 0.7), (0, 255, 0)),     # Green, will match
        ((0.7, 1.0), (0, 0, 255)),     # Blue, won't match
    ])

    assert result is layer, "apply_ranges should return self"

    c = layer.at(0, 0)
    assert c.r == 0 and c.g == 255 and c.b == 0, \
        f"Expected green, got ({c.r}, {c.g}, {c.b})"
    print("PASS: test_apply_ranges_fixed_colors")


def test_apply_ranges_gradient():
    """apply_ranges with gradient specification"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('color', z_index=0)

    # Gradient from (0,0,0) to (255,255,255) over range [0,1]
    # At value 0.5, should be ~(127,127,127)
    layer.apply_ranges(hmap, [
        ((0.0, 1.0), ((0, 0, 0), (255, 255, 255))),  # Gradient
    ])

    c = layer.at(0, 0)
    assert 120 < c.r < 135, f"Expected ~127, got r={c.r}"
    print("PASS: test_apply_ranges_gradient")


def test_apply_ranges_mixed():
    """apply_ranges with mixed fixed and gradient entries"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('color', z_index=0)
    layer.fill((0, 0, 0))

    # Test mixed: gradient that includes 0.5
    layer.apply_ranges(hmap, [
        ((0.0, 0.3), (255, 0, 0)),                         # Fixed red
        ((0.3, 0.7), ((50, 50, 50), (200, 200, 200))),   # Gradient gray
    ])

    # 0.5 is at midpoint of [0.3, 0.7] range, so t = 0.5
    # Expected: 50 + (200-50)*0.5 = 125
    c = layer.at(0, 0)
    assert 120 < c.r < 130, f"Expected ~125, got r={c.r}"
    print("PASS: test_apply_ranges_mixed")


def test_apply_ranges_later_wins():
    """apply_ranges: later ranges override earlier ones"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('color', z_index=0)

    layer.apply_ranges(hmap, [
        ((0.0, 1.0), (255, 0, 0)),   # Red, matches everything
        ((0.4, 0.6), (0, 255, 0)),   # Green, also matches 0.5
    ])

    # Green should win (later entry)
    c = layer.at(0, 0)
    assert c.r == 0 and c.g == 255 and c.b == 0
    print("PASS: test_apply_ranges_later_wins")


def test_apply_ranges_no_match_unchanged():
    """apply_ranges leaves unmatched cells unchanged"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('color', z_index=0)
    layer.fill((128, 128, 128))  # Gray marker

    layer.apply_ranges(hmap, [
        ((0.0, 0.2), (255, 0, 0)),
        ((0.8, 1.0), (0, 0, 255)),
    ])

    # Should still be gray
    c = layer.at(0, 0)
    assert c.r == 128 and c.g == 128 and c.b == 128
    print("PASS: test_apply_ranges_no_match_unchanged")


def test_apply_threshold_invalid_range():
    """apply_threshold rejects min > max"""
    hmap = mcrfpy.HeightMap((10, 10))

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('color', z_index=0)

    try:
        layer.apply_threshold(hmap, (1.0, 0.0), (255, 0, 0))
        print("FAIL: test_apply_threshold_invalid_range - should have raised ValueError")
        sys.exit(1)
    except ValueError as e:
        assert "min" in str(e).lower()

    print("PASS: test_apply_threshold_invalid_range")


def test_apply_gradient_narrow_range():
    """apply_gradient handles narrow value ranges correctly"""
    # Use a value exactly at the range
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = grid.add_layer('color', z_index=0)

    # Apply gradient over exact value (min == max)
    layer.apply_gradient(hmap, (0.5, 0.5), (0, 0, 0), (255, 255, 255))

    # When range_span is 0, t should be 0, so color_low
    c = layer.at(0, 0)
    assert c.r == 0 and c.g == 0 and c.b == 0, \
        f"Expected black at zero-width range, got ({c.r}, {c.g}, {c.b})"
    print("PASS: test_apply_gradient_narrow_range")


def run_all_tests():
    """Run all tests"""
    print("Running ColorLayer HeightMap method tests (#201)...")
    print()

    test_apply_threshold_basic()
    test_apply_threshold_with_alpha()
    test_apply_threshold_preserves_outside()
    test_apply_threshold_with_color_object()
    test_apply_threshold_size_mismatch()
    test_apply_gradient_basic()
    test_apply_gradient_full_range()
    test_apply_gradient_preserves_outside()
    test_apply_ranges_fixed_colors()
    test_apply_ranges_gradient()
    test_apply_ranges_mixed()
    test_apply_ranges_later_wins()
    test_apply_ranges_no_match_unchanged()
    test_apply_threshold_invalid_range()
    test_apply_gradient_narrow_range()

    print()
    print("All ColorLayer HeightMap method tests PASSED!")


# Run tests directly
run_all_tests()
sys.exit(0)
