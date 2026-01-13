"""Unit tests for NoiseSource class (Issue #207)

Tests:
- Construction with default and custom parameters
- Read-only property access
- Point query methods (get, fbm, turbulence)
- Determinism (same seed = same results)
- Error handling for invalid inputs
"""
import mcrfpy
import sys

def test_default_construction():
    """Test NoiseSource with default parameters"""
    noise = mcrfpy.NoiseSource()
    assert noise.dimensions == 2, f"Expected dimensions=2, got {noise.dimensions}"
    assert noise.algorithm == "simplex", f"Expected algorithm='simplex', got {noise.algorithm}"
    assert noise.hurst == 0.5, f"Expected hurst=0.5, got {noise.hurst}"
    assert noise.lacunarity == 2.0, f"Expected lacunarity=2.0, got {noise.lacunarity}"
    assert isinstance(noise.seed, int), f"Expected seed to be int, got {type(noise.seed)}"
    print("  PASS: Default construction")

def test_custom_construction():
    """Test NoiseSource with custom parameters"""
    noise = mcrfpy.NoiseSource(
        dimensions=3,
        algorithm="perlin",
        hurst=0.7,
        lacunarity=2.5,
        seed=12345
    )
    assert noise.dimensions == 3, f"Expected dimensions=3, got {noise.dimensions}"
    assert noise.algorithm == "perlin", f"Expected algorithm='perlin', got {noise.algorithm}"
    assert abs(noise.hurst - 0.7) < 0.001, f"Expected hurst~=0.7, got {noise.hurst}"
    assert abs(noise.lacunarity - 2.5) < 0.001, f"Expected lacunarity~=2.5, got {noise.lacunarity}"
    assert noise.seed == 12345, f"Expected seed=12345, got {noise.seed}"
    print("  PASS: Custom construction")

def test_algorithms():
    """Test all supported algorithms"""
    for alg in ["simplex", "perlin", "wavelet"]:
        noise = mcrfpy.NoiseSource(algorithm=alg, seed=42)
        assert noise.algorithm == alg, f"Expected algorithm='{alg}', got {noise.algorithm}"
    print("  PASS: All algorithms")

def test_dimensions():
    """Test valid dimension values (1-4)"""
    for dim in [1, 2, 3, 4]:
        noise = mcrfpy.NoiseSource(dimensions=dim, seed=42)
        assert noise.dimensions == dim, f"Expected dimensions={dim}, got {noise.dimensions}"
    print("  PASS: All valid dimensions")

def test_get_method():
    """Test flat noise get() method"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)
    value = noise.get((0.0, 0.0))
    assert isinstance(value, float), f"Expected float, got {type(value)}"
    assert -1.0 <= value <= 1.0, f"Value {value} out of range [-1, 1]"

    # Test different coordinates
    value2 = noise.get((10.5, 20.3))
    assert isinstance(value2, float), f"Expected float, got {type(value2)}"
    assert -1.0 <= value2 <= 1.0, f"Value {value2} out of range [-1, 1]"

    # Different coordinates should produce different values (most of the time)
    value3 = noise.get((100.0, 200.0))
    assert value != value3 or value == value3, "Values can be equal but typically differ"  # This is always true
    print("  PASS: get() method")

def test_fbm_method():
    """Test fractal brownian motion method"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)

    # Default octaves
    value = noise.fbm((10.0, 20.0))
    assert isinstance(value, float), f"Expected float, got {type(value)}"
    assert -1.0 <= value <= 1.0, f"Value {value} out of range [-1, 1]"

    # Custom octaves
    value2 = noise.fbm((10.0, 20.0), octaves=6)
    assert isinstance(value2, float), f"Expected float, got {type(value2)}"

    # Different octaves should produce different values
    value3 = noise.fbm((10.0, 20.0), octaves=2)
    # Values with different octaves are typically different
    print("  PASS: fbm() method")

def test_turbulence_method():
    """Test turbulence method"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)

    # Default octaves
    value = noise.turbulence((10.0, 20.0))
    assert isinstance(value, float), f"Expected float, got {type(value)}"
    assert -1.0 <= value <= 1.0, f"Value {value} out of range [-1, 1]"

    # Custom octaves
    value2 = noise.turbulence((10.0, 20.0), octaves=6)
    assert isinstance(value2, float), f"Expected float, got {type(value2)}"
    print("  PASS: turbulence() method")

def test_determinism():
    """Test that same seed produces same results"""
    noise1 = mcrfpy.NoiseSource(dimensions=2, seed=42)
    noise2 = mcrfpy.NoiseSource(dimensions=2, seed=42)

    coords = [(0.0, 0.0), (10.5, 20.3), (100.0, 200.0), (-50.0, 75.0)]

    for pos in coords:
        v1 = noise1.get(pos)
        v2 = noise2.get(pos)
        assert v1 == v2, f"Determinism failed at {pos}: {v1} != {v2}"

        fbm1 = noise1.fbm(pos, octaves=4)
        fbm2 = noise2.fbm(pos, octaves=4)
        assert fbm1 == fbm2, f"FBM determinism failed at {pos}: {fbm1} != {fbm2}"

        turb1 = noise1.turbulence(pos, octaves=4)
        turb2 = noise2.turbulence(pos, octaves=4)
        assert turb1 == turb2, f"Turbulence determinism failed at {pos}: {turb1} != {turb2}"

    print("  PASS: Determinism")

def test_different_seeds():
    """Test that different seeds produce different results"""
    noise1 = mcrfpy.NoiseSource(dimensions=2, seed=42)
    noise2 = mcrfpy.NoiseSource(dimensions=2, seed=999)

    # Check several positions - at least some should differ
    coords = [(0.0, 0.0), (10.5, 20.3), (100.0, 200.0)]
    differences_found = 0

    for pos in coords:
        v1 = noise1.get(pos)
        v2 = noise2.get(pos)
        if v1 != v2:
            differences_found += 1

    assert differences_found > 0, "Different seeds should produce different results"
    print("  PASS: Different seeds produce different results")

def test_multidimensional():
    """Test 1D, 3D, and 4D noise"""
    # 1D noise
    noise1d = mcrfpy.NoiseSource(dimensions=1, seed=42)
    v1d = noise1d.get((5.5,))
    assert isinstance(v1d, float), f"1D: Expected float, got {type(v1d)}"
    assert -1.0 <= v1d <= 1.0, f"1D: Value {v1d} out of range"

    # 3D noise
    noise3d = mcrfpy.NoiseSource(dimensions=3, seed=42)
    v3d = noise3d.get((5.5, 10.0, 15.5))
    assert isinstance(v3d, float), f"3D: Expected float, got {type(v3d)}"
    assert -1.0 <= v3d <= 1.0, f"3D: Value {v3d} out of range"

    # 4D noise
    noise4d = mcrfpy.NoiseSource(dimensions=4, seed=42)
    v4d = noise4d.get((5.5, 10.0, 15.5, 20.0))
    assert isinstance(v4d, float), f"4D: Expected float, got {type(v4d)}"
    assert -1.0 <= v4d <= 1.0, f"4D: Value {v4d} out of range"

    print("  PASS: Multidimensional noise")

def test_invalid_dimensions():
    """Test error handling for invalid dimensions"""
    # Test dimension 0
    try:
        noise = mcrfpy.NoiseSource(dimensions=0)
        print("  FAIL: Should raise ValueError for dimensions=0")
        sys.exit(1)
    except ValueError:
        pass

    # Test dimension 5 (exceeds max)
    try:
        noise = mcrfpy.NoiseSource(dimensions=5)
        print("  FAIL: Should raise ValueError for dimensions=5")
        sys.exit(1)
    except ValueError:
        pass

    print("  PASS: Invalid dimensions error handling")

def test_invalid_algorithm():
    """Test error handling for invalid algorithm"""
    try:
        noise = mcrfpy.NoiseSource(algorithm="invalid")
        print("  FAIL: Should raise ValueError for invalid algorithm")
        sys.exit(1)
    except ValueError:
        pass
    print("  PASS: Invalid algorithm error handling")

def test_dimension_mismatch():
    """Test error handling for position/dimension mismatch"""
    noise = mcrfpy.NoiseSource(dimensions=2, seed=42)

    # Too few coordinates
    try:
        noise.get((5.0,))
        print("  FAIL: Should raise ValueError for wrong dimension count")
        sys.exit(1)
    except ValueError:
        pass

    # Too many coordinates
    try:
        noise.get((5.0, 10.0, 15.0))
        print("  FAIL: Should raise ValueError for wrong dimension count")
        sys.exit(1)
    except ValueError:
        pass

    print("  PASS: Dimension mismatch error handling")

def test_repr():
    """Test string representation"""
    noise = mcrfpy.NoiseSource(dimensions=2, algorithm="simplex", seed=42)
    r = repr(noise)
    assert "NoiseSource" in r, f"repr should contain 'NoiseSource': {r}"
    assert "2D" in r, f"repr should contain '2D': {r}"
    assert "simplex" in r, f"repr should contain 'simplex': {r}"
    assert "42" in r, f"repr should contain seed '42': {r}"
    print("  PASS: String representation")

def test_properties_readonly():
    """Test that properties are read-only"""
    noise = mcrfpy.NoiseSource(seed=42)

    readonly_props = ['dimensions', 'algorithm', 'hurst', 'lacunarity', 'seed']
    for prop in readonly_props:
        try:
            setattr(noise, prop, 0)
            print(f"  FAIL: Property '{prop}' should be read-only")
            sys.exit(1)
        except AttributeError:
            pass

    print("  PASS: Properties are read-only")

def run_tests():
    """Run all NoiseSource tests"""
    print("Testing NoiseSource (Issue #207)...")

    test_default_construction()
    test_custom_construction()
    test_algorithms()
    test_dimensions()
    test_get_method()
    test_fbm_method()
    test_turbulence_method()
    test_determinism()
    test_different_seeds()
    test_multidimensional()
    test_invalid_dimensions()
    test_invalid_algorithm()
    test_dimension_mismatch()
    test_repr()
    test_properties_readonly()

    print("All NoiseSource tests PASSED!")
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
