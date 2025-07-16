#!/usr/bin/env python3
"""Simple interactive visibility test"""

import mcrfpy
import sys

# Create scene and grid
print("Creating scene...")
mcrfpy.createScene("vis_test")

print("Creating grid...")
grid = mcrfpy.Grid(grid_x=10, grid_y=10)

# Initialize grid
print("Initializing grid...")
for y in range(10):
    for x in range(10):
        cell = grid.at(x, y)
        cell.walkable = True
        cell.transparent = True
        cell.color = mcrfpy.Color(100, 100, 120)

# Create entity
print("Creating entity...")
entity = mcrfpy.Entity(5, 5, grid=grid)
entity.sprite_index = 64

print("Updating visibility...")
entity.update_visibility()

# Set up UI
print("Setting up UI...")
ui = mcrfpy.sceneUI("vis_test")
ui.append(grid)
grid.position = (50, 50)
grid.size = (300, 300)

# Test perspective
print("Testing perspective...")
grid.perspective = -1  # Omniscient
print(f"Perspective set to: {grid.perspective}")

print("Setting scene...")
mcrfpy.setScene("vis_test")

print("Ready!")