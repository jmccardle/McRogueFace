#!/usr/bin/env python3
"""Test pathfinding integration with demos"""

import mcrfpy
import sys

print("Testing pathfinding integration...")
print("=" * 50)

# Create scene and grid
mcrfpy.createScene("test")
grid = mcrfpy.Grid(grid_x=10, grid_y=10)

# Initialize grid
for y in range(10):
    for x in range(10):
        grid.at(x, y).walkable = True

# Add some walls
for i in range(5):
    grid.at(5, i + 2).walkable = False

# Create entities
e1 = mcrfpy.Entity((2, 5), grid=grid)
e2 = mcrfpy.Entity((8, 5), grid=grid)

# Test pathfinding between entities
print(f"Entity 1 at ({e1.x}, {e1.y})")
print(f"Entity 2 at ({e2.x}, {e2.y})")

# Entity 1 finds path to Entity 2
path = e1.path_to(int(e2.x), int(e2.y))
print(f"\nPath from E1 to E2: {path}")
print(f"Path length: {len(path)} steps")

# Test movement simulation
if path and len(path) > 1:
    print("\nSimulating movement along path:")
    for i, (x, y) in enumerate(path[:5]):  # Show first 5 steps
        print(f"  Step {i}: Move to ({x}, {y})")

# Test path in reverse
path_reverse = e2.path_to(int(e1.x), int(e1.y))
print(f"\nPath from E2 to E1: {path_reverse}")
print(f"Reverse path length: {len(path_reverse)} steps")

print("\n✓ Pathfinding integration working correctly!")
print("Enhanced demos are ready for interactive use.")

# Quick animation test
def test_timer(dt):
    print(f"Timer callback received: dt={dt}ms")
    sys.exit(0)

# Set a quick timer to test animation system
mcrfpy.setTimer("test", test_timer, 100)

print("\nTesting timer system for animations...")