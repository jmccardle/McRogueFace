#!/usr/bin/env python3
"""
Test Knowledge Stubs 1 Visibility System
========================================

Tests per-entity visibility tracking with perspective rendering.

API notes (updated for current mcrfpy):
  - entity.gridstate -> entity.perspective_map (a 3-state DiscreteMap:
    UNKNOWN / DISCOVERED / VISIBLE, exclusive states).
  - grid.perspective is an Entity (or None for omniscient), not an int index.
  - Cell colors come from a ColorLayer, not GridPoint.color.
  - Headless time only advances via mcrfpy.step().
"""

import mcrfpy
from mcrfpy import automation
import sys

print("Knowledge Stubs 1 - Visibility System Test")
print("==========================================")

failures = []

def check(condition, message):
    if condition:
        print(f"  PASS: {message}")
    else:
        print(f"  FAIL: {message}")
        failures.append(message)

# Create scene and grid
visibility_test = mcrfpy.Scene("visibility_test")
grid = mcrfpy.Grid(grid_size=(20, 15), pos=(50, 50), size=(600, 450))
grid.fill_color = mcrfpy.Color(20, 20, 30)  # Dark background

# Add a color layer for cell coloring
color_layer = mcrfpy.ColorLayer(name="color", z_index=-1)
grid.grid_data.add_layer(color_layer)

# Initialize grid - all walkable and transparent
print("\nInitializing 20x15 grid...")
for y in range(15):
    for x in range(20):
        cell = grid.grid_data.at(x, y)
        cell.walkable = True
        cell.transparent = True
        color_layer.set((x, y), mcrfpy.Color(100, 100, 120))  # Floor color

# Create some walls to block vision
print("Adding walls...")
walls = [
    # Vertical wall
    [(10, y) for y in range(3, 12)],
    # Horizontal walls
    [(x, 7) for x in range(5, 10)],
    [(x, 7) for x in range(11, 16)],
    # Corner walls
    [(5, 3), (5, 4), (6, 3)],
    [(15, 3), (15, 4), (14, 3)],
    [(5, 11), (5, 10), (6, 11)],
    [(15, 11), (15, 10), (14, 11)],
]

for wall_group in walls:
    for x, y in wall_group:
        cell = grid.grid_data.at(x, y)
        cell.walkable = False
        cell.transparent = False
        color_layer.set((x, y), mcrfpy.Color(40, 20, 20))  # Wall color

# Create entities
print("\nCreating entities...")
entities = [
    mcrfpy.Entity(grid_pos=(2, 7)),    # Left side
    mcrfpy.Entity(grid_pos=(18, 7)),   # Right side
    mcrfpy.Entity(grid_pos=(10, 1)),   # Top center (above wall)
]

for i, entity in enumerate(entities):
    entity.sprite_index = 64 + i  # @, A, B
    grid.entities.append(entity)
    print(f"  Entity {i}: cell {entity.grid_x, entity.grid_y}")

# Test 1: Check initial perspective_map (was: gridstate)
print("\nTest 1: Initial perspective_map")
e0 = entities[0]
pm0 = e0.perspective_map
print(f"  Entity 0 perspective_map size: {pm0.size}")
check(pm0.size == (20, 15), "perspective_map covers all 20x15 cells")
check(pm0.enum_type is mcrfpy.Perspective, "perspective_map uses the Perspective enum")

# Test 2: Update visibility for each entity
print("\nTest 2: Updating visibility for each entity")
counts = []
for i, entity in enumerate(entities):
    entity.update_visibility()

    pm = entity.perspective_map
    # VISIBLE and DISCOVERED are exclusive states; "ever seen" = both.
    visible_count = pm.count(mcrfpy.Perspective.VISIBLE)
    discovered_count = visible_count + pm.count(mcrfpy.Perspective.DISCOVERED)
    counts.append((visible_count, discovered_count))
    print(f"  Entity {i}: {visible_count} visible, {discovered_count} discovered")
    check(visible_count > 0, f"Entity {i} sees at least one cell")
    check(pm.get(entity.grid_pos) == mcrfpy.Perspective.VISIBLE,
          f"Entity {i} sees its own cell")
    check(visible_count < 20 * 15, f"Entity {i} does not see the whole map (walls block FOV)")

# Walls must actually block vision: entity 0 (left of the vertical wall at x=10)
# must not see entity 1's cell (18, 7) on the far side of it.
pm0 = entities[0].perspective_map
check(pm0.get((18, 7)) == mcrfpy.Perspective.UNKNOWN,
      "Entity 0 cannot see through the wall to (18, 7)")
# ...but the near face of a blocking wall is itself visible.
check(pm0.get((5, 7)) == mcrfpy.Perspective.VISIBLE,
      "Entity 0 sees the wall cell (5, 7) that blocks it")

# Test 3: Test perspective property
# NOTE: perspective is now an Entity (or None), not an integer index (#313/#361).
print("\nTest 3: Testing perspective property")
print(f"  Initial perspective: {grid.perspective}")
check(grid.perspective is None, "perspective defaults to None (omniscient)")
check(grid.perspective_enabled is False, "perspective_enabled defaults to False")

grid.perspective = entities[0]
print(f"  Set to entity 0: {grid.perspective}")
check(grid.perspective is entities[0], "perspective returns the assigned entity")
check(grid.perspective_enabled is True, "assigning an entity enables perspective mode")

# Test invalid perspective (an int index is no longer accepted)
try:
    grid.perspective = 10  # Not an Entity
    check(False, "invalid perspective should raise TypeError")
except TypeError as e:
    print(f"  Correctly rejected invalid perspective: {e}")
    check(True, "invalid perspective raises TypeError")

# Test 4: Visual demonstration - cycle perspectives via a timer, driven by step()
print("\nTest 4: cycling perspectives")
cycle_order = [None, entities[0], entities[1], entities[2]]
seen_perspectives = []

def visual_test(timer, runtime):
    idx = len(seen_perspectives)
    if idx >= len(cycle_order):
        timer.stop()
        return
    grid.perspective = cycle_order[idx]
    seen_perspectives.append(grid.perspective)
    label = "omniscient" if grid.perspective is None else f"Entity {idx - 1}"
    print(f"  Switched to {label} perspective at {runtime}ms")
    automation.screenshot(f"visibility_perspective_{idx}.png")

# Set scene and UI
ui = visibility_test.children
ui.append(grid)

title = mcrfpy.Caption(pos=(200, 10), text="Knowledge Stubs 1 - Visibility Test")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

info = mcrfpy.Caption(pos=(50, 520), text="Perspective: None (omniscient)")
info.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(info)

legend = mcrfpy.Caption(pos=(50, 540), text="Black=Never seen, Dark gray=Discovered, Normal=Visible")
legend.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(legend)

visibility_test.activate()

cycle_timer = mcrfpy.Timer("cycle", visual_test, 100)
# Headless: mcrfpy.step() is the only clock; one timer event per step.
for _ in range(len(cycle_order) + 1):
    mcrfpy.step(0.1)

check(seen_perspectives == cycle_order,
      f"cycled through all perspectives (got {len(seen_perspectives)} of {len(cycle_order)})")

# Test 5: Movement and visibility update
print("\nTest 5: Movement and visibility update")
entity = entities[0]
# NOTE: entity.x/.y are pixel draw coordinates; the logical cell is grid_x/grid_y.
print(f"  Entity 0 initial cell: {entity.grid_x, entity.grid_y}")
before_visible, _ = counts[0]

# Move entity next to the horizontal wall opening
entity.grid_pos = (8, 7)
print(f"  Moved to: {entity.grid_x, entity.grid_y}")
check((entity.grid_x, entity.grid_y) == (8, 7), "entity moved to (8, 7)")

# Update visibility
entity.update_visibility()
pm0 = entity.perspective_map
visible_count = pm0.count(mcrfpy.Perspective.VISIBLE)
ever_seen = visible_count + pm0.count(mcrfpy.Perspective.DISCOVERED)
print(f"  Visible cells after move: {visible_count} (ever seen: {ever_seen})")
check(visible_count > 0, "entity sees cells from its new position")
check(pm0.get((8, 7)) == mcrfpy.Perspective.VISIBLE, "entity sees its new cell")
check(ever_seen >= before_visible,
      "memory is retained across movement (discovered cells persist)")
# Cells visible from the old spot but not the new one must be remembered, not forgotten.
check(pm0.get((2, 7)) in (mcrfpy.Perspective.DISCOVERED, mcrfpy.Perspective.VISIBLE),
      "old position remains at least DISCOVERED after moving away")

print()
if failures:
    print(f"FAIL: {len(failures)} check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("PASS")
sys.exit(0)
