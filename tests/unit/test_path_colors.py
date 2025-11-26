#!/usr/bin/env python3
"""Simple test to check path color setting"""

import mcrfpy
import sys

print("Testing path color changes...")
print("=" * 50)

# Create scene and small grid
mcrfpy.createScene("test")
grid = mcrfpy.Grid(grid_x=5, grid_y=5)

# Initialize
for y in range(5):
    for x in range(5):
        grid.at(x, y).walkable = True
        grid.at(x, y).color = mcrfpy.Color(200, 200, 200)  # Light gray

# Add entities
e1 = mcrfpy.Entity(0, 0)
e2 = mcrfpy.Entity(4, 4)
grid.entities.append(e1)
grid.entities.append(e2)

print(f"Entity 1 at ({e1.x}, {e1.y})")
print(f"Entity 2 at ({e2.x}, {e2.y})")

# Get path
path = e1.path_to(int(e2.x), int(e2.y))
print(f"\nPath: {path}")

# Try to color the path
PATH_COLOR = mcrfpy.Color(100, 255, 100)  # Green
print(f"\nSetting path cells to green ({PATH_COLOR.r}, {PATH_COLOR.g}, {PATH_COLOR.b})...")

for x, y in path:
    cell = grid.at(x, y)
    # Check before
    before = cell.color[:3]  # Get RGB from tuple
    
    # Set color
    cell.color = PATH_COLOR
    
    # Check after
    after = cell.color[:3]  # Get RGB from tuple
    
    print(f"  Cell ({x},{y}): {before} -> {after}")

# Verify all path cells
print("\nVerifying all cells in grid:")
for y in range(5):
    for x in range(5):
        cell = grid.at(x, y)
        color = cell.color[:3]  # Get RGB from tuple
        is_path = (x, y) in path
        print(f"  ({x},{y}): color={color}, in_path={is_path}")

print("\nIf colors are changing in data but not visually, it may be a rendering issue.")

# Quick visual test
def check_visual(runtime):
    print("\nTimer fired - checking if scene is rendering...")
    # Take screenshot to see actual rendering
    try:
        from mcrfpy import automation
        automation.screenshot("path_color_test.png")
        print("Screenshot saved as path_color_test.png")
    except:
        print("Could not take screenshot")
    sys.exit(0)

# Set up minimal UI to test rendering
ui = mcrfpy.sceneUI("test")
ui.append(grid)
grid.position = (50, 50)
grid.size = (250, 250)

mcrfpy.setScene("test")
mcrfpy.setTimer("check", check_visual, 500)

print("\nStarting render test...")