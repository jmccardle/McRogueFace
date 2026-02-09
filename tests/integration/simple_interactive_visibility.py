#!/usr/bin/env python3
"""Simple interactive visibility test"""

import mcrfpy
import sys

# Create scene and grid
print("Creating scene...")
vis_test = mcrfpy.Scene("vis_test")

print("Creating grid...")
grid = mcrfpy.Grid(grid_w=10, grid_h=10)

# Add color layer for cell coloring
color_layer = grid.add_layer("color", z_index=-1)

# Initialize grid
print("Initializing grid...")
for y in range(10):
    for x in range(10):
        cell = grid.at(x, y)
        cell.walkable = True
        cell.transparent = True
        color_layer.set(x, y, mcrfpy.Color(100, 100, 120))

# Create entity
print("Creating entity...")
entity = mcrfpy.Entity((5, 5), grid=grid)
entity.sprite_index = 64

print("Updating visibility...")
entity.update_visibility()

# Set up UI
print("Setting up UI...")
ui = vis_test.children
ui.append(grid)
grid.position = (50, 50)
grid.size = (300, 300)

# Test perspective
print("Testing perspective...")
grid.perspective = -1  # Omniscient
print(f"Perspective set to: {grid.perspective}")

print("Setting scene...")
vis_test.activate()

print("Ready!")