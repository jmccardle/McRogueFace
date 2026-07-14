#!/usr/bin/env python3
"""Simple interactive visibility test"""

import mcrfpy
import sys

failures = []

def check(cond, msg):
    if cond:
        print(f"  ok: {msg}")
    else:
        print(f"  FAIL: {msg}")
        failures.append(msg)

# Create scene and grid
print("Creating scene...")
vis_test = mcrfpy.Scene("vis_test")

print("Creating grid...")
grid = mcrfpy.Grid(grid_size=(10, 10), pos=(50, 50), size=(300, 300))

# Add color layer for cell coloring
# (GridPoint has no .color anymore; per-cell color lives in a ColorLayer)
color_layer = mcrfpy.ColorLayer(name="color", z_index=-1)
grid.add_layer(color_layer)
check(grid.layer("color") is not None, "color layer attached to grid")
check(tuple(color_layer.grid_size) == (10, 10), "color layer auto-resized to grid")

# Initialize grid
print("Initializing grid...")
for y in range(10):
    for x in range(10):
        cell = grid.at(x, y)
        cell.walkable = True
        cell.transparent = True
        color_layer.set((x, y), mcrfpy.Color(100, 100, 120))

_c = color_layer.at(3, 7)
check((_c.r, _c.g, _c.b) == (100, 100, 120), "color layer stores per-cell color")

# An opaque wall so visibility has something to actually occlude
for y in range(10):
    wall = grid.at(2, y)
    wall.transparent = False
    wall.walkable = False

# Create entity
print("Creating entity...")
entity = mcrfpy.Entity(grid_pos=(5, 5))
entity.sprite_index = 64
grid.entities.append(entity)
check(entity.grid is grid.grid_data, "entity.grid is the shared GridData (#313/#361)")

print("Updating visibility...")
entity.update_visibility()

# entity.gridstate -> entity.perspective_map (UNKNOWN/DISCOVERED/VISIBLE)
pmap = entity.perspective_map
check(pmap.get((5, 5)) == mcrfpy.Perspective.VISIBLE, "entity's own cell is VISIBLE")
check(pmap.get((9, 5)) == mcrfpy.Perspective.VISIBLE, "open cell on entity's side is VISIBLE")
check(pmap.get((0, 5)) == mcrfpy.Perspective.UNKNOWN, "cell behind the wall is UNKNOWN")
check(grid.is_in_fov((5, 5)), "grid.is_in_fov agrees the entity's cell is lit")

# Set up UI
print("Setting up UI...")
ui = vis_test.children
ui.append(grid)
check(len(ui) == 1, "grid appended to scene UI")

# Test perspective
# perspective is now an Entity (fog-of-war source) or None (omniscient),
# not the old integer entity index (-1 == omniscient).
print("Testing perspective...")
grid.perspective = entity
check(grid.perspective is entity, "perspective bound to entity")
check(grid.perspective_enabled, "perspective mode enabled")

grid.perspective = None  # Omniscient
print(f"Perspective set to: {grid.perspective}")
check(grid.perspective is None, "perspective cleared")
check(not grid.perspective_enabled, "omniscient: perspective mode disabled")

print("Setting scene...")
vis_test.activate()
check(mcrfpy.current_scene is vis_test, "scene activated")

print("Ready!")

if failures:
    print(f"FAIL ({len(failures)} checks failed)")
    sys.exit(1)
print("PASS")
sys.exit(0)
