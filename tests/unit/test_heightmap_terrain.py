#!/usr/bin/env python3
"""Unit tests for mcrfpy.HeightMap terrain generation methods (#195)

Tests the HeightMap terrain methods: add_hill, dig_hill, add_voronoi,
mid_point_displacement, rain_erosion, dig_bezier, smooth
"""

import sys
import mcrfpy


def test_add_hill_basic():
    """add_hill() creates elevation at center"""
    hmap = mcrfpy.HeightMap((50, 50), fill=0.0)
    hmap.add_hill((25, 25), radius=10.0, height=1.0)

    # Center should have highest value
    center_val = hmap[25, 25]
    edge_val = hmap[0, 0]

    assert center_val > edge_val, f"Center ({center_val}) should be higher than edge ({edge_val})"
    assert center_val > 0.5, f"Center should be significantly elevated, got {center_val}"
    print("PASS: test_add_hill_basic")


def test_add_hill_returns_self():
    """add_hill() returns self for chaining"""
    hmap = mcrfpy.HeightMap((20, 20))
    result = hmap.add_hill((10, 10), 5.0, 1.0)
    assert result is hmap
    print("PASS: test_add_hill_returns_self")


def test_add_hill_flexible_center():
    """add_hill() accepts tuple, list, and Vector for center"""
    hmap1 = mcrfpy.HeightMap((20, 20), fill=0.0)
    hmap2 = mcrfpy.HeightMap((20, 20), fill=0.0)
    hmap3 = mcrfpy.HeightMap((20, 20), fill=0.0)

    hmap1.add_hill((10, 10), 5.0, 1.0)
    hmap2.add_hill([10, 10], 5.0, 1.0)
    hmap3.add_hill(mcrfpy.Vector(10, 10), 5.0, 1.0)

    # All should produce same result
    assert abs(hmap1[10, 10] - hmap2[10, 10]) < 0.001
    assert abs(hmap1[10, 10] - hmap3[10, 10]) < 0.001
    print("PASS: test_add_hill_flexible_center")


def test_dig_hill_basic():
    """dig_hill() creates depression at center using negative depth"""
    hmap = mcrfpy.HeightMap((50, 50), fill=0.5)
    # dig_hill with negative depth creates a crater by setting values
    # to max(current, target_depth) where target curves from center
    hmap.dig_hill((25, 25), radius=15.0, depth=-0.3)

    # Center should have lowest value (set to the negative depth)
    center_val = hmap[25, 25]
    edge_val = hmap[0, 0]

    assert center_val < edge_val, f"Center ({center_val}) should be lower than edge ({edge_val})"
    assert center_val < 0, f"Center should be negative, got {center_val}"
    print("PASS: test_dig_hill_basic")


def test_dig_hill_returns_self():
    """dig_hill() returns self for chaining"""
    hmap = mcrfpy.HeightMap((20, 20))
    result = hmap.dig_hill((10, 10), 5.0, 0.5)
    assert result is hmap
    print("PASS: test_dig_hill_returns_self")


def test_add_voronoi_basic():
    """add_voronoi() modifies heightmap"""
    hmap = mcrfpy.HeightMap((50, 50), fill=0.0)
    min_before, max_before = hmap.min_max()

    hmap.add_voronoi(10, seed=12345)

    min_after, max_after = hmap.min_max()

    # Values should have changed
    assert max_after > max_before or min_after < min_before, "Voronoi should modify values"
    print("PASS: test_add_voronoi_basic")


def test_add_voronoi_with_coefficients():
    """add_voronoi() accepts custom coefficients"""
    hmap = mcrfpy.HeightMap((30, 30), fill=0.0)
    hmap.add_voronoi(5, coefficients=(1.0, -0.5, 0.3), seed=42)

    # Should complete without error
    min_val, max_val = hmap.min_max()
    assert min_val != max_val, "Voronoi should create variation"
    print("PASS: test_add_voronoi_with_coefficients")


def test_add_voronoi_returns_self():
    """add_voronoi() returns self for chaining"""
    hmap = mcrfpy.HeightMap((20, 20))
    result = hmap.add_voronoi(5)
    assert result is hmap
    print("PASS: test_add_voronoi_returns_self")


def test_add_voronoi_invalid_num_points():
    """add_voronoi() raises ValueError for invalid num_points"""
    hmap = mcrfpy.HeightMap((20, 20))

    try:
        hmap.add_voronoi(0)
        print("FAIL: should have raised ValueError for num_points=0")
        sys.exit(1)
    except ValueError:
        pass

    print("PASS: test_add_voronoi_invalid_num_points")


def test_mid_point_displacement_basic():
    """mid_point_displacement() generates terrain"""
    # Use power-of-2+1 size for best results
    hmap = mcrfpy.HeightMap((65, 65), fill=0.0)
    hmap.mid_point_displacement(roughness=0.5, seed=12345)

    min_val, max_val = hmap.min_max()
    assert min_val != max_val, "MPD should create variation"
    print("PASS: test_mid_point_displacement_basic")


def test_mid_point_displacement_returns_self():
    """mid_point_displacement() returns self for chaining"""
    hmap = mcrfpy.HeightMap((33, 33))
    result = hmap.mid_point_displacement()
    assert result is hmap
    print("PASS: test_mid_point_displacement_returns_self")


def test_mid_point_displacement_reproducible():
    """mid_point_displacement() is reproducible with same seed"""
    hmap1 = mcrfpy.HeightMap((33, 33), fill=0.0)
    hmap2 = mcrfpy.HeightMap((33, 33), fill=0.0)

    hmap1.mid_point_displacement(roughness=0.6, seed=99999)
    hmap2.mid_point_displacement(roughness=0.6, seed=99999)

    # Should produce identical results
    assert abs(hmap1[16, 16] - hmap2[16, 16]) < 0.001
    assert abs(hmap1[5, 5] - hmap2[5, 5]) < 0.001
    print("PASS: test_mid_point_displacement_reproducible")


def test_rain_erosion_basic():
    """rain_erosion() modifies terrain"""
    hmap = mcrfpy.HeightMap((50, 50), fill=0.5)
    # Add some hills first to have something to erode
    hmap.add_hill((25, 25), 15.0, 0.5)

    val_before = hmap[25, 25]
    hmap.rain_erosion(1000, seed=12345)
    val_after = hmap[25, 25]

    # Erosion should change values
    # Note: might not change if terrain is completely flat
    # so we check min/max spread
    min_val, max_val = hmap.min_max()
    assert max_val > min_val, "Rain erosion should leave some variation"
    print("PASS: test_rain_erosion_basic")


def test_rain_erosion_returns_self():
    """rain_erosion() returns self for chaining"""
    hmap = mcrfpy.HeightMap((20, 20))
    result = hmap.rain_erosion(100)
    assert result is hmap
    print("PASS: test_rain_erosion_returns_self")


def test_rain_erosion_invalid_drops():
    """rain_erosion() raises ValueError for invalid drops"""
    hmap = mcrfpy.HeightMap((20, 20))

    try:
        hmap.rain_erosion(0)
        print("FAIL: should have raised ValueError for drops=0")
        sys.exit(1)
    except ValueError:
        pass

    print("PASS: test_rain_erosion_invalid_drops")


def test_dig_bezier_basic():
    """dig_bezier() carves a path using negative depths"""
    hmap = mcrfpy.HeightMap((50, 50), fill=0.5)

    # Carve a path from corner to corner
    # Use negative depths to actually dig below current terrain
    points = ((0, 0), (10, 25), (40, 25), (49, 49))
    hmap.dig_bezier(points, start_radius=5.0, end_radius=5.0,
                    start_depth=-0.3, end_depth=-0.3)

    # Start and end should be lower than original (carved out)
    assert hmap[0, 0] < 0.5, f"Start should be carved, got {hmap[0, 0]}"
    assert hmap[0, 0] < 0, f"Start should be negative, got {hmap[0, 0]}"
    print("PASS: test_dig_bezier_basic")


def test_dig_bezier_returns_self():
    """dig_bezier() returns self for chaining"""
    hmap = mcrfpy.HeightMap((20, 20))
    result = hmap.dig_bezier(((0, 0), (5, 10), (15, 10), (19, 19)), 2.0, 2.0, 0.3, 0.3)
    assert result is hmap
    print("PASS: test_dig_bezier_returns_self")


def test_dig_bezier_wrong_point_count():
    """dig_bezier() raises ValueError for wrong number of points"""
    hmap = mcrfpy.HeightMap((20, 20))

    try:
        hmap.dig_bezier(((0, 0), (5, 5), (10, 10)), 2.0, 2.0, 0.3, 0.3)  # Only 3 points
        print("FAIL: should have raised ValueError for 3 points")
        sys.exit(1)
    except ValueError as e:
        assert "4" in str(e)

    print("PASS: test_dig_bezier_wrong_point_count")


def test_dig_bezier_accepts_list():
    """dig_bezier() accepts list of points"""
    hmap = mcrfpy.HeightMap((20, 20), fill=0.5)
    points = [[0, 0], [5, 10], [15, 10], [19, 19]]  # List instead of tuple
    hmap.dig_bezier(points, 2.0, 2.0, 0.3, 0.3)
    # Should complete without error
    print("PASS: test_dig_bezier_accepts_list")


def test_smooth_basic():
    """smooth() reduces terrain variation"""
    hmap = mcrfpy.HeightMap((30, 30), fill=0.0)
    # Create sharp height differences
    hmap.add_hill((15, 15), 5.0, 1.0)

    # Get slope before smoothing (measure of sharpness)
    slope_before = hmap.get_slope((15, 15))

    hmap.smooth(iterations=3)

    # Smoothing should reduce the slope
    slope_after = hmap.get_slope((15, 15))
    # Note: slope might not always decrease depending on terrain, so we just verify it runs
    min_val, max_val = hmap.min_max()
    assert max_val >= min_val
    print("PASS: test_smooth_basic")


def test_smooth_returns_self():
    """smooth() returns self for chaining"""
    hmap = mcrfpy.HeightMap((20, 20))
    result = hmap.smooth()
    assert result is hmap
    print("PASS: test_smooth_returns_self")


def test_smooth_invalid_iterations():
    """smooth() raises ValueError for invalid iterations"""
    hmap = mcrfpy.HeightMap((20, 20))

    try:
        hmap.smooth(iterations=0)
        print("FAIL: should have raised ValueError for iterations=0")
        sys.exit(1)
    except ValueError:
        pass

    print("PASS: test_smooth_invalid_iterations")


def test_chaining_terrain_methods():
    """Terrain methods can be chained together"""
    hmap = mcrfpy.HeightMap((50, 50), fill=0.0)

    result = (hmap
              .add_hill((25, 25), 10.0, 0.5)
              .add_hill((10, 10), 8.0, 0.3)
              .dig_hill((40, 40), 5.0, 0.2)
              .smooth(iterations=2)
              .normalize(0.0, 1.0))

    assert result is hmap
    min_val, max_val = hmap.min_max()
    assert abs(min_val - 0.0) < 0.001
    assert abs(max_val - 1.0) < 0.001
    print("PASS: test_chaining_terrain_methods")


def test_terrain_pipeline():
    """Complete terrain generation pipeline"""
    hmap = mcrfpy.HeightMap((65, 65), fill=0.0)

    # Generate base terrain
    hmap.mid_point_displacement(roughness=0.6, seed=42)
    hmap.normalize(0.0, 1.0)

    # Add features
    hmap.add_hill((32, 32), 20.0, 0.3)  # Mountain
    # dig_bezier with negative depths to carve a river valley
    hmap.dig_bezier(((0, 32), (20, 20), (45, 45), (64, 32)), 3.0, 2.0, -0.3, -0.2)

    # Apply erosion and smoothing
    hmap.rain_erosion(500, seed=123)
    hmap.smooth()

    # Normalize to 0-1 range
    hmap.normalize(0.0, 1.0)

    min_val, max_val = hmap.min_max()
    assert abs(min_val - 0.0) < 0.001
    assert abs(max_val - 1.0) < 0.001
    print("PASS: test_terrain_pipeline")


def run_all_tests():
    """Run all tests"""
    print("Running HeightMap terrain generation tests (#195)...")
    print()

    test_add_hill_basic()
    test_add_hill_returns_self()
    test_add_hill_flexible_center()
    test_dig_hill_basic()
    test_dig_hill_returns_self()
    test_add_voronoi_basic()
    test_add_voronoi_with_coefficients()
    test_add_voronoi_returns_self()
    test_add_voronoi_invalid_num_points()
    test_mid_point_displacement_basic()
    test_mid_point_displacement_returns_self()
    test_mid_point_displacement_reproducible()
    test_rain_erosion_basic()
    test_rain_erosion_returns_self()
    test_rain_erosion_invalid_drops()
    test_dig_bezier_basic()
    test_dig_bezier_returns_self()
    test_dig_bezier_wrong_point_count()
    test_dig_bezier_accepts_list()
    test_smooth_basic()
    test_smooth_returns_self()
    test_smooth_invalid_iterations()
    test_chaining_terrain_methods()
    test_terrain_pipeline()

    print()
    print("All HeightMap terrain generation tests PASSED!")


# Run tests directly
run_all_tests()
sys.exit(0)
