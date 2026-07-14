#!/usr/bin/env python3
"""Simple test to check path color setting"""

import mcrfpy
import sys

print("Testing path color changes...")
print("=" * 50)

failures = []

def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL: {msg}")

# Create scene and small grid
test = mcrfpy.Scene("test")
grid = mcrfpy.Grid(grid_size=(5, 5), pos=(50, 50), size=(250, 250))

# Add color layer for cell coloring (layers are objects now; add_layer takes no kwargs)
color_layer = mcrfpy.ColorLayer(name="color", z_index=-1)
grid.add_layer(color_layer)

BASE_COLOR = mcrfpy.Color(200, 200, 200)  # Light gray

# Initialize
for y in range(5):
    for x in range(5):
        grid.at(x, y).walkable = True
        color_layer.set((x, y), BASE_COLOR)

# Add entities
e1 = mcrfpy.Entity((0, 0), grid=grid)
e2 = mcrfpy.Entity((4, 4), grid=grid)
e1.sprite_index = 64
e2.sprite_index = 69

# .x/.y are PIXEL coords now; logical cell coords live on .cell_pos
print(f"Entity 1 at ({e1.cell_pos.x}, {e1.cell_pos.y})")
print(f"Entity 2 at ({e2.cell_pos.x}, {e2.cell_pos.y})")

# Get path
path = e1.path_to(int(e2.cell_pos.x), int(e2.cell_pos.y))
print(f"\nPath: {path}")
check(len(path) > 0, "path_to() returned an empty path on a fully walkable grid")
check(path[-1] == (4, 4), f"path does not end at the target: {path[-1] if path else None}")

# Try to color the path
PATH_COLOR = mcrfpy.Color(100, 255, 100)  # Green
print(f"\nSetting path cells to green ({PATH_COLOR.r}, {PATH_COLOR.g}, {PATH_COLOR.b})...")

for x, y in path:
    # Check before
    before_c = color_layer.at(x, y)
    before = (before_c.r, before_c.g, before_c.b)
    check(before == (200, 200, 200), f"cell ({x},{y}) was not the initialized gray: {before}")

    # Set color
    color_layer.set((x, y), PATH_COLOR)

    # Check after
    after_c = color_layer.at(x, y)
    after = (after_c.r, after_c.g, after_c.b)
    check(after == (100, 255, 100), f"cell ({x},{y}) did not take the path color: {after}")

    print(f"  Cell ({x},{y}): {before} -> {after}")

# Verify all path cells (and that non-path cells were NOT touched)
print("\nVerifying all cells in grid:")
for y in range(5):
    for x in range(5):
        c = color_layer.at(x, y)
        color = (c.r, c.g, c.b)
        is_path = (x, y) in path
        expected = (100, 255, 100) if is_path else (200, 200, 200)
        check(color == expected,
              f"cell ({x},{y}) in_path={is_path} expected {expected}, got {color}")
        print(f"  ({x},{y}): color={color}, in_path={is_path}")

# Quick visual test: colors must survive a real render, not just live in the data.
def check_visual(timer, runtime):
    print("\nTimer fired - checking if scene is rendering...")
    from mcrfpy import automation
    automation.screenshot("path_color_test.png")
    print("Screenshot saved as path_color_test.png")
    # Re-read after render: the render pass must not clobber the layer data
    for x, y in path:
        c = color_layer.at(x, y)
        check((c.r, c.g, c.b) == (100, 255, 100),
              f"cell ({x},{y}) lost its color after rendering: {(c.r, c.g, c.b)}")
    timer_fired.append(True)

# Set up minimal UI to test rendering
ui = test.children
ui.append(grid)

test.activate()
timer_fired = []
check_timer = mcrfpy.Timer("check", check_visual, 500, once=True)

print("\nStarting render test...")
# Headless: mcrfpy.step() is the only clock. Drive it until the timer fires.
for _ in range(20):
    mcrfpy.step(0.05)
    if timer_fired:
        break

check(bool(timer_fired), "Timer never fired after stepping 1.0s of simulated time")

print("=" * 50)
if failures:
    print(f"FAIL ({len(failures)} check(s) failed)")
    sys.exit(1)
print("PASS")
sys.exit(0)
