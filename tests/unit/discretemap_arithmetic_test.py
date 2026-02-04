#!/usr/bin/env python3
"""Unit tests for DiscreteMap arithmetic and bitwise operations."""

import mcrfpy
import sys

def test_add_scalar():
    """Test adding a scalar value."""
    dmap = mcrfpy.DiscreteMap((10, 10), fill=50)
    dmap.add(25)
    assert dmap[5, 5] == 75, f"Expected 75, got {dmap[5, 5]}"

    # Test saturation at 255
    dmap.fill(250)
    dmap.add(20)  # 250 + 20 = 270 -> saturates to 255
    assert dmap[0, 0] == 255, f"Expected 255 (saturated), got {dmap[0, 0]}"

    print("  [PASS] Add scalar")

def test_add_map():
    """Test adding another DiscreteMap."""
    dmap1 = mcrfpy.DiscreteMap((10, 10), fill=50)
    dmap2 = mcrfpy.DiscreteMap((10, 10), fill=30)

    dmap1.add(dmap2)
    assert dmap1[5, 5] == 80, f"Expected 80, got {dmap1[5, 5]}"

    # Test saturation
    dmap1.fill(200)
    dmap2.fill(100)
    dmap1.add(dmap2)
    assert dmap1[0, 0] == 255, f"Expected 255 (saturated), got {dmap1[0, 0]}"

    print("  [PASS] Add map")

def test_subtract_scalar():
    """Test subtracting a scalar value."""
    dmap = mcrfpy.DiscreteMap((10, 10), fill=100)
    dmap.subtract(25)
    assert dmap[5, 5] == 75, f"Expected 75, got {dmap[5, 5]}"

    # Test saturation at 0
    dmap.fill(10)
    dmap.subtract(20)  # 10 - 20 = -10 -> saturates to 0
    assert dmap[0, 0] == 0, f"Expected 0 (saturated), got {dmap[0, 0]}"

    print("  [PASS] Subtract scalar")

def test_subtract_map():
    """Test subtracting another DiscreteMap."""
    dmap1 = mcrfpy.DiscreteMap((10, 10), fill=100)
    dmap2 = mcrfpy.DiscreteMap((10, 10), fill=30)

    dmap1.subtract(dmap2)
    assert dmap1[5, 5] == 70, f"Expected 70, got {dmap1[5, 5]}"

    # Test saturation
    dmap1.fill(50)
    dmap2.fill(100)
    dmap1.subtract(dmap2)
    assert dmap1[0, 0] == 0, f"Expected 0 (saturated), got {dmap1[0, 0]}"

    print("  [PASS] Subtract map")

def test_multiply():
    """Test scalar multiplication."""
    dmap = mcrfpy.DiscreteMap((10, 10), fill=50)
    dmap.multiply(2.0)
    assert dmap[5, 5] == 100, f"Expected 100, got {dmap[5, 5]}"

    # Test saturation
    dmap.fill(100)
    dmap.multiply(3.0)  # 100 * 3 = 300 -> saturates to 255
    assert dmap[0, 0] == 255, f"Expected 255 (saturated), got {dmap[0, 0]}"

    # Test fractional
    dmap.fill(100)
    dmap.multiply(0.5)
    assert dmap[0, 0] == 50, f"Expected 50, got {dmap[0, 0]}"

    print("  [PASS] Multiply")

def test_copy_from():
    """Test copy_from operation."""
    dmap1 = mcrfpy.DiscreteMap((10, 10), fill=0)
    dmap2 = mcrfpy.DiscreteMap((5, 5), fill=99)

    dmap1.copy_from(dmap2, pos=(2, 2))

    assert dmap1[2, 2] == 99, f"Expected 99 at (2,2), got {dmap1[2, 2]}"
    assert dmap1[6, 6] == 99, f"Expected 99 at (6,6), got {dmap1[6, 6]}"
    assert dmap1[0, 0] == 0, f"Expected 0 at (0,0), got {dmap1[0, 0]}"
    assert dmap1[7, 7] == 0, f"Expected 0 at (7,7), got {dmap1[7, 7]}"

    print("  [PASS] Copy from")

def test_max():
    """Test element-wise max."""
    dmap1 = mcrfpy.DiscreteMap((10, 10), fill=50)
    dmap2 = mcrfpy.DiscreteMap((10, 10), fill=70)

    # Set some values in dmap1 higher
    dmap1[3, 3] = 100

    dmap1.max(dmap2)

    assert dmap1[0, 0] == 70, f"Expected 70 at (0,0), got {dmap1[0, 0]}"
    assert dmap1[3, 3] == 100, f"Expected 100 at (3,3), got {dmap1[3, 3]}"

    print("  [PASS] Max")

def test_min():
    """Test element-wise min."""
    dmap1 = mcrfpy.DiscreteMap((10, 10), fill=50)
    dmap2 = mcrfpy.DiscreteMap((10, 10), fill=30)

    # Set some values in dmap1 lower
    dmap1[3, 3] = 10

    dmap1.min(dmap2)

    assert dmap1[0, 0] == 30, f"Expected 30 at (0,0), got {dmap1[0, 0]}"
    assert dmap1[3, 3] == 10, f"Expected 10 at (3,3), got {dmap1[3, 3]}"

    print("  [PASS] Min")

def test_bitwise_and():
    """Test bitwise AND."""
    dmap1 = mcrfpy.DiscreteMap((10, 10), fill=0xFF)  # 11111111
    dmap2 = mcrfpy.DiscreteMap((10, 10), fill=0x0F)  # 00001111

    dmap1.bitwise_and(dmap2)
    assert dmap1[0, 0] == 0x0F, f"Expected 0x0F, got {hex(dmap1[0, 0])}"

    # Test specific pattern
    dmap1.fill(0b10101010)
    dmap2.fill(0b11110000)
    dmap1.bitwise_and(dmap2)
    assert dmap1[0, 0] == 0b10100000, f"Expected 0b10100000, got {bin(dmap1[0, 0])}"

    print("  [PASS] Bitwise AND")

def test_bitwise_or():
    """Test bitwise OR."""
    dmap1 = mcrfpy.DiscreteMap((10, 10), fill=0x0F)  # 00001111
    dmap2 = mcrfpy.DiscreteMap((10, 10), fill=0xF0)  # 11110000

    dmap1.bitwise_or(dmap2)
    assert dmap1[0, 0] == 0xFF, f"Expected 0xFF, got {hex(dmap1[0, 0])}"

    print("  [PASS] Bitwise OR")

def test_bitwise_xor():
    """Test bitwise XOR."""
    dmap1 = mcrfpy.DiscreteMap((10, 10), fill=0xFF)
    dmap2 = mcrfpy.DiscreteMap((10, 10), fill=0xFF)

    dmap1.bitwise_xor(dmap2)
    assert dmap1[0, 0] == 0x00, f"Expected 0x00, got {hex(dmap1[0, 0])}"

    dmap1.fill(0b10101010)
    dmap2.fill(0b11110000)
    dmap1.bitwise_xor(dmap2)
    assert dmap1[0, 0] == 0b01011010, f"Expected 0b01011010, got {bin(dmap1[0, 0])}"

    print("  [PASS] Bitwise XOR")

def test_invert():
    """Test invert (returns new map)."""
    dmap = mcrfpy.DiscreteMap((10, 10), fill=100)
    result = dmap.invert()

    # Original unchanged
    assert dmap[0, 0] == 100, f"Original should be unchanged, got {dmap[0, 0]}"

    # Result is inverted
    assert result[0, 0] == 155, f"Expected 155 (255-100), got {result[0, 0]}"

    # Test edge cases
    dmap.fill(0)
    result = dmap.invert()
    assert result[0, 0] == 255, f"Expected 255, got {result[0, 0]}"

    dmap.fill(255)
    result = dmap.invert()
    assert result[0, 0] == 0, f"Expected 0, got {result[0, 0]}"

    print("  [PASS] Invert")

def test_region_operations():
    """Test operations with region parameters."""
    dmap1 = mcrfpy.DiscreteMap((20, 20), fill=10)
    dmap2 = mcrfpy.DiscreteMap((20, 20), fill=5)

    # Add only in a region
    dmap1.add(dmap2, pos=(5, 5), source_pos=(0, 0), size=(5, 5))

    assert dmap1[5, 5] == 15, f"Expected 15 in region, got {dmap1[5, 5]}"
    assert dmap1[9, 9] == 15, f"Expected 15 in region, got {dmap1[9, 9]}"
    assert dmap1[0, 0] == 10, f"Expected 10 outside region, got {dmap1[0, 0]}"
    assert dmap1[10, 10] == 10, f"Expected 10 outside region, got {dmap1[10, 10]}"

    print("  [PASS] Region operations")

def main():
    print("Running DiscreteMap arithmetic tests...")

    test_add_scalar()
    test_add_map()
    test_subtract_scalar()
    test_subtract_map()
    test_multiply()
    test_copy_from()
    test_max()
    test_min()
    test_bitwise_and()
    test_bitwise_or()
    test_bitwise_xor()
    test_invert()
    test_region_operations()

    print("All DiscreteMap arithmetic tests PASSED!")
    sys.exit(0)

if __name__ == "__main__":
    main()
