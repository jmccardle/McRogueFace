#!/usr/bin/env python3
"""Simple visual test for path highlighting"""

import mcrfpy
import sys

# Colors
WALL_COLOR = mcrfpy.Color(60, 30, 30)
FLOOR_COLOR = mcrfpy.Color(200, 200, 220)
PATH_COLOR = mcrfpy.Color(100, 255, 100)

# Create scene
visual_test = mcrfpy.Scene("visual_test")

# Create grid
grid = mcrfpy.Grid(grid_w=5, grid_h=5)
grid.fill_color = mcrfpy.Color(0, 0, 0)

# Add color layer for cell coloring
color_layer = grid.add_layer("color", z_index=-1)

def check_render(timer, runtime):
    """Timer callback to verify rendering"""
    print(f"\nTimer fired after {runtime}ms")

    # Take screenshot
    from mcrfpy import automation
    automation.screenshot("visual_path_test.png")
    print("Screenshot saved as visual_path_test.png")

    # Sample some path cells to verify colors
    print("\nSampling path cell colors from grid:")
    for x, y in [(1, 1), (2, 2), (3, 3)]:
        color = color_layer.at(x, y)
        print(f"  Cell ({x},{y}): color=({color.r}, {color.g}, {color.b})")

    sys.exit(0)

# Initialize all cells as floor
print("Initializing grid...")
for y in range(5):
    for x in range(5):
        grid.at(x, y).walkable = True
        color_layer.set(x, y, FLOOR_COLOR)

# Create entities
e1 = mcrfpy.Entity((0, 0), grid=grid)
e2 = mcrfpy.Entity((4, 4), grid=grid)
e1.sprite_index = 64  # @
e2.sprite_index = 69  # E

print(f"Entity 1 at ({e1.x}, {e1.y})")
print(f"Entity 2 at ({e2.x}, {e2.y})")

# Get path
path = e1.path_to(int(e2.x), int(e2.y))
print(f"\nPath from E1 to E2: {path}")

# Color the path
if path:
    print("\nColoring path cells green...")
    for x, y in path:
        color_layer.set(x, y, PATH_COLOR)
        print(f"  Set ({x},{y}) to green")

# Set up UI
ui = visual_test.children
ui.append(grid)
grid.position = (50, 50)
grid.size = (250, 250)

# Add title
title = mcrfpy.Caption(pos=(50, 10), text="Path Visualization Test")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Set scene
visual_test.activate()

# Set timer to check rendering
check_timer = mcrfpy.Timer("check", check_render, 500, once=True)

print("\nScene ready. Path should be visible in green.")