#!/usr/bin/env python3
"""Unit tests for DiscreteMap basic operations."""

import mcrfpy
import sys

def test_construction():
    """Test basic construction."""
    # Default construction
    dmap = mcrfpy.DiscreteMap((100, 100))
    assert dmap.size == (100, 100), f"Expected (100, 100), got {dmap.size}"

    # With fill value
    dmap2 = mcrfpy.DiscreteMap((50, 50), fill=42)
    assert dmap2[0, 0] == 42, f"Expected 42, got {dmap2[0, 0]}"
    assert dmap2[25, 25] == 42, f"Expected 42, got {dmap2[25, 25]}"

    print("  [PASS] Construction")

def test_size_property():
    """Test size property."""
    dmap = mcrfpy.DiscreteMap((123, 456))
    w, h = dmap.size
    assert w == 123, f"Expected width 123, got {w}"
    assert h == 456, f"Expected height 456, got {h}"
    print("  [PASS] Size property")

def test_get_set():
    """Test get/set methods."""
    dmap = mcrfpy.DiscreteMap((10, 10))

    # Test set/get
    dmap.set(5, 5, 100)
    assert dmap.get(5, 5) == 100, f"Expected 100, got {dmap.get(5, 5)}"

    # Test subscript
    dmap[3, 7] = 200
    assert dmap[3, 7] == 200, f"Expected 200, got {dmap[3, 7]}"

    # Test tuple subscript
    dmap[(1, 2)] = 150
    assert dmap[(1, 2)] == 150, f"Expected 150, got {dmap[(1, 2)]}"

    print("  [PASS] Get/set methods")

def test_bounds_checking():
    """Test that out-of-bounds access raises IndexError."""
    dmap = mcrfpy.DiscreteMap((10, 10))

    # Test out of bounds get
    try:
        _ = dmap[10, 10]
        print("  [FAIL] Should have raised IndexError for (10, 10)")
        return False
    except IndexError:
        pass

    try:
        _ = dmap[-1, 0]
        print("  [FAIL] Should have raised IndexError for (-1, 0)")
        return False
    except IndexError:
        pass

    # Test out of bounds set
    try:
        dmap[100, 100] = 5
        print("  [FAIL] Should have raised IndexError for set")
        return False
    except IndexError:
        pass

    print("  [PASS] Bounds checking")
    return True

def test_value_range():
    """Test that values are clamped to 0-255."""
    dmap = mcrfpy.DiscreteMap((10, 10))

    # Test valid range
    dmap[0, 0] = 0
    dmap[0, 1] = 255
    assert dmap[0, 0] == 0
    assert dmap[0, 1] == 255

    # Test invalid values
    try:
        dmap[0, 0] = -1
        print("  [FAIL] Should have raised ValueError for -1")
        return False
    except ValueError:
        pass

    try:
        dmap[0, 0] = 256
        print("  [FAIL] Should have raised ValueError for 256")
        return False
    except ValueError:
        pass

    print("  [PASS] Value range")
    return True

def test_fill():
    """Test fill operation."""
    dmap = mcrfpy.DiscreteMap((10, 10))

    # Fill entire map
    dmap.fill(77)
    for y in range(10):
        for x in range(10):
            assert dmap[x, y] == 77, f"Expected 77 at ({x}, {y}), got {dmap[x, y]}"

    # Fill region
    dmap.fill(88, pos=(2, 2), size=(3, 3))
    assert dmap[2, 2] == 88, "Region fill failed at start"
    assert dmap[4, 4] == 88, "Region fill failed at end"
    assert dmap[1, 1] == 77, "Region fill affected outside area"
    assert dmap[5, 5] == 77, "Region fill affected outside area"

    print("  [PASS] Fill operation")

def test_clear():
    """Test clear operation."""
    dmap = mcrfpy.DiscreteMap((10, 10), fill=100)
    dmap.clear()

    for y in range(10):
        for x in range(10):
            assert dmap[x, y] == 0, f"Expected 0 at ({x}, {y}), got {dmap[x, y]}"

    print("  [PASS] Clear operation")

def test_repr():
    """Test repr output."""
    dmap = mcrfpy.DiscreteMap((100, 50))
    r = repr(dmap)
    assert "DiscreteMap" in r, f"Expected 'DiscreteMap' in repr, got {r}"
    assert "100" in r, f"Expected '100' in repr, got {r}"
    assert "50" in r, f"Expected '50' in repr, got {r}"
    print("  [PASS] Repr")

def test_chaining():
    """Test method chaining."""
    dmap = mcrfpy.DiscreteMap((10, 10))

    # Methods should return self
    result = dmap.fill(50).clear().fill(100)
    assert result is dmap, "Method chaining should return self"
    assert dmap[5, 5] == 100, "Chained operations should work"

    print("  [PASS] Method chaining")

def main():
    print("Running DiscreteMap basic tests...")

    test_construction()
    test_size_property()
    test_get_set()
    if not test_bounds_checking():
        sys.exit(1)
    if not test_value_range():
        sys.exit(1)
    test_fill()
    test_clear()
    test_repr()
    test_chaining()

    print("All DiscreteMap basic tests PASSED!")
    sys.exit(0)

if __name__ == "__main__":
    main()
