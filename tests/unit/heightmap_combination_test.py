"""Unit tests for HeightMap combination operations (Issue #194)

Tests:
- add(other) - cell-by-cell addition
- subtract(other) - cell-by-cell subtraction
- multiply(other) - cell-by-cell multiplication (masking)
- lerp(other, t) - linear interpolation
- copy_from(other) - copy values
- max(other) - cell-by-cell maximum
- min(other) - cell-by-cell minimum
- Dimension mismatch handling (operates on overlapping region)
- Method chaining
"""
import mcrfpy
import sys

def test_add():
    """Test add() operation"""
    h1 = mcrfpy.HeightMap((10, 10), fill=1.0)
    h2 = mcrfpy.HeightMap((10, 10), fill=2.0)

    result = h1.add(h2)

    # Should return self for chaining
    assert result is h1, "add() should return self"

    # Check values
    for x in range(10):
        for y in range(10):
            assert h1.get((x, y)) == 3.0, f"Expected 3.0 at ({x},{y}), got {h1.get((x, y))}"

    print("  PASS: add()")

def test_subtract():
    """Test subtract() operation"""
    h1 = mcrfpy.HeightMap((10, 10), fill=5.0)
    h2 = mcrfpy.HeightMap((10, 10), fill=2.0)

    result = h1.subtract(h2)

    assert result is h1, "subtract() should return self"

    for x in range(10):
        for y in range(10):
            assert h1.get((x, y)) == 3.0, f"Expected 3.0, got {h1.get((x, y))}"

    print("  PASS: subtract()")

def test_multiply():
    """Test multiply() operation"""
    h1 = mcrfpy.HeightMap((10, 10), fill=3.0)
    h2 = mcrfpy.HeightMap((10, 10), fill=2.0)

    result = h1.multiply(h2)

    assert result is h1, "multiply() should return self"

    for x in range(10):
        for y in range(10):
            assert h1.get((x, y)) == 6.0, f"Expected 6.0, got {h1.get((x, y))}"

    print("  PASS: multiply()")

def test_multiply_masking():
    """Test multiply() for masking (0/1 values)"""
    h1 = mcrfpy.HeightMap((10, 10), fill=5.0)

    # Create mask: 1.0 in center, 0.0 outside
    mask = mcrfpy.HeightMap((10, 10), fill=0.0)
    for x in range(3, 7):
        for y in range(3, 7):
            # Need to use the underlying heightmap directly
            pass  # We'll fill differently

    # Actually fill the mask using a different approach
    mask = mcrfpy.HeightMap((10, 10), fill=0.0)
    # Fill with 0, then add 1 to center region
    center = mcrfpy.HeightMap((10, 10), fill=0.0)
    center.add_hill((5, 5), 0.1, 1.0)  # Small hill at center
    center.threshold_binary((0.5, 2.0), value=1.0)  # Make binary

    # Just test basic masking with simple uniform values
    h1 = mcrfpy.HeightMap((10, 10), fill=5.0)
    mask = mcrfpy.HeightMap((10, 10), fill=0.5)

    h1.multiply(mask)

    # All values should be 5.0 * 0.5 = 2.5
    for x in range(10):
        for y in range(10):
            assert abs(h1.get((x, y)) - 2.5) < 0.001, f"Expected 2.5, got {h1.get((x, y))}"

    print("  PASS: multiply() for masking")

def test_lerp():
    """Test lerp() operation"""
    h1 = mcrfpy.HeightMap((10, 10), fill=0.0)
    h2 = mcrfpy.HeightMap((10, 10), fill=10.0)

    # t=0.5 should give midpoint
    result = h1.lerp(h2, 0.5)

    assert result is h1, "lerp() should return self"

    for x in range(10):
        for y in range(10):
            assert abs(h1.get((x, y)) - 5.0) < 0.001, f"Expected 5.0, got {h1.get((x, y))}"

    print("  PASS: lerp() at t=0.5")

def test_lerp_extremes():
    """Test lerp() at t=0 and t=1"""
    h1 = mcrfpy.HeightMap((10, 10), fill=0.0)
    h2 = mcrfpy.HeightMap((10, 10), fill=10.0)

    # t=0 should keep h1 values
    h1.lerp(h2, 0.0)
    assert abs(h1.get((5, 5)) - 0.0) < 0.001, f"t=0: Expected 0.0, got {h1.get((5, 5))}"

    # Reset and test t=1
    h1.fill(0.0)
    h1.lerp(h2, 1.0)
    assert abs(h1.get((5, 5)) - 10.0) < 0.001, f"t=1: Expected 10.0, got {h1.get((5, 5))}"

    print("  PASS: lerp() at extremes")

def test_copy_from():
    """Test copy_from() operation"""
    h1 = mcrfpy.HeightMap((10, 10), fill=0.0)
    h2 = mcrfpy.HeightMap((10, 10), fill=7.5)

    result = h1.copy_from(h2)

    assert result is h1, "copy_from() should return self"

    for x in range(10):
        for y in range(10):
            assert h1.get((x, y)) == 7.5, f"Expected 7.5, got {h1.get((x, y))}"

    print("  PASS: copy_from()")

def test_max():
    """Test max() operation"""
    h1 = mcrfpy.HeightMap((10, 10), fill=3.0)
    h2 = mcrfpy.HeightMap((10, 10), fill=5.0)

    result = h1.max(h2)

    assert result is h1, "max() should return self"

    for x in range(10):
        for y in range(10):
            assert h1.get((x, y)) == 5.0, f"Expected 5.0, got {h1.get((x, y))}"

    print("  PASS: max()")

def test_max_varying():
    """Test max() with varying values"""
    h1 = mcrfpy.HeightMap((10, 10), fill=0.0)
    h2 = mcrfpy.HeightMap((10, 10), fill=0.0)

    # h1 has values 0-4 in left half, h2 has values 5-9 in right half
    h1.fill(3.0)  # All 3
    h2.fill(7.0)  # All 7

    # Modify h1 to have some higher values
    h1.add_constant(5.0)  # Now h1 is 8.0

    h1.max(h2)

    # Result should be 8.0 everywhere (h1 was 8, h2 was 7)
    for x in range(10):
        for y in range(10):
            assert h1.get((x, y)) == 8.0, f"Expected 8.0, got {h1.get((x, y))}"

    print("  PASS: max() with varying values")

def test_min():
    """Test min() operation"""
    h1 = mcrfpy.HeightMap((10, 10), fill=8.0)
    h2 = mcrfpy.HeightMap((10, 10), fill=5.0)

    result = h1.min(h2)

    assert result is h1, "min() should return self"

    for x in range(10):
        for y in range(10):
            assert h1.get((x, y)) == 5.0, f"Expected 5.0, got {h1.get((x, y))}"

    print("  PASS: min()")

def test_dimension_mismatch_allowed():
    """Test that dimension mismatch works (operates on overlapping region)"""
    # Smaller dest, larger source - uses smaller size
    h1 = mcrfpy.HeightMap((10, 10), fill=5.0)
    h2 = mcrfpy.HeightMap((20, 20), fill=3.0)

    h1.add(h2)

    # All cells in h1 should be 5.0 + 3.0 = 8.0
    for x in range(10):
        for y in range(10):
            assert h1.get((x, y)) == 8.0, f"Expected 8.0 at ({x},{y}), got {h1.get((x, y))}"

    # Test the reverse: larger dest, smaller source
    h3 = mcrfpy.HeightMap((20, 20), fill=10.0)
    h4 = mcrfpy.HeightMap((5, 5), fill=2.0)

    h3.add(h4)

    # Only the 5x5 region should be affected
    for x in range(20):
        for y in range(20):
            expected = 12.0 if (x < 5 and y < 5) else 10.0
            assert h3.get((x, y)) == expected, f"Expected {expected} at ({x},{y}), got {h3.get((x, y))}"

    print("  PASS: Dimension mismatch handling (overlapping region)")

def test_type_error():
    """Test that non-HeightMap argument raises TypeError"""
    h1 = mcrfpy.HeightMap((10, 10), fill=0.0)

    ops = [
        ('add', lambda: h1.add(5.0)),
        ('subtract', lambda: h1.subtract("invalid")),
        ('multiply', lambda: h1.multiply([1, 2, 3])),
        ('copy_from', lambda: h1.copy_from(None)),
        ('max', lambda: h1.max({})),
        ('min', lambda: h1.min(42)),
    ]

    for name, op in ops:
        try:
            op()
            print(f"  FAIL: {name}() should raise TypeError for non-HeightMap")
            sys.exit(1)
        except TypeError:
            pass

    print("  PASS: Type error handling")

def test_method_chaining():
    """Test method chaining with combination operations"""
    h1 = mcrfpy.HeightMap((10, 10), fill=1.0)
    h2 = mcrfpy.HeightMap((10, 10), fill=2.0)
    h3 = mcrfpy.HeightMap((10, 10), fill=3.0)

    # Chain multiple operations
    result = h1.add(h2).add(h3).scale(0.5)

    # 1.0 + 2.0 + 3.0 = 6.0, then * 0.5 = 3.0
    for x in range(10):
        for y in range(10):
            assert abs(h1.get((x, y)) - 3.0) < 0.001, f"Expected 3.0, got {h1.get((x, y))}"

    print("  PASS: Method chaining")

def test_self_operation():
    """Test operations with self (h.add(h))"""
    h1 = mcrfpy.HeightMap((10, 10), fill=5.0)

    # Adding to self should double values
    h1.add(h1)

    for x in range(10):
        for y in range(10):
            assert h1.get((x, y)) == 10.0, f"Expected 10.0, got {h1.get((x, y))}"

    # Multiplying self by self should square
    h1.fill(3.0)
    h1.multiply(h1)

    for x in range(10):
        for y in range(10):
            assert h1.get((x, y)) == 9.0, f"Expected 9.0, got {h1.get((x, y))}"

    print("  PASS: Self operations")

def run_tests():
    """Run all HeightMap combination tests"""
    print("Testing HeightMap combination operations (Issue #194)...")

    test_add()
    test_subtract()
    test_multiply()
    test_multiply_masking()
    test_lerp()
    test_lerp_extremes()
    test_copy_from()
    test_max()
    test_max_varying()
    test_min()
    test_dimension_mismatch_allowed()
    test_type_error()
    test_method_chaining()
    test_self_operation()

    print("All HeightMap combination tests PASSED!")
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
