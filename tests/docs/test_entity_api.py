#!/usr/bin/env python3
"""Quick test to verify Entity constructor signature."""
import mcrfpy
import sys

scene = mcrfpy.Scene("test")
scene.activate()
mcrfpy.step(0.01)

texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
grid = mcrfpy.Grid(grid_size=(20, 15), texture=texture, pos=(10, 10), size=(640, 480))
scene.children.append(grid)

# Test grid_pos vs grid_x/grid_y
try:
    e1 = mcrfpy.Entity(grid_pos=(5, 5), texture=texture, sprite_index=85)
    grid.entities.append(e1)
    print("grid_pos= WORKS")
except TypeError as e:
    print(f"grid_pos= FAILS: {e}")

try:
    e2 = mcrfpy.Entity(grid_x=7, grid_y=7, texture=texture, sprite_index=85)
    grid.entities.append(e2)
    print("grid_x=/grid_y= WORKS")
except TypeError as e:
    print(f"grid_x=/grid_y= FAILS: {e}")

print("Entity API test complete")
sys.exit(0)
