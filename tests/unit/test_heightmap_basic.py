#!/usr/bin/env python3
"""Unit tests for mcrfpy.HeightMap core functionality (#193)

Tests the HeightMap class constructor, size property, and scalar operations.
"""

import sys
import mcrfpy


def test_constructor_basic():
    """HeightMap can be created with a size tuple"""
    hmap = mcrfpy.HeightMap((100, 50))
    assert hmap is not None
    print("PASS: test_constructor_basic")


def test_constructor_with_fill():
    """HeightMap can be created with a fill value"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    assert hmap is not None
    print("PASS: test_constructor_with_fill")


def test_size_property():
    """size property returns correct dimensions"""
    hmap = mcrfpy.HeightMap((100, 50))
    size = hmap.size
    assert size == (100, 50), f"Expected (100, 50), got {size}"
    print("PASS: test_size_property")


def test_size_immutable():
    """size property is read-only"""
    hmap = mcrfpy.HeightMap((100, 50))
    try:
        hmap.size = (200, 100)
        print("FAIL: test_size_immutable - should have raised AttributeError")
        sys.exit(1)
    except AttributeError:
        pass
    print("PASS: test_size_immutable")


def test_fill_method():
    """fill() sets all cells and returns self"""
    hmap = mcrfpy.HeightMap((10, 10))
    result = hmap.fill(0.5)
    assert result is hmap, "fill() should return self"
    print("PASS: test_fill_method")


def test_clear_method():
    """clear() sets all cells to 0.0 and returns self"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    result = hmap.clear()
    assert result is hmap, "clear() should return self"
    print("PASS: test_clear_method")


def test_add_constant_method():
    """add_constant() adds to all cells and returns self"""
    hmap = mcrfpy.HeightMap((10, 10))
    result = hmap.add_constant(0.25)
    assert result is hmap, "add_constant() should return self"
    print("PASS: test_add_constant_method")


def test_scale_method():
    """scale() multiplies all cells and returns self"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    result = hmap.scale(2.0)
    assert result is hmap, "scale() should return self"
    print("PASS: test_scale_method")


def test_clamp_method():
    """clamp() clamps values and returns self"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    result = hmap.clamp(0.0, 1.0)
    assert result is hmap, "clamp() should return self"
    print("PASS: test_clamp_method")


def test_clamp_with_defaults():
    """clamp() works with default parameters"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    result = hmap.clamp()  # Uses defaults 0.0, 1.0
    assert result is hmap
    print("PASS: test_clamp_with_defaults")


def test_normalize_method():
    """normalize() rescales values and returns self"""
    hmap = mcrfpy.HeightMap((10, 10))
    hmap.fill(0.25).add_constant(0.1)  # Some values
    result = hmap.normalize(0.0, 1.0)
    assert result is hmap, "normalize() should return self"
    print("PASS: test_normalize_method")


def test_normalize_with_defaults():
    """normalize() works with default parameters"""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)
    result = hmap.normalize()  # Uses defaults 0.0, 1.0
    assert result is hmap
    print("PASS: test_normalize_with_defaults")


def test_method_chaining():
    """Methods can be chained"""
    hmap = mcrfpy.HeightMap((10, 10))
    result = hmap.fill(0.5).scale(2.0).clamp(0.0, 1.0)
    assert result is hmap, "Chained methods should return self"
    print("PASS: test_method_chaining")


def test_complex_chaining():
    """Complex chains work correctly"""
    hmap = mcrfpy.HeightMap((100, 100))
    result = (hmap
              .fill(0.0)
              .add_constant(0.5)
              .scale(1.5)
              .clamp(0.0, 1.0)
              .normalize(0.2, 0.8))
    assert result is hmap
    print("PASS: test_complex_chaining")


def test_repr():
    """repr() returns a readable string"""
    hmap = mcrfpy.HeightMap((100, 50))
    r = repr(hmap)
    assert "HeightMap" in r
    assert "100" in r and "50" in r
    print(f"PASS: test_repr - {r}")


def test_invalid_size():
    """Negative or zero size raises ValueError"""
    try:
        mcrfpy.HeightMap((0, 10))
        print("FAIL: test_invalid_size - should have raised ValueError for width=0")
        sys.exit(1)
    except ValueError:
        pass

    try:
        mcrfpy.HeightMap((10, -5))
        print("FAIL: test_invalid_size - should have raised ValueError for height=-5")
        sys.exit(1)
    except ValueError:
        pass

    print("PASS: test_invalid_size")


def test_invalid_size_type():
    """Non-tuple size raises TypeError"""
    try:
        mcrfpy.HeightMap([100, 50])  # list instead of tuple
        print("FAIL: test_invalid_size_type - should have raised TypeError")
        sys.exit(1)
    except TypeError:
        pass
    print("PASS: test_invalid_size_type")


def run_all_tests():
    """Run all tests"""
    print("Running HeightMap basic tests...")
    print()

    test_constructor_basic()
    test_constructor_with_fill()
    test_size_property()
    test_size_immutable()
    test_fill_method()
    test_clear_method()
    test_add_constant_method()
    test_scale_method()
    test_clamp_method()
    test_clamp_with_defaults()
    test_normalize_method()
    test_normalize_with_defaults()
    test_method_chaining()
    test_complex_chaining()
    test_repr()
    test_invalid_size()
    test_invalid_size_type()

    print()
    print("All HeightMap basic tests PASSED!")


# Run tests directly
run_all_tests()
sys.exit(0)
