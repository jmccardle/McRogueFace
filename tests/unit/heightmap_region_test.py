"""Unit tests for HeightMap region-based operations

Tests:
- Scalar operations with pos/size parameters (fill, add_constant, scale, clamp, normalize)
- Combination operations with pos/source_pos/size parameters
- BSP operations with pos parameter for coordinate translation
- Region parameter validation and error handling
"""
import mcrfpy
import sys

# ============================================================================
# Scalar operations with region parameters
# ============================================================================

def test_fill_region():
    """Test fill() with region parameters"""
    hmap = mcrfpy.HeightMap((20, 20), fill=0.0)

    # Fill a 5x5 region starting at (5, 5)
    result = hmap.fill(10.0, pos=(5, 5), size=(5, 5))

    # Should return self
    assert result is hmap, "fill() should return self"

    # Check values
    for x in range(20):
        for y in range(20):
            expected = 10.0 if (5 <= x < 10 and 5 <= y < 10) else 0.0
            actual = hmap.get((x, y))
            assert actual == expected, f"At ({x},{y}): expected {expected}, got {actual}"

    print("  PASS: fill() with region")


def test_fill_region_inferred_size():
    """Test fill() with position but no size (infers remaining)"""
    hmap = mcrfpy.HeightMap((15, 15), fill=0.0)

    # Fill from (10, 10) with no size - should fill to end
    hmap.fill(5.0, pos=(10, 10))

    for x in range(15):
        for y in range(15):
            expected = 5.0 if (x >= 10 and y >= 10) else 0.0
            actual = hmap.get((x, y))
            assert actual == expected, f"At ({x},{y}): expected {expected}, got {actual}"

    print("  PASS: fill() with inferred size")


def test_add_constant_region():
    """Test add_constant() with region parameters"""
    hmap = mcrfpy.HeightMap((20, 20), fill=1.0)

    # Add 5.0 to a 10x10 region at origin
    hmap.add_constant(5.0, pos=(0, 0), size=(10, 10))

    for x in range(20):
        for y in range(20):
            expected = 6.0 if (x < 10 and y < 10) else 1.0
            actual = hmap.get((x, y))
            assert actual == expected, f"At ({x},{y}): expected {expected}, got {actual}"

    print("  PASS: add_constant() with region")


def test_scale_region():
    """Test scale() with region parameters"""
    hmap = mcrfpy.HeightMap((20, 20), fill=2.0)

    # Scale a 5x5 region by 3.0
    hmap.scale(3.0, pos=(5, 5), size=(5, 5))

    for x in range(20):
        for y in range(20):
            expected = 6.0 if (5 <= x < 10 and 5 <= y < 10) else 2.0
            actual = hmap.get((x, y))
            assert actual == expected, f"At ({x},{y}): expected {expected}, got {actual}"

    print("  PASS: scale() with region")


def test_clamp_region():
    """Test clamp() with region parameters"""
    hmap = mcrfpy.HeightMap((20, 20), fill=0.0)

    # Set up varying values
    for x in range(20):
        for y in range(20):
            # Values from 0 to 39
            val = float(x + y)
            hmap.fill(val, pos=(x, y), size=(1, 1))

    # Clamp only the center region
    hmap.clamp(5.0, 15.0, pos=(5, 5), size=(10, 10))

    for x in range(20):
        for y in range(20):
            original = float(x + y)
            if 5 <= x < 15 and 5 <= y < 15:
                # Clamped region
                expected = max(5.0, min(15.0, original))
            else:
                # Unaffected
                expected = original
            actual = hmap.get((x, y))
            assert abs(actual - expected) < 0.001, f"At ({x},{y}): expected {expected}, got {actual}"

    print("  PASS: clamp() with region")


def test_normalize_region():
    """Test normalize() with region parameters"""
    hmap = mcrfpy.HeightMap((20, 20), fill=0.0)

    # Set up the center region with known min/max
    for x in range(5, 15):
        for y in range(5, 15):
            val = float((x - 5) + (y - 5))  # 0 to 18
            hmap.fill(val, pos=(x, y), size=(1, 1))

    # Normalize the center region to 0-100
    hmap.normalize(0.0, 100.0, pos=(5, 5), size=(10, 10))

    # Check the center region is normalized
    center_min, center_max = float('inf'), float('-inf')
    for x in range(5, 15):
        for y in range(5, 15):
            val = hmap.get((x, y))
            center_min = min(center_min, val)
            center_max = max(center_max, val)

    assert abs(center_min - 0.0) < 0.001, f"Normalized min should be 0.0, got {center_min}"
    assert abs(center_max - 100.0) < 0.001, f"Normalized max should be 100.0, got {center_max}"

    # Check outside region unchanged (should still be 0.0)
    assert hmap.get((0, 0)) == 0.0, "Outside region should be unchanged"

    print("  PASS: normalize() with region")


# ============================================================================
# Combination operations with region parameters
# ============================================================================

def test_add_region():
    """Test add() with region parameters"""
    h1 = mcrfpy.HeightMap((20, 20), fill=1.0)
    h2 = mcrfpy.HeightMap((20, 20), fill=5.0)

    # Add h2 to h1 in a specific region
    h1.add(h2, pos=(5, 5), source_pos=(0, 0), size=(10, 10))

    for x in range(20):
        for y in range(20):
            expected = 6.0 if (5 <= x < 15 and 5 <= y < 15) else 1.0
            actual = h1.get((x, y))
            assert actual == expected, f"At ({x},{y}): expected {expected}, got {actual}"

    print("  PASS: add() with region")


def test_add_source_pos():
    """Test add() with different source_pos"""
    h1 = mcrfpy.HeightMap((20, 20), fill=0.0)
    h2 = mcrfpy.HeightMap((20, 20), fill=0.0)

    # Set up h2 with non-zero values in a specific area
    h2.fill(10.0, pos=(10, 10), size=(5, 5))

    # Copy from h2's non-zero region to h1's origin
    h1.add(h2, pos=(0, 0), source_pos=(10, 10), size=(5, 5))

    for x in range(20):
        for y in range(20):
            expected = 10.0 if (x < 5 and y < 5) else 0.0
            actual = h1.get((x, y))
            assert actual == expected, f"At ({x},{y}): expected {expected}, got {actual}"

    print("  PASS: add() with source_pos")


def test_copy_from_region():
    """Test copy_from() with region parameters"""
    h1 = mcrfpy.HeightMap((30, 30), fill=0.0)
    h2 = mcrfpy.HeightMap((20, 20), fill=0.0)

    # Fill h2 with a pattern
    for x in range(20):
        for y in range(20):
            h2.fill(float(x * 20 + y), pos=(x, y), size=(1, 1))

    # Copy a 10x10 region from h2 to h1 at offset
    h1.copy_from(h2, pos=(5, 5), source_pos=(3, 3), size=(10, 10))

    # Verify copied region
    for x in range(10):
        for y in range(10):
            src_val = float((3 + x) * 20 + (3 + y))
            dest_val = h1.get((5 + x, 5 + y))
            assert dest_val == src_val, f"At dest ({5+x},{5+y}): expected {src_val}, got {dest_val}"

    # Verify outside copied region is still 0
    assert h1.get((0, 0)) == 0.0, "Outside region should be 0"
    assert h1.get((4, 4)) == 0.0, "Just outside region should be 0"

    print("  PASS: copy_from() with region")


def test_multiply_region():
    """Test multiply() with region parameters (masking)"""
    h1 = mcrfpy.HeightMap((20, 20), fill=10.0)
    h2 = mcrfpy.HeightMap((20, 20), fill=0.5)

    # Multiply a 5x5 region
    h1.multiply(h2, pos=(5, 5), size=(5, 5))

    for x in range(20):
        for y in range(20):
            expected = 5.0 if (5 <= x < 10 and 5 <= y < 10) else 10.0
            actual = h1.get((x, y))
            assert actual == expected, f"At ({x},{y}): expected {expected}, got {actual}"

    print("  PASS: multiply() with region")


def test_lerp_region():
    """Test lerp() with region parameters"""
    h1 = mcrfpy.HeightMap((20, 20), fill=0.0)
    h2 = mcrfpy.HeightMap((20, 20), fill=100.0)

    # Lerp a region with t=0.3
    h1.lerp(h2, 0.3, pos=(5, 5), size=(10, 10))

    for x in range(20):
        for y in range(20):
            expected = 30.0 if (5 <= x < 15 and 5 <= y < 15) else 0.0
            actual = h1.get((x, y))
            assert abs(actual - expected) < 0.001, f"At ({x},{y}): expected {expected}, got {actual}"

    print("  PASS: lerp() with region")


def test_max_region():
    """Test max() with region parameters"""
    h1 = mcrfpy.HeightMap((20, 20), fill=5.0)
    h2 = mcrfpy.HeightMap((20, 20), fill=10.0)

    # Max in a specific region
    h1.max(h2, pos=(5, 5), size=(5, 5))

    for x in range(20):
        for y in range(20):
            expected = 10.0 if (5 <= x < 10 and 5 <= y < 10) else 5.0
            actual = h1.get((x, y))
            assert actual == expected, f"At ({x},{y}): expected {expected}, got {actual}"

    print("  PASS: max() with region")


def test_min_region():
    """Test min() with region parameters"""
    h1 = mcrfpy.HeightMap((20, 20), fill=10.0)
    h2 = mcrfpy.HeightMap((20, 20), fill=3.0)

    # Min in a specific region
    h1.min(h2, pos=(5, 5), size=(5, 5))

    for x in range(20):
        for y in range(20):
            expected = 3.0 if (5 <= x < 10 and 5 <= y < 10) else 10.0
            actual = h1.get((x, y))
            assert actual == expected, f"At ({x},{y}): expected {expected}, got {actual}"

    print("  PASS: min() with region")


# ============================================================================
# BSP operations with pos parameter
# ============================================================================

def test_add_bsp_pos_default():
    """Test add_bsp() with default pos (origin-relative, like to_heightmap)"""
    # Create BSP at non-origin position
    bsp = mcrfpy.BSP(pos=(10, 10), size=(30, 30))
    bsp.split_recursive(depth=2, min_size=(10, 10))

    # Create heightmap larger than BSP
    hmap = mcrfpy.HeightMap((50, 50), fill=0.0)

    # Default pos=None should translate to origin-relative (BSP at 0,0)
    hmap.add_bsp(bsp)

    # Verify: the BSP region should be mapped starting from (0, 0)
    # Check that at least some of the 30x30 region has non-zero values
    count = 0
    for x in range(30):
        for y in range(30):
            if hmap.get((x, y)) > 0:
                count += 1

    assert count > 0, "add_bsp() with default pos should map BSP to origin"

    # Check that outside BSP's relative bounds is zero
    assert hmap.get((35, 35)) == 0.0, "Outside BSP bounds should be 0"

    print("  PASS: add_bsp() with default pos (origin-relative)")


def test_add_bsp_pos_custom():
    """Test add_bsp() with custom pos parameter"""
    # Create BSP at (0, 0)
    bsp = mcrfpy.BSP(pos=(0, 0), size=(20, 20))
    bsp.split_recursive(depth=2, min_size=(5, 5))

    # Create heightmap
    hmap = mcrfpy.HeightMap((50, 50), fill=0.0)

    # Map BSP to position (15, 15) in heightmap
    hmap.add_bsp(bsp, pos=(15, 15))

    # Verify: there should be values in the 15-35 region
    count_in_region = 0
    for x in range(15, 35):
        for y in range(15, 35):
            if hmap.get((x, y)) > 0:
                count_in_region += 1

    assert count_in_region > 0, "add_bsp() with pos=(15,15) should place BSP there"

    # Verify: the 0-15 region should be empty
    count_outside = 0
    for x in range(15):
        for y in range(15):
            if hmap.get((x, y)) > 0:
                count_outside += 1

    assert count_outside == 0, "Before pos offset should be empty"

    print("  PASS: add_bsp() with custom pos")


def test_multiply_bsp_pos():
    """Test multiply_bsp() with pos parameter for masking"""
    # Create BSP
    bsp = mcrfpy.BSP(pos=(0, 0), size=(30, 30))
    bsp.split_recursive(depth=2, min_size=(10, 10))

    # Create heightmap with uniform value
    hmap = mcrfpy.HeightMap((50, 50), fill=10.0)

    # Multiply/mask at position (10, 10) with shrink
    hmap.multiply_bsp(bsp, pos=(10, 10), shrink=2)

    # Check that areas outside the BSP+pos region are zeroed
    # At (5, 5) should be zeroed (before pos offset)
    assert hmap.get((5, 5)) == 0.0, "Before BSP region should be zeroed"

    # At (45, 45) should be zeroed (after BSP region)
    assert hmap.get((45, 45)) == 0.0, "After BSP region should be zeroed"

    # Inside the BSP region (accounting for pos and shrink), some should be preserved
    preserved_count = 0
    for x in range(10, 40):
        for y in range(10, 40):
            if hmap.get((x, y)) > 0:
                preserved_count += 1

    assert preserved_count > 0, "Inside BSP region should have some preserved values"

    print("  PASS: multiply_bsp() with pos")


# ============================================================================
# Error handling
# ============================================================================

def test_region_out_of_bounds():
    """Test that out-of-bounds positions raise ValueError"""
    hmap = mcrfpy.HeightMap((20, 20), fill=0.0)

    # Position beyond bounds
    try:
        hmap.fill(1.0, pos=(25, 25))
        print("  FAIL: Should raise ValueError for out-of-bounds pos")
        sys.exit(1)
    except ValueError:
        pass

    # Negative position
    try:
        hmap.fill(1.0, pos=(-1, 0))
        print("  FAIL: Should raise ValueError for negative pos")
        sys.exit(1)
    except ValueError:
        pass

    print("  PASS: Out-of-bounds position error handling")


def test_region_size_exceeds_bounds():
    """Test that explicit size exceeding bounds raises ValueError"""
    hmap = mcrfpy.HeightMap((20, 20), fill=0.0)

    # Size that exceeds remaining space
    try:
        hmap.fill(1.0, pos=(15, 15), size=(10, 10))
        print("  FAIL: Should raise ValueError when size exceeds bounds")
        sys.exit(1)
    except ValueError:
        pass

    print("  PASS: Size exceeds bounds error handling")


def test_source_region_out_of_bounds():
    """Test that out-of-bounds source_pos raises ValueError"""
    h1 = mcrfpy.HeightMap((20, 20), fill=0.0)
    h2 = mcrfpy.HeightMap((10, 10), fill=5.0)

    # source_pos beyond source bounds
    try:
        h1.add(h2, source_pos=(15, 15))
        print("  FAIL: Should raise ValueError for out-of-bounds source_pos")
        sys.exit(1)
    except ValueError:
        pass

    print("  PASS: Out-of-bounds source_pos error handling")


def test_method_chaining_with_regions():
    """Test that region operations support method chaining"""
    hmap = mcrfpy.HeightMap((30, 30), fill=0.0)

    # Chain multiple regional operations
    result = (hmap
        .fill(10.0, pos=(5, 5), size=(10, 10))
        .scale(2.0, pos=(5, 5), size=(10, 10))
        .add_constant(-5.0, pos=(5, 5), size=(10, 10)))

    assert result is hmap, "Chained operations should return self"

    # Verify: region should be 10*2-5 = 15, outside should be 0
    for x in range(30):
        for y in range(30):
            expected = 15.0 if (5 <= x < 15 and 5 <= y < 15) else 0.0
            actual = hmap.get((x, y))
            assert actual == expected, f"At ({x},{y}): expected {expected}, got {actual}"

    print("  PASS: Method chaining with regions")


# ============================================================================
# Run all tests
# ============================================================================

def run_tests():
    """Run all HeightMap region tests"""
    print("Testing HeightMap region operations...")

    # Scalar operations
    test_fill_region()
    test_fill_region_inferred_size()
    test_add_constant_region()
    test_scale_region()
    test_clamp_region()
    test_normalize_region()

    # Combination operations
    test_add_region()
    test_add_source_pos()
    test_copy_from_region()
    test_multiply_region()
    test_lerp_region()
    test_max_region()
    test_min_region()

    # BSP operations
    test_add_bsp_pos_default()
    test_add_bsp_pos_custom()
    test_multiply_bsp_pos()

    # Error handling
    test_region_out_of_bounds()
    test_region_size_exceeds_bounds()
    test_source_region_out_of_bounds()
    test_method_chaining_with_regions()

    print("All HeightMap region tests PASSED!")
    return True


if __name__ == "__main__":
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"FAIL: Unexpected exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
