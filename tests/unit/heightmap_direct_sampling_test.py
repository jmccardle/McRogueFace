"""Unit tests for HeightMap direct source sampling (Issue #209)

Tests:
- add_noise() - sample noise and add to heightmap
- multiply_noise() - sample noise and multiply with heightmap
- add_bsp() - add BSP regions to heightmap
- multiply_bsp() - multiply by BSP regions (masking)
- Equivalence with intermediate HeightMap approach
- Error handling
"""
import mcrfpy
import sys

def test_add_noise_basic():
    """Test basic add_noise() operation"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)
    hmap = mcrfpy.HeightMap((50, 50), fill=0.0)

    result = hmap.add_noise(noise)

    # Should return self for chaining
    assert result is hmap, "add_noise() should return self"

    # Check that values have been modified
    min_val, max_val = hmap.min_max()
    assert max_val > 0 or min_val < 0, "Noise should add non-zero values"

    print("  PASS: add_noise() basic")

def test_add_noise_modes():
    """Test add_noise() with different modes"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)

    for mode in ["flat", "fbm", "turbulence"]:
        hmap = mcrfpy.HeightMap((30, 30), fill=0.0)
        hmap.add_noise(noise, mode=mode)

        min_val, max_val = hmap.min_max()
        assert min_val >= -2.0 and max_val <= 2.0, f"Mode '{mode}': values out of expected range"

    print("  PASS: add_noise() modes")

def test_add_noise_scale():
    """Test add_noise() with scale parameter"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)

    # Scale 0.5
    hmap1 = mcrfpy.HeightMap((30, 30), fill=0.0)
    hmap1.add_noise(noise, scale=0.5)
    min1, max1 = hmap1.min_max()

    # Scale 1.0
    hmap2 = mcrfpy.HeightMap((30, 30), fill=0.0)
    hmap2.add_noise(noise, scale=1.0)
    min2, max2 = hmap2.min_max()

    # Scale 0.5 should have smaller range
    range1 = max1 - min1
    range2 = max2 - min2
    assert range1 < range2 or abs(range1 - range2 * 0.5) < 0.1, "Scale should affect value range"

    print("  PASS: add_noise() scale")

def test_add_noise_equivalence():
    """Test that add_noise() produces same result as sample() + add()"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)

    # Method 1: Using sample() then add()
    hmap1 = mcrfpy.HeightMap((40, 40), fill=5.0)
    sampled = noise.sample(size=(40, 40), mode="fbm", octaves=4)
    hmap1.add(sampled)

    # Method 2: Using add_noise() directly
    hmap2 = mcrfpy.HeightMap((40, 40), fill=5.0)
    hmap2.add_noise(noise, mode="fbm", octaves=4)

    # Compare values - should be identical
    differences = 0
    for y in range(40):
        for x in range(40):
            v1 = hmap1.get((x, y))
            v2 = hmap2.get((x, y))
            if abs(v1 - v2) > 0.0001:
                differences += 1

    assert differences == 0, f"add_noise() should produce same result as sample()+add(), got {differences} differences"

    print("  PASS: add_noise() equivalence")

def test_multiply_noise_basic():
    """Test basic multiply_noise() operation"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)
    hmap = mcrfpy.HeightMap((50, 50), fill=1.0)

    result = hmap.multiply_noise(noise)

    assert result is hmap, "multiply_noise() should return self"

    # Values should now be in a range around 0 (noise * 1.0)
    min_val, max_val = hmap.min_max()
    # FBM noise ranges from ~-1 to ~1, so multiplied values should too
    assert min_val < 0.5, "multiply_noise() should produce values less than 0.5"

    print("  PASS: multiply_noise() basic")

def test_multiply_noise_scale():
    """Test multiply_noise() with scale parameter"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)

    # Start with values of 10
    hmap = mcrfpy.HeightMap((30, 30), fill=10.0)
    # Multiply by noise scaled to 0.5
    # Result should be 10 * (noise_value * 0.5)
    hmap.multiply_noise(noise, scale=0.5)

    min_val, max_val = hmap.min_max()
    # With scale 0.5, max possible is 10 * 0.5 = 5, min is 10 * -0.5 = -5
    assert max_val <= 6.0, f"Expected max <= 6.0, got {max_val}"

    print("  PASS: multiply_noise() scale")

def test_add_bsp_basic():
    """Test basic add_bsp() operation"""
    # Create BSP
    bsp = mcrfpy.BSP(pos=(0, 0), size=(50, 50))
    bsp.split_recursive(depth=3, min_size=(8, 8))

    # Create heightmap and add BSP
    hmap = mcrfpy.HeightMap((50, 50), fill=0.0)
    result = hmap.add_bsp(bsp)

    assert result is hmap, "add_bsp() should return self"

    # Check that some values are non-zero (inside rooms)
    min_val, max_val = hmap.min_max()
    assert max_val > 0, "add_bsp() should add non-zero values inside BSP regions"

    print("  PASS: add_bsp() basic")

def test_add_bsp_select_modes():
    """Test add_bsp() with different select modes"""
    bsp = mcrfpy.BSP(pos=(0, 0), size=(60, 60))
    bsp.split_recursive(depth=3, min_size=(10, 10))

    # Test leaves
    hmap_leaves = mcrfpy.HeightMap((60, 60), fill=0.0)
    hmap_leaves.add_bsp(bsp, select="leaves")

    # Test all
    hmap_all = mcrfpy.HeightMap((60, 60), fill=0.0)
    hmap_all.add_bsp(bsp, select="all")

    # Test internal
    hmap_internal = mcrfpy.HeightMap((60, 60), fill=0.0)
    hmap_internal.add_bsp(bsp, select="internal")

    # All modes should produce some non-zero values
    for name, hmap in [("leaves", hmap_leaves), ("all", hmap_all), ("internal", hmap_internal)]:
        min_val, max_val = hmap.min_max()
        assert max_val > 0, f"select='{name}' should produce non-zero values"

    # "all" should cover more area than just leaves or internal
    count_leaves = hmap_leaves.count_in_range((0.5, 2.0))
    count_all = hmap_all.count_in_range((0.5, 10.0))  # 'all' may overlap, so higher max
    count_internal = hmap_internal.count_in_range((0.5, 2.0))

    assert count_all >= count_leaves, "'all' should cover at least as much as 'leaves'"

    print("  PASS: add_bsp() select modes")

def test_add_bsp_shrink():
    """Test add_bsp() with shrink parameter"""
    bsp = mcrfpy.BSP(pos=(0, 0), size=(80, 80))
    bsp.split_recursive(depth=2, min_size=(20, 20))

    # Without shrink
    hmap1 = mcrfpy.HeightMap((80, 80), fill=0.0)
    hmap1.add_bsp(bsp, shrink=0)
    count1 = hmap1.count_in_range((0.5, 2.0))

    # With shrink
    hmap2 = mcrfpy.HeightMap((80, 80), fill=0.0)
    hmap2.add_bsp(bsp, shrink=2)
    count2 = hmap2.count_in_range((0.5, 2.0))

    # Shrunk version should have fewer cells
    assert count2 < count1, f"Shrink should reduce covered cells: {count2} vs {count1}"

    print("  PASS: add_bsp() shrink")

def test_add_bsp_value():
    """Test add_bsp() with custom value"""
    bsp = mcrfpy.BSP(pos=(0, 0), size=(40, 40))
    bsp.split_recursive(depth=2, min_size=(10, 10))

    hmap = mcrfpy.HeightMap((40, 40), fill=0.0)
    hmap.add_bsp(bsp, value=5.0)

    min_val, max_val = hmap.min_max()
    assert max_val == 5.0, f"Value parameter should set cell values to 5.0, got {max_val}"

    print("  PASS: add_bsp() value")

def test_multiply_bsp_basic():
    """Test basic multiply_bsp() operation (masking)"""
    bsp = mcrfpy.BSP(pos=(0, 0), size=(50, 50))
    bsp.split_recursive(depth=3, min_size=(8, 8))

    # Create heightmap with uniform value
    hmap = mcrfpy.HeightMap((50, 50), fill=10.0)
    result = hmap.multiply_bsp(bsp)

    assert result is hmap, "multiply_bsp() should return self"

    # Note: BSP leaves partition the ENTIRE space, so all cells are inside some leaf
    # To get "walls" between rooms, you need to use shrink > 0
    # Without shrink, all cells should be preserved
    min_val, max_val = hmap.min_max()
    assert max_val == 10.0, f"Areas inside BSP should be 10.0, got max={max_val}"

    # Test with shrink to get actual masking (walls between rooms)
    hmap2 = mcrfpy.HeightMap((50, 50), fill=10.0)
    hmap2.multiply_bsp(bsp, shrink=2)  # Leave 2-pixel walls

    min_val2, max_val2 = hmap2.min_max()
    assert min_val2 == 0.0, f"Areas between shrunken rooms should be 0, got min={min_val2}"
    assert max_val2 == 10.0, f"Areas inside shrunken rooms should be 10.0, got max={max_val2}"

    print("  PASS: multiply_bsp() basic (masking)")

def test_multiply_bsp_with_noise():
    """Test multiply_bsp() to mask noisy terrain"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)
    bsp = mcrfpy.BSP(pos=(0, 0), size=(80, 80))
    bsp.split_recursive(depth=3, min_size=(10, 10))

    # Generate noisy terrain
    hmap = mcrfpy.HeightMap((80, 80), fill=0.0)
    hmap.add_noise(noise, mode="fbm", octaves=6, scale=1.0)
    hmap.normalize(0.0, 1.0)

    # Mask to BSP regions
    hmap.multiply_bsp(bsp, select="leaves", shrink=1)

    # Check that some values are 0 (outside rooms) and some are positive (inside)
    count_zero = hmap.count_in_range((-0.001, 0.001))
    count_positive = hmap.count_in_range((0.1, 1.5))

    assert count_zero > 0, "Should have zero values outside BSP"
    assert count_positive > 0, "Should have positive values inside BSP"

    print("  PASS: multiply_bsp() with noise (terrain masking)")

def test_add_noise_requires_2d():
    """Test that add_noise() requires 2D NoiseSource"""
    for dim in [1, 3, 4]:
        noise = mcrfpy.NoiseSource(dimensions=dim, seed=42)
        hmap = mcrfpy.HeightMap((20, 20), fill=0.0)

        try:
            hmap.add_noise(noise)
            print(f"  FAIL: add_noise() should raise ValueError for {dim}D noise")
            sys.exit(1)
        except ValueError:
            pass

    print("  PASS: add_noise() requires 2D noise")

def test_type_errors():
    """Test type error handling"""
    hmap = mcrfpy.HeightMap((20, 20), fill=0.0)
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)

    # add_noise with non-NoiseSource
    try:
        hmap.add_noise("not a noise source")
        print("  FAIL: add_noise() should raise TypeError")
        sys.exit(1)
    except TypeError:
        pass

    # add_bsp with non-BSP
    try:
        hmap.add_bsp(noise)  # passing NoiseSource instead of BSP
        print("  FAIL: add_bsp() should raise TypeError")
        sys.exit(1)
    except TypeError:
        pass

    print("  PASS: Type error handling")

def test_invalid_select_mode():
    """Test invalid select mode error"""
    bsp = mcrfpy.BSP(pos=(0, 0), size=(30, 30))
    hmap = mcrfpy.HeightMap((30, 30), fill=0.0)

    try:
        hmap.add_bsp(bsp, select="invalid")
        print("  FAIL: add_bsp() should raise ValueError for invalid select")
        sys.exit(1)
    except ValueError:
        pass

    print("  PASS: Invalid select mode error")

def test_method_chaining():
    """Test method chaining with direct sampling"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)
    bsp = mcrfpy.BSP(pos=(0, 0), size=(60, 60))
    bsp.split_recursive(depth=2, min_size=(15, 15))

    hmap = mcrfpy.HeightMap((60, 60), fill=0.0)

    # Chain operations
    result = (hmap
        .add_noise(noise, mode="fbm", octaves=4)
        .normalize(0.0, 1.0)
        .multiply_bsp(bsp, select="leaves", shrink=1)
        .scale(10.0))

    assert result is hmap, "Chained operations should return self"

    # Verify the result makes sense
    min_val, max_val = hmap.min_max()
    assert min_val == 0.0, "Masked areas should be 0"
    assert max_val > 0.0, "Unmasked areas should have positive values"

    print("  PASS: Method chaining")

def run_tests():
    """Run all HeightMap direct sampling tests"""
    print("Testing HeightMap direct sampling (Issue #209)...")

    test_add_noise_basic()
    test_add_noise_modes()
    test_add_noise_scale()
    test_add_noise_equivalence()
    test_multiply_noise_basic()
    test_multiply_noise_scale()
    test_add_bsp_basic()
    test_add_bsp_select_modes()
    test_add_bsp_shrink()
    test_add_bsp_value()
    test_multiply_bsp_basic()
    test_multiply_bsp_with_noise()
    test_add_noise_requires_2d()
    test_type_errors()
    test_invalid_select_mode()
    test_method_chaining()

    print("All HeightMap direct sampling tests PASSED!")
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
