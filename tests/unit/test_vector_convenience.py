#!/usr/bin/env python3
"""Unit tests for Vector convenience features (Issue #109)

Tests:
- Sequence protocol: indexing, negative indexing, iteration, unpacking
- Tuple comparison: Vector == tuple, Vector != tuple
- Integer conversion: .floor() method, .int property
- Boolean check: falsey for (0, 0)
"""

import mcrfpy
import sys

def approx(a, b, epsilon=1e-5):
    """Check if two floats are approximately equal (handles float32 precision)"""
    return abs(a - b) < epsilon

def test_indexing():
    """Test sequence protocol indexing"""
    # Use values that are exact in float32: 3.5 = 7/2, 7.5 = 15/2
    v = mcrfpy.Vector(3.5, 7.5)

    # Positive indices
    assert v[0] == 3.5, f"v[0] should be 3.5, got {v[0]}"
    assert v[1] == 7.5, f"v[1] should be 7.5, got {v[1]}"

    # Negative indices
    assert v[-1] == 7.5, f"v[-1] should be 7.5, got {v[-1]}"
    assert v[-2] == 3.5, f"v[-2] should be 3.5, got {v[-2]}"

    # Out of bounds
    try:
        _ = v[2]
        assert False, "v[2] should raise IndexError"
    except IndexError:
        pass

    try:
        _ = v[-3]
        assert False, "v[-3] should raise IndexError"
    except IndexError:
        pass

    print("  [PASS] Indexing")

def test_length():
    """Test len() on Vector"""
    v = mcrfpy.Vector(1, 2)
    assert len(v) == 2, f"len(Vector) should be 2, got {len(v)}"
    print("  [PASS] Length")

def test_iteration():
    """Test iteration and unpacking"""
    # Use values that are exact in float32
    v = mcrfpy.Vector(10.5, 20.5)

    # Iteration - use approximate comparison for float32 precision
    values = list(v)
    assert len(values) == 2, f"list(v) should have 2 elements"
    assert approx(values[0], 10.5), f"list(v)[0] should be ~10.5, got {values[0]}"
    assert approx(values[1], 20.5), f"list(v)[1] should be ~20.5, got {values[1]}"

    # Unpacking
    x, y = v
    assert approx(x, 10.5), f"Unpacked x should be ~10.5, got {x}"
    assert approx(y, 20.5), f"Unpacked y should be ~20.5, got {y}"

    # tuple() conversion
    t = tuple(v)
    assert len(t) == 2 and approx(t[0], 10.5) and approx(t[1], 20.5), f"tuple(v) should be ~(10.5, 20.5), got {t}"

    print("  [PASS] Iteration and unpacking")

def test_tuple_comparison():
    """Test comparison with tuples"""
    # Use integer values which are exact in float32
    v = mcrfpy.Vector(5, 6)

    # Vector == tuple (integers are exact)
    assert v == (5, 6), "Vector(5, 6) should equal (5, 6)"
    assert v == (5.0, 6.0), "Vector(5, 6) should equal (5.0, 6.0)"

    # Vector != tuple
    assert v != (5, 7), "Vector(5, 6) should not equal (5, 7)"
    assert v != (4, 6), "Vector(5, 6) should not equal (4, 6)"

    # Tuple == Vector (reverse comparison)
    assert (5, 6) == v, "(5, 6) should equal Vector(5, 6)"
    assert (5, 7) != v, "(5, 7) should not equal Vector(5, 6)"

    # Edge cases
    v_zero = mcrfpy.Vector(0, 0)
    assert v_zero == (0, 0), "Vector(0, 0) should equal (0, 0)"
    assert v_zero == (0.0, 0.0), "Vector(0, 0) should equal (0.0, 0.0)"

    # Negative values - use exact float32 values (x.5 are exact)
    v_neg = mcrfpy.Vector(-3.5, -7.5)
    assert v_neg == (-3.5, -7.5), "Vector(-3.5, -7.5) should equal (-3.5, -7.5)"

    print("  [PASS] Tuple comparison")

def test_floor_method():
    """Test .floor() method"""
    # Use values that clearly floor to different integers
    v = mcrfpy.Vector(3.75, -2.25)  # exact in float32
    floored = v.floor()

    assert isinstance(floored, mcrfpy.Vector), ".floor() should return a Vector"
    assert floored.x == 3.0, f"floor(3.75) should be 3.0, got {floored.x}"
    assert floored.y == -3.0, f"floor(-2.25) should be -3.0, got {floored.y}"

    # Positive values (use exact float32 values)
    v2 = mcrfpy.Vector(5.875, 0.125)  # exact in float32
    f2 = v2.floor()
    assert f2 == (5.0, 0.0), f"floor(5.875, 0.125) should be (5.0, 0.0), got ({f2.x}, {f2.y})"

    # Already integers
    v3 = mcrfpy.Vector(10.0, 20.0)
    f3 = v3.floor()
    assert f3 == (10.0, 20.0), f"floor(10.0, 20.0) should be (10.0, 20.0)"

    print("  [PASS] .floor() method")

def test_int_property():
    """Test .int property"""
    # Use exact float32 values
    v = mcrfpy.Vector(3.75, -2.25)
    int_tuple = v.int

    assert isinstance(int_tuple, tuple), ".int should return a tuple"
    assert len(int_tuple) == 2, ".int tuple should have 2 elements"
    assert int_tuple == (3, -3), f".int should be (3, -3), got {int_tuple}"

    # Check it's hashable (can be used as dict key)
    d = {}
    d[v.int] = "test"
    assert d[(3, -3)] == "test", ".int tuple should work as dict key"

    # Positive values (use exact float32 values)
    v2 = mcrfpy.Vector(5.875, 0.125)
    assert v2.int == (5, 0), f".int should be (5, 0), got {v2.int}"

    print("  [PASS] .int property")

def test_bool_check():
    """Test boolean conversion (already implemented, verify it works)"""
    v_zero = mcrfpy.Vector(0, 0)
    v_nonzero = mcrfpy.Vector(1, 0)
    v_nonzero2 = mcrfpy.Vector(0, 1)

    assert not bool(v_zero), "Vector(0, 0) should be falsey"
    assert bool(v_nonzero), "Vector(1, 0) should be truthy"
    assert bool(v_nonzero2), "Vector(0, 1) should be truthy"

    # In if statement
    if v_zero:
        assert False, "Vector(0, 0) should not pass if check"

    if not v_nonzero:
        assert False, "Vector(1, 0) should pass if check"

    print("  [PASS] Boolean check")

def test_combined_operations():
    """Test that new features work together with existing operations"""
    # Use exact float32 values
    v1 = mcrfpy.Vector(3.5, 4.5)
    v2 = mcrfpy.Vector(1.5, 2.5)

    # Arithmetic then tuple comparison (sums are exact)
    result = v1 + v2
    assert result == (5.0, 7.0), f"(3.5+1.5, 4.5+2.5) should equal (5.0, 7.0), got ({result.x}, {result.y})"

    # Floor then use as dict key
    floored = v1.floor()
    positions = {floored.int: "player"}
    assert (3, 4) in positions, "floored.int should work as dict key"

    # Unpack, modify, compare (products are exact)
    x, y = v1
    v3 = mcrfpy.Vector(x * 2, y * 2)
    assert v3 == (7.0, 9.0), f"Unpacking and creating new vector should work, got ({v3.x}, {v3.y})"

    print("  [PASS] Combined operations")

def run_tests():
    """Run all tests"""
    print("Testing Vector convenience features (Issue #109)...")

    test_indexing()
    test_length()
    test_iteration()
    test_tuple_comparison()
    test_floor_method()
    test_int_property()
    test_bool_check()
    test_combined_operations()

    print("\n[ALL TESTS PASSED]")
    sys.exit(0)

# Run tests immediately (no game loop needed)
run_tests()
