#!/usr/bin/env python3
"""Test GridPoint.grid_pos property"""
import sys
import mcrfpy

print("Testing GridPoint.grid_pos...")

texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)
grid = mcrfpy.Grid(grid_size=(10, 10), texture=texture, pos=(0, 0), size=(160, 160))

# Get a grid point
print("Getting grid point at (3, 5)...")
point = grid.at(3, 5)
print(f"Point: {point}")

# Test grid_pos property exists and returns tuple
print("Checking grid_pos property...")
grid_pos = point.grid_pos
print(f"grid_pos type: {type(grid_pos)}")
print(f"grid_pos value: {grid_pos}")

if not isinstance(grid_pos, tuple):
    print(f"FAIL: grid_pos should be tuple, got {type(grid_pos)}")
    sys.exit(1)

if len(grid_pos) != 2:
    print(f"FAIL: grid_pos should have 2 elements, got {len(grid_pos)}")
    sys.exit(1)

if grid_pos != (3, 5):
    print(f"FAIL: grid_pos should be (3, 5), got {grid_pos}")
    sys.exit(1)

# Test another position
print("Getting grid point at (7, 2)...")
point2 = grid.at(7, 2)
if point2.grid_pos != (7, 2):
    print(f"FAIL: grid_pos should be (7, 2), got {point2.grid_pos}")
    sys.exit(1)

print("PASS: GridPoint.grid_pos works correctly!")
sys.exit(0)
