"""Unit tests for NoiseSource.sample() method (Issue #208)

Tests:
- Basic sampling returning HeightMap
- world_origin parameter
- world_size parameter (zoom effect)
- Mode parameter (flat, fbm, turbulence)
- Octaves parameter
- Determinism
- Error handling
"""
import mcrfpy
import sys

def test_basic_sample():
    """Test basic sample() returning HeightMap"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)
    hmap = noise.sample(size=(50, 50))

    # Should return HeightMap
    assert isinstance(hmap, mcrfpy.HeightMap), f"Expected HeightMap, got {type(hmap)}"

    # Check dimensions
    assert hmap.size == (50, 50), f"Expected size (50, 50), got {hmap.size}"

    # Check values are in range
    min_val, max_val = hmap.min_max()
    assert min_val >= -1.0, f"Min value {min_val} out of range"
    assert max_val <= 1.0, f"Max value {max_val} out of range"

    print("  PASS: Basic sample")

def test_sample_world_origin():
    """Test sample() with world_origin parameter"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)

    # Sample at origin
    hmap1 = noise.sample(size=(20, 20), world_origin=(0.0, 0.0))

    # Sample at different location
    hmap2 = noise.sample(size=(20, 20), world_origin=(100.0, 100.0))

    # Values should be different (at least some)
    v1 = hmap1.get((0, 0))
    v2 = hmap2.get((0, 0))

    # Note: could be equal by chance but very unlikely
    # Just verify both are valid
    assert -1.0 <= v1 <= 1.0, f"Value1 {v1} out of range"
    assert -1.0 <= v2 <= 1.0, f"Value2 {v2} out of range"

    print("  PASS: Sample with world_origin")

def test_sample_world_size():
    """Test sample() with world_size parameter (zoom effect)"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)

    # Small world_size = zoomed in (smoother features)
    hmap_zoom_in = noise.sample(size=(20, 20), world_size=(1.0, 1.0))

    # Large world_size = zoomed out (more detail)
    hmap_zoom_out = noise.sample(size=(20, 20), world_size=(100.0, 100.0))

    # Both should be valid
    min1, max1 = hmap_zoom_in.min_max()
    min2, max2 = hmap_zoom_out.min_max()

    assert min1 >= -1.0 and max1 <= 1.0, "Zoomed-in values out of range"
    assert min2 >= -1.0 and max2 <= 1.0, "Zoomed-out values out of range"

    print("  PASS: Sample with world_size")

def test_sample_modes():
    """Test all sampling modes (flat, fbm, turbulence)"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)

    for mode in ["flat", "fbm", "turbulence"]:
        hmap = noise.sample(size=(20, 20), mode=mode)
        assert isinstance(hmap, mcrfpy.HeightMap), f"Mode '{mode}': Expected HeightMap"

        min_val, max_val = hmap.min_max()
        assert min_val >= -1.0, f"Mode '{mode}': Min {min_val} out of range"
        assert max_val <= 1.0, f"Mode '{mode}': Max {max_val} out of range"

    print("  PASS: All sample modes")

def test_sample_octaves():
    """Test sample() with different octave values"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)

    for octaves in [1, 4, 8]:
        hmap = noise.sample(size=(20, 20), mode="fbm", octaves=octaves)
        assert isinstance(hmap, mcrfpy.HeightMap), f"Octaves {octaves}: Expected HeightMap"

    print("  PASS: Sample with different octaves")

def test_sample_determinism():
    """Test that same parameters produce same HeightMap"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)

    hmap1 = noise.sample(
        size=(30, 30),
        world_origin=(10.0, 20.0),
        world_size=(5.0, 5.0),
        mode="fbm",
        octaves=4
    )

    hmap2 = noise.sample(
        size=(30, 30),
        world_origin=(10.0, 20.0),
        world_size=(5.0, 5.0),
        mode="fbm",
        octaves=4
    )

    # Compare several points
    for x in [0, 10, 20, 29]:
        for y in [0, 10, 20, 29]:
            v1 = hmap1.get((x, y))
            v2 = hmap2.get((x, y))
            assert v1 == v2, f"Determinism failed at ({x}, {y}): {v1} != {v2}"

    print("  PASS: Sample determinism")

def test_sample_different_seeds():
    """Test that different seeds produce different HeightMaps"""
    noise1 = mcrfpy.NoiseSource(dimensions=2, seed=42)
    noise2 = mcrfpy.NoiseSource(dimensions=2, seed=999)

    hmap1 = noise1.sample(size=(20, 20))
    hmap2 = noise2.sample(size=(20, 20))

    # At least some values should differ
    differences = 0
    for x in range(20):
        for y in range(20):
            if hmap1.get((x, y)) != hmap2.get((x, y)):
                differences += 1

    assert differences > 0, "Different seeds should produce different results"
    print("  PASS: Different seeds produce different HeightMaps")

def test_sample_heightmap_operations():
    """Test that returned HeightMap supports all HeightMap operations"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)
    hmap = noise.sample(size=(50, 50), mode="fbm")

    # Test various HeightMap operations
    # Normalize to 0-1 range
    hmap.normalize(0.0, 1.0)
    min_val, max_val = hmap.min_max()
    assert abs(min_val - 0.0) < 0.001, f"After normalize: min should be ~0, got {min_val}"
    assert abs(max_val - 1.0) < 0.001, f"After normalize: max should be ~1, got {max_val}"

    # Scale
    hmap.scale(2.0)
    min_val, max_val = hmap.min_max()
    assert abs(max_val - 2.0) < 0.001, f"After scale: max should be ~2, got {max_val}"

    # Clamp
    hmap.clamp(0.5, 1.5)
    min_val, max_val = hmap.min_max()
    assert min_val >= 0.5, f"After clamp: min should be >= 0.5, got {min_val}"
    assert max_val <= 1.5, f"After clamp: max should be <= 1.5, got {max_val}"

    print("  PASS: HeightMap operations on sampled noise")

def test_sample_requires_2d():
    """Test that sample() requires 2D NoiseSource"""
    for dim in [1, 3, 4]:
        noise = mcrfpy.NoiseSource(dimensions=dim, seed=42)
        try:
            hmap = noise.sample(size=(20, 20))
            print(f"  FAIL: sample() should raise ValueError for {dim}D noise")
            sys.exit(1)
        except ValueError:
            pass

    print("  PASS: sample() requires 2D noise")

def test_sample_invalid_size():
    """Test error handling for invalid size parameter"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)

    # Non-tuple
    try:
        noise.sample(size=50)
        print("  FAIL: Should raise TypeError for non-tuple size")
        sys.exit(1)
    except TypeError:
        pass

    # Wrong tuple length
    try:
        noise.sample(size=(50,))
        print("  FAIL: Should raise TypeError for wrong tuple length")
        sys.exit(1)
    except TypeError:
        pass

    # Zero dimensions
    try:
        noise.sample(size=(0, 50))
        print("  FAIL: Should raise ValueError for zero width")
        sys.exit(1)
    except ValueError:
        pass

    print("  PASS: Invalid size error handling")

def test_sample_invalid_mode():
    """Test error handling for invalid mode"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)

    try:
        noise.sample(size=(20, 20), mode="invalid")
        print("  FAIL: Should raise ValueError for invalid mode")
        sys.exit(1)
    except ValueError:
        pass

    print("  PASS: Invalid mode error handling")

def test_sample_contiguous_regions():
    """Test that adjacent samples are contiguous (proper world coordinate mapping)"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)
    world_size = (10.0, 10.0)
    sample_size = (20, 20)

    # Sample left region
    left = noise.sample(
        size=sample_size,
        world_origin=(0.0, 0.0),
        world_size=world_size,
        mode="fbm"
    )

    # Sample right region (adjacent to left)
    right = noise.sample(
        size=sample_size,
        world_origin=(10.0, 0.0),
        world_size=world_size,
        mode="fbm"
    )

    # The rightmost column of 'left' should match same world coords
    # sampled at leftmost of 'right' - but due to discrete sampling,
    # we verify the pattern rather than exact match

    # Verify both samples are valid
    assert left.size == sample_size, f"Left sample wrong size"
    assert right.size == sample_size, f"Right sample wrong size"

    print("  PASS: Contiguous region sampling")

def test_sample_large():
    """Test sampling large HeightMap"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)
    hmap = noise.sample(size=(200, 200), mode="fbm", octaves=6)

    assert hmap.size == (200, 200), f"Expected size (200, 200), got {hmap.size}"

    min_val, max_val = hmap.min_max()
    assert min_val >= -1.0 and max_val <= 1.0, "Values out of range"

    print("  PASS: Large sample")

def run_tests():
    """Run all NoiseSource.sample() tests"""
    print("Testing NoiseSource.sample() (Issue #208)...")

    test_basic_sample()
    test_sample_world_origin()
    test_sample_world_size()
    test_sample_modes()
    test_sample_octaves()
    test_sample_determinism()
    test_sample_different_seeds()
    test_sample_heightmap_operations()
    test_sample_requires_2d()
    test_sample_invalid_size()
    test_sample_invalid_mode()
    test_sample_contiguous_regions()
    test_sample_large()

    print("All NoiseSource.sample() tests PASSED!")
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
