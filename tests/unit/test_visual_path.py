#!/usr/bin/env python3
"""Simple visual test for path highlighting"""

import mcrfpy
import sys

# Colors as tuples (r, g, b, a)
WALL_COLOR = (60, 30, 30, 255)
FLOOR_COLOR = (200, 200, 220, 255) 
PATH_COLOR = (100, 255, 100, 255)

def check_render(dt):
    """Timer callback to verify rendering"""
    print(f"\nTimer fired after {dt}ms")
    
    # Take screenshot
    from mcrfpy import automation
    automation.screenshot("visual_path_test.png")
    print("Screenshot saved as visual_path_test.png")
    
    # Sample some path cells to verify colors
    print("\nSampling path cell colors from grid:")
    for x, y in [(1, 1), (2, 2), (3, 3)]:
        cell = grid.at(x, y)
        color = cell.color
        print(f"  Cell ({x},{y}): color={color[:3]}")
    
    sys.exit(0)

# Create scene
mcrfpy.createScene("visual_test")

# Create grid
grid = mcrfpy.Grid(grid_x=5, grid_y=5)
grid.fill_color = mcrfpy.Color(0, 0, 0)

# Initialize all cells as floor
print("Initializing grid...")
for y in range(5):
    for x in range(5):
        grid.at(x, y).walkable = True
        grid.at(x, y).color = FLOOR_COLOR

# Create entities
e1 = mcrfpy.Entity(0, 0)
e2 = mcrfpy.Entity(4, 4)
e1.sprite_index = 64  # @
e2.sprite_index = 69  # E
grid.entities.append(e1)
grid.entities.append(e2)

print(f"Entity 1 at ({e1.x}, {e1.y})")
print(f"Entity 2 at ({e2.x}, {e2.y})")

# Get path
path = e1.path_to(int(e2.x), int(e2.y))
print(f"\nPath from E1 to E2: {path}")

# Color the path
if path:
    print("\nColoring path cells green...")
    for x, y in path:
        grid.at(x, y).color = PATH_COLOR
        print(f"  Set ({x},{y}) to green")

# Set up UI
ui = mcrfpy.sceneUI("visual_test")
ui.append(grid)
grid.position = (50, 50)
grid.size = (250, 250)

# Add title
title = mcrfpy.Caption("Path Visualization Test", 50, 10)
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Set scene
mcrfpy.setScene("visual_test")

# Set timer to check rendering
mcrfpy.setTimer("check", check_render, 500)

print("\nScene ready. Path should be visible in green.")