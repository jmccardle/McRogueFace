#!/usr/bin/env python3
"""Debug visibility crash"""

import mcrfpy
import sys

print("Debug visibility...")

# Create scene and grid
mcrfpy.createScene("debug")
grid = mcrfpy.Grid(grid_x=5, grid_y=5)

# Initialize grid
print("Initializing grid...")
for y in range(5):
    for x in range(5):
        cell = grid.at(x, y)
        cell.walkable = True
        cell.transparent = True

# Create entity
print("Creating entity...")
entity = mcrfpy.Entity((2, 2), grid=grid)
entity.sprite_index = 64
print(f"Entity at ({entity.x}, {entity.y})")

# Check gridstate
print(f"\nGridstate length: {len(entity.gridstate)}")
print(f"Expected: {5 * 5}")

# Try to access gridstate
print("\nChecking gridstate access...")
try:
    if len(entity.gridstate) > 0:
        state = entity.gridstate[0]
        print(f"First state: visible={state.visible}, discovered={state.discovered}")
except Exception as e:
    print(f"Error accessing gridstate: {e}")

# Try update_visibility
print("\nTrying update_visibility...")
try:
    entity.update_visibility()
    print("update_visibility succeeded")
except Exception as e:
    print(f"Error in update_visibility: {e}")

# Try perspective
print("\nTesting perspective...")
print(f"Initial perspective: {grid.perspective}")
try:
    grid.perspective = 0
    print(f"Set perspective to 0: {grid.perspective}")
except Exception as e:
    print(f"Error setting perspective: {e}")

print("\nTest complete")
sys.exit(0)