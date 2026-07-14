#!/usr/bin/env python3
"""Debug visibility crash

Originally probed entity.gridstate / entity.update_visibility() / grid.perspective
for crashes. Updated to the current API (#313/#361):
  - entity.gridstate  -> entity.perspective_map (a 3-state DiscreteMap:
                         UNKNOWN / DISCOVERED / VISIBLE, indexed by (x, y))
  - grid.perspective  -> now takes an Entity or None, not an int index
"""

import mcrfpy
import sys

failures = []

def check(cond, msg):
    if cond:
        print(f"  ok: {msg}")
    else:
        print(f"  FAIL: {msg}")
        failures.append(msg)

print("Debug visibility...")

# Create scene and grid
debug = mcrfpy.Scene("debug")
grid = mcrfpy.Grid(grid_size=(5, 5))

# Initialize grid
print("Initializing grid...")
for y in range(5):
    for x in range(5):
        cell = grid.at(x, y)
        cell.walkable = True
        cell.transparent = True

# Create entity
print("Creating entity...")
entity = mcrfpy.Entity(grid_pos=(2, 2))
entity.sprite_index = 64
grid.entities.append(entity)
# .x/.y are PIXEL coords now; .grid_x/.grid_y are the canonical cell coords
print(f"Entity at cell ({entity.grid_x}, {entity.grid_y}), pixels ({entity.x}, {entity.y})")
check((entity.grid_x, entity.grid_y) == (2, 2), "entity sits at its grid_pos (2, 2)")

# A second entity, so visible_entities() has something to find
neighbor = mcrfpy.Entity(grid_pos=(4, 4))
grid.entities.append(neighbor)

# Check perspective_map (successor to gridstate)
pmap = entity.perspective_map
print(f"\nPerspective map size: {pmap.size}")
check(pmap.size == (5, 5), "perspective_map covers every grid cell (5x5)")

# Access the map before any FOV is computed: everything is unknown
print("\nChecking perspective_map access...")
Perspective = pmap.enum_type
check(pmap.get((0, 0)) == Perspective.UNKNOWN,
      "cells start UNKNOWN before update_visibility()")
check(pmap.histogram() == {int(Perspective.UNKNOWN): 25},
      "all 25 cells start UNKNOWN")

# update_visibility must populate the map (open 5x5 room, sight_radius 10)
print("\nTrying update_visibility...")
entity.update_visibility()
check(pmap.get((2, 2)) == Perspective.VISIBLE,
      "entity's own cell is VISIBLE after update_visibility()")
check(pmap.get((0, 0)) == Perspective.VISIBLE,
      "far corner of an open, transparent room is VISIBLE")
check(pmap.histogram() == {int(Perspective.VISIBLE): 25},
      "all 25 cells of the open room are VISIBLE")
# visible_entities() returns OTHER entities only. Compare by cell, not identity:
# it hands back fresh wrappers rather than cached ones (see notes on UIEntity.cpp:1334).
seen = [(e.grid_x, e.grid_y) for e in entity.visible_entities()]
check(seen == [(4, 4)],
      "visible_entities() sees the neighbor at (4, 4) and excludes self")

# Perspective now takes an Entity (or None), not an index
print("\nTesting perspective...")
print(f"Initial perspective: {grid.perspective}")
check(grid.perspective is None, "grid.perspective defaults to None (omniscient)")

grid.perspective = entity
print(f"Set perspective to entity: {grid.perspective}")
check(grid.perspective is entity, "grid.perspective round-trips the Entity")

grid.perspective = None
check(grid.perspective is None, "grid.perspective can be cleared back to None")

try:
    grid.perspective = 0
    check(False, "grid.perspective rejects a non-Entity (int index is gone)")
except TypeError:
    check(True, "grid.perspective rejects a non-Entity (int index is gone)")

print("\nTest complete")
if failures:
    print(f"FAIL: {len(failures)} check(s) failed")
    sys.exit(1)
print("PASS")
sys.exit(0)
