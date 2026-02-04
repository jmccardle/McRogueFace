#!/usr/bin/env python3
"""Unit tests for DiscreteMap <-> HeightMap integration."""

import mcrfpy
import sys
from enum import IntEnum

class Terrain(IntEnum):
    WATER = 0
    SAND = 1
    GRASS = 2
    FOREST = 3
    MOUNTAIN = 4

def test_from_heightmap_basic():
    """Test basic HeightMap to DiscreteMap conversion."""
    # Create a simple heightmap
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    # Create a simple mapping
    mapping = [
        ((0.0, 0.3), 0),
        ((0.3, 0.6), 1),
        ((0.6, 1.0), 2),
    ]

    dmap = mcrfpy.DiscreteMap.from_heightmap(hmap, mapping)

    # 0.5 should map to category 1
    assert dmap[5, 5] == 1, f"Expected 1, got {dmap[5, 5]}"

    print("  [PASS] from_heightmap basic")

def test_from_heightmap_full_range():
    """Test conversion with values spanning the full range."""
    hmap = mcrfpy.HeightMap((100, 1))

    # Create gradient
    for x in range(100):
        hmap[x, 0] = x / 100.0  # 0.0 to 0.99

    mapping = [
        ((0.0, 0.25), Terrain.WATER),
        ((0.25, 0.5), Terrain.SAND),
        ((0.5, 0.75), Terrain.GRASS),
        ((0.75, 1.0), Terrain.FOREST),
    ]

    dmap = mcrfpy.DiscreteMap.from_heightmap(hmap, mapping)

    # Check values at key positions
    assert dmap[10, 0] == Terrain.WATER, f"Expected WATER at 10, got {dmap[10, 0]}"
    assert dmap[30, 0] == Terrain.SAND, f"Expected SAND at 30, got {dmap[30, 0]}"
    assert dmap[60, 0] == Terrain.GRASS, f"Expected GRASS at 60, got {dmap[60, 0]}"
    assert dmap[80, 0] == Terrain.FOREST, f"Expected FOREST at 80, got {dmap[80, 0]}"

    print("  [PASS] from_heightmap full range")

def test_from_heightmap_with_enum():
    """Test from_heightmap with enum parameter."""
    hmap = mcrfpy.HeightMap((10, 10), fill=0.5)

    mapping = [
        ((0.0, 0.3), Terrain.WATER),
        ((0.3, 0.7), Terrain.GRASS),
        ((0.7, 1.0), Terrain.MOUNTAIN),
    ]

    dmap = mcrfpy.DiscreteMap.from_heightmap(hmap, mapping, enum=Terrain)

    # Value should be returned as enum member
    val = dmap[5, 5]
    assert val == Terrain.GRASS, f"Expected Terrain.GRASS, got {val}"
    assert isinstance(val, Terrain), f"Expected Terrain type, got {type(val)}"

    print("  [PASS] from_heightmap with enum")

def test_to_heightmap_basic():
    """Test basic DiscreteMap to HeightMap conversion."""
    dmap = mcrfpy.DiscreteMap((10, 10), fill=100)

    hmap = dmap.to_heightmap()

    # Direct conversion: uint8 -> float
    assert abs(hmap[5, 5] - 100.0) < 0.001, f"Expected 100.0, got {hmap[5, 5]}"

    print("  [PASS] to_heightmap basic")

def test_to_heightmap_with_mapping():
    """Test to_heightmap with value mapping."""
    dmap = mcrfpy.DiscreteMap((10, 10))

    # Create pattern
    dmap.fill(0, pos=(0, 0), size=(5, 10))  # Left half = 0
    dmap.fill(1, pos=(5, 0), size=(5, 10))  # Right half = 1

    # Map discrete values to heights
    mapping = {
        0: 0.2,
        1: 0.8,
    }

    hmap = dmap.to_heightmap(mapping)

    assert abs(hmap[2, 5] - 0.2) < 0.001, f"Expected 0.2, got {hmap[2, 5]}"
    assert abs(hmap[7, 5] - 0.8) < 0.001, f"Expected 0.8, got {hmap[7, 5]}"

    print("  [PASS] to_heightmap with mapping")

def test_roundtrip():
    """Test HeightMap -> DiscreteMap -> HeightMap roundtrip."""
    # Create original heightmap
    original = mcrfpy.HeightMap((50, 50))
    for y in range(50):
        for x in range(50):
            original[x, y] = (x + y) / 100.0  # Gradient 0.0 to 0.98

    # Convert to discrete with specific ranges
    mapping = [
        ((0.0, 0.33), 0),
        ((0.33, 0.66), 1),
        ((0.66, 1.0), 2),
    ]
    dmap = mcrfpy.DiscreteMap.from_heightmap(original, mapping)

    # Convert back with value mapping
    reverse_mapping = {
        0: 0.15,  # Midpoint of first range
        1: 0.5,   # Midpoint of second range
        2: 0.85,  # Midpoint of third range
    }
    restored = dmap.to_heightmap(reverse_mapping)

    # Verify approximate restoration
    assert abs(restored[0, 0] - 0.15) < 0.01, f"Expected ~0.15 at (0,0), got {restored[0, 0]}"
    assert abs(restored[25, 25] - 0.5) < 0.01, f"Expected ~0.5 at (25,25), got {restored[25, 25]}"

    print("  [PASS] Roundtrip conversion")

def test_query_methods():
    """Test count, count_range, min_max, histogram."""
    dmap = mcrfpy.DiscreteMap((10, 10))

    # Create pattern with different values
    dmap.fill(0, pos=(0, 0), size=(5, 5))   # 25 cells with 0
    dmap.fill(1, pos=(5, 0), size=(5, 5))   # 25 cells with 1
    dmap.fill(2, pos=(0, 5), size=(5, 5))   # 25 cells with 2
    dmap.fill(3, pos=(5, 5), size=(5, 5))   # 25 cells with 3

    # Test count
    assert dmap.count(0) == 25, f"Expected 25 zeros, got {dmap.count(0)}"
    assert dmap.count(1) == 25, f"Expected 25 ones, got {dmap.count(1)}"
    assert dmap.count(4) == 0, f"Expected 0 fours, got {dmap.count(4)}"

    # Test count_range
    assert dmap.count_range(0, 1) == 50, f"Expected 50 in range 0-1, got {dmap.count_range(0, 1)}"
    assert dmap.count_range(0, 3) == 100, f"Expected 100 in range 0-3, got {dmap.count_range(0, 3)}"

    # Test min_max
    min_val, max_val = dmap.min_max()
    assert min_val == 0, f"Expected min 0, got {min_val}"
    assert max_val == 3, f"Expected max 3, got {max_val}"

    # Test histogram
    hist = dmap.histogram()
    assert hist[0] == 25, f"Expected 25 for value 0, got {hist.get(0)}"
    assert hist[1] == 25, f"Expected 25 for value 1, got {hist.get(1)}"
    assert hist[2] == 25, f"Expected 25 for value 2, got {hist.get(2)}"
    assert hist[3] == 25, f"Expected 25 for value 3, got {hist.get(3)}"
    assert 4 not in hist, "Value 4 should not be in histogram"

    print("  [PASS] Query methods")

def test_bool_int():
    """Test bool() with integer condition."""
    dmap = mcrfpy.DiscreteMap((10, 10), fill=0)
    dmap.fill(1, pos=(2, 2), size=(3, 3))

    mask = dmap.bool(1)

    # Should be 1 where original is 1, 0 elsewhere
    assert mask[0, 0] == 0, f"Expected 0 outside region, got {mask[0, 0]}"
    assert mask[3, 3] == 1, f"Expected 1 inside region, got {mask[3, 3]}"
    assert mask.count(1) == 9, f"Expected 9 ones, got {mask.count(1)}"

    print("  [PASS] bool() with int")

def test_bool_set():
    """Test bool() with set condition."""
    dmap = mcrfpy.DiscreteMap((10, 10))
    dmap.fill(0, pos=(0, 0), size=(5, 5))
    dmap.fill(1, pos=(5, 0), size=(5, 5))
    dmap.fill(2, pos=(0, 5), size=(5, 5))
    dmap.fill(3, pos=(5, 5), size=(5, 5))

    # Match 0 or 2
    mask = dmap.bool({0, 2})

    assert mask[2, 2] == 1, "Expected 1 where value is 0"
    assert mask[7, 2] == 0, "Expected 0 where value is 1"
    assert mask[2, 7] == 1, "Expected 1 where value is 2"
    assert mask[7, 7] == 0, "Expected 0 where value is 3"
    assert mask.count(1) == 50, f"Expected 50 ones, got {mask.count(1)}"

    print("  [PASS] bool() with set")

def test_bool_callable():
    """Test bool() with callable condition."""
    dmap = mcrfpy.DiscreteMap((10, 10), fill=0)
    for y in range(10):
        for x in range(10):
            dmap[x, y] = x + y  # Values 0-18

    # Match where value > 10
    mask = dmap.bool(lambda v: v > 10)

    assert mask[5, 5] == 0, "Expected 0 where value is 10"
    assert mask[6, 6] == 1, "Expected 1 where value is 12"
    assert mask[9, 9] == 1, "Expected 1 where value is 18"

    print("  [PASS] bool() with callable")

def test_mask_memoryview():
    """Test mask() returns working memoryview."""
    dmap = mcrfpy.DiscreteMap((10, 10), fill=42)

    mv = dmap.mask()

    assert len(mv) == 100, f"Expected 100 bytes, got {len(mv)}"
    assert mv[0] == 42, f"Expected 42, got {mv[0]}"

    # Test writing through memoryview
    mv[50] = 99
    assert dmap[0, 5] == 99, f"Expected 99, got {dmap[0, 5]}"

    print("  [PASS] mask() memoryview")

def test_enum_type_property():
    """Test enum_type property getter/setter."""
    dmap = mcrfpy.DiscreteMap((10, 10), fill=1)

    # Initially no enum
    assert dmap.enum_type is None, "Expected None initially"

    # Set enum type
    dmap.enum_type = Terrain
    assert dmap.enum_type is Terrain, "Expected Terrain enum"

    # Value should now return enum member
    val = dmap[5, 5]
    assert val == Terrain.SAND, f"Expected Terrain.SAND, got {val}"

    # Clear enum type
    dmap.enum_type = None
    val = dmap[5, 5]
    assert isinstance(val, int), f"Expected int after clearing enum, got {type(val)}"

    print("  [PASS] enum_type property")

def main():
    print("Running DiscreteMap HeightMap integration tests...")

    test_from_heightmap_basic()
    test_from_heightmap_full_range()
    test_from_heightmap_with_enum()
    test_to_heightmap_basic()
    test_to_heightmap_with_mapping()
    test_roundtrip()
    test_query_methods()
    test_bool_int()
    test_bool_set()
    test_bool_callable()
    test_mask_memoryview()
    test_enum_type_property()

    print("All DiscreteMap HeightMap integration tests PASSED!")
    sys.exit(0)

if __name__ == "__main__":
    main()
