#!/usr/bin/env python3
"""Test edge cases for Entity.path_to() method"""

import mcrfpy

print("Testing Entity.path_to() edge cases...")
print("=" * 50)

# Test 1: Entity without grid
print("Test 1: Entity not in grid")
try:
    entity = mcrfpy.Entity(5, 5)
    path = entity.path_to(8, 8)
    print("  ✗ Should have failed for entity not in grid")
except ValueError as e:
    print(f"  ✓ Correctly caught no grid error: {e}")
except Exception as e:
    print(f"  ✗ Wrong exception type: {e}")

# Test 2: Entity in grid with walls blocking path
print("\nTest 2: Completely blocked path")
mcrfpy.createScene("blocked_test")
grid = mcrfpy.Grid(grid_x=5, grid_y=5)

# Make all tiles walkable first
for y in range(5):
    for x in range(5):
        grid.at(x, y).walkable = True

# Create a wall that completely blocks the path
for x in range(5):
    grid.at(x, 2).walkable = False

entity = mcrfpy.Entity(1, 1)
grid.entities.append(entity)

try:
    path = entity.path_to(1, 4)
    if path:
        print(f"  Path found: {path}")
    else:
        print("  ✓ No path found (empty list returned)")
except Exception as e:
    print(f"  ✗ Unexpected error: {e}")

# Test 3: Alternative parameter parsing
print("\nTest 3: Alternative parameter names")
try:
    path = entity.path_to(x=3, y=1)
    print(f"  Path with x/y params: {path}")
    print("  ✓ SUCCESS")
except Exception as e:
    print(f"  ✗ FAILED: {e}")

print("\n" + "=" * 50)
print("Edge case testing complete!")