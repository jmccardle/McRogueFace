#!/usr/bin/env python3
"""Test the new Entity.path_to() method"""

import mcrfpy

print("Testing Entity.path_to() method...")
print("=" * 50)

# Create scene and grid
mcrfpy.createScene("path_test")
grid = mcrfpy.Grid(grid_x=10, grid_y=10)

# Set up a simple map with some walls
for y in range(10):
    for x in range(10):
        grid.at(x, y).walkable = True
        grid.at(x, y).transparent = True

# Add some walls to create an interesting path
walls = [(3, 3), (3, 4), (3, 5), (4, 3), (5, 3)]
for x, y in walls:
    grid.at(x, y).walkable = False

# Create entity
entity = mcrfpy.Entity(2, 2)
grid.entities.append(entity)

print(f"Entity at: ({entity.x}, {entity.y})")

# Test 1: Simple path
print("\nTest 1: Path to (6, 6)")
try:
    path = entity.path_to(6, 6)
    print(f"  Path: {path}")
    print(f"  Length: {len(path)} steps")
    print("  ✓ SUCCESS")
except Exception as e:
    print(f"  ✗ FAILED: {e}")

# Test 2: Path with target_x/target_y keywords
print("\nTest 2: Path using keyword arguments")
try:
    path = entity.path_to(target_x=7, target_y=7)
    print(f"  Path: {path}")
    print(f"  Length: {len(path)} steps")
    print("  ✓ SUCCESS")
except Exception as e:
    print(f"  ✗ FAILED: {e}")

# Test 3: Path to unreachable location
print("\nTest 3: Path to current position")
try:
    path = entity.path_to(2, 2)
    print(f"  Path: {path}")
    print(f"  Length: {len(path)} steps")
    print("  ✓ SUCCESS")
except Exception as e:
    print(f"  ✗ FAILED: {e}")

# Test 4: Error cases
print("\nTest 4: Error handling")
try:
    # Out of bounds
    path = entity.path_to(15, 15)
    print("  ✗ Should have failed for out of bounds")
except ValueError as e:
    print(f"  ✓ Correctly caught out of bounds: {e}")
except Exception as e:
    print(f"  ✗ Wrong exception type: {e}")

print("\n" + "=" * 50)
print("Entity.path_to() testing complete!")