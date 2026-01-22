#!/usr/bin/env python3
"""Test Grid features"""
import sys
import mcrfpy

print("Testing Grid features...")

# Create a texture first
print("Loading texture...")
texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)
print(f"Texture loaded: {texture}")

# Create grid
print("Creating grid...")
grid = mcrfpy.Grid(grid_size=(15, 20), texture=texture, pos=(50, 100), size=(240, 320))
print(f"Grid created: {grid}")

# Test grid_size returns Vector
print("Testing grid_size...")
grid_size = grid.grid_size
print(f"grid_size type: {type(grid_size)}")
print(f"grid_size value: {grid_size}")

if not hasattr(grid_size, 'x'):
    print(f"FAIL: grid_size should be Vector, got {type(grid_size)}")
    sys.exit(1)

print(f"grid_size.x={grid_size.x}, grid_size.y={grid_size.y}")

if grid_size.x != 15 or grid_size.y != 20:
    print(f"FAIL: grid_size should be (15, 20), got ({grid_size.x}, {grid_size.y})")
    sys.exit(1)

# Test center returns Vector
print("Testing center...")
center = grid.center
print(f"center type: {type(center)}")
print(f"center value: {center}")

if not hasattr(center, 'x'):
    print(f"FAIL: center should be Vector, got {type(center)}")
    sys.exit(1)

print(f"center.x={center.x}, center.y={center.y}")

# Test pos returns Vector
print("Testing pos...")
pos = grid.pos
print(f"pos type: {type(pos)}")

if not hasattr(pos, 'x'):
    print(f"FAIL: pos should be Vector, got {type(pos)}")
    sys.exit(1)

print(f"pos.x={pos.x}, pos.y={pos.y}")

print("PASS: Grid Vector properties work correctly!")
sys.exit(0)
