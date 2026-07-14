#!/usr/bin/env python3
"""Simple visual test for path highlighting"""

import mcrfpy
import sys

# Colors
WALL_COLOR = mcrfpy.Color(60, 30, 30)
FLOOR_COLOR = mcrfpy.Color(200, 200, 220)
PATH_COLOR = mcrfpy.Color(100, 255, 100)

failures = []
timer_fired = False

# Create scene
visual_test = mcrfpy.Scene("visual_test")

# Create grid
grid = mcrfpy.Grid(grid_size=(5, 5), pos=(50, 50), size=(250, 250))
grid.fill_color = mcrfpy.Color(0, 0, 0)

# Add color layer for cell coloring (GridPoint has no .color anymore; use a ColorLayer)
color_layer = mcrfpy.ColorLayer(name="color", z_index=-1)
grid.add_layer(color_layer)

def check_render(timer, runtime):
    """Timer callback to verify rendering"""
    global timer_fired
    timer_fired = True
    print(f"\nTimer fired after {runtime}ms")

    # Take screenshot (this is what forces a render in headless mode)
    from mcrfpy import automation
    automation.screenshot("visual_path_test.png")
    print("Screenshot saved as visual_path_test.png")

    # Sample some path cells to verify colors
    print("\nSampling path cell colors from grid:")
    for x, y in [(1, 1), (2, 2), (3, 3)]:
        color = color_layer.at((x, y))
        print(f"  Cell ({x},{y}): color=({color.r}, {color.g}, {color.b})")
        if (color.r, color.g, color.b) != (PATH_COLOR.r, PATH_COLOR.g, PATH_COLOR.b):
            failures.append(f"cell ({x},{y}) is not PATH_COLOR: "
                            f"({color.r}, {color.g}, {color.b})")

    # A cell off the path must still be floor-colored
    off = color_layer.at((0, 4))
    if (off.r, off.g, off.b) != (FLOOR_COLOR.r, FLOOR_COLOR.g, FLOOR_COLOR.b):
        failures.append(f"off-path cell (0,4) is not FLOOR_COLOR: "
                        f"({off.r}, {off.g}, {off.b})")

    timer.stop()

# Initialize all cells as floor
print("Initializing grid...")
for y in range(5):
    for x in range(5):
        grid.at(x, y).walkable = True
        color_layer.set((x, y), FLOOR_COLOR)

# Create entities
e1 = mcrfpy.Entity(grid_pos=(0, 0))
e2 = mcrfpy.Entity(grid_pos=(4, 4))
grid.entities.append(e1)
grid.entities.append(e2)
e1.sprite_index = 64  # @
e2.sprite_index = 69  # E

# .x/.y are pixel coords now; .cell_pos is the logical cell
print(f"Entity 1 at ({e1.cell_pos.x}, {e1.cell_pos.y})")
print(f"Entity 2 at ({e2.cell_pos.x}, {e2.cell_pos.y})")

# Get path
path = e1.path_to(int(e2.cell_pos.x), int(e2.cell_pos.y))
print(f"\nPath from E1 to E2: {path}")

if not path:
    failures.append("path_to() returned no path between (0,0) and (4,4)")
else:
    if path[-1] != (4, 4):
        failures.append(f"path does not end at target: {path[-1]}")
    for cell in [(1, 1), (2, 2), (3, 3)]:
        if cell not in path:
            failures.append(f"expected diagonal path cell {cell} missing from path")

# Color the path
if path:
    print("\nColoring path cells green...")
    for x, y in path:
        color_layer.set((x, y), PATH_COLOR)
        print(f"  Set ({x},{y}) to green")

# Set up UI
ui = visual_test.children
ui.append(grid)

# Add title
title = mcrfpy.Caption(pos=(50, 10), text="Path Visualization Test")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Set scene
visual_test.activate()

# Set timer to check rendering
check_timer = mcrfpy.Timer("check", check_render, 500, once=True)

print("\nScene ready. Path should be visible in green.")

# Headless: mcrfpy.step() is the clock; the timer never fires on its own.
for _ in range(20):
    mcrfpy.step(0.1)

if not timer_fired:
    failures.append("timer callback never fired; render checks did not run")

if failures:
    for f in failures:
        print(f"FAIL: {f}")
    sys.exit(1)

print("PASS")
sys.exit(0)
