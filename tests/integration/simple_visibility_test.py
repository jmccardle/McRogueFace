#!/usr/bin/env python3
"""Simple visibility test without entity append

Original intent: verify an Entity associated with a Grid has per-entity visibility
memory that is initialized, that entity.at(x, y) reports per-cell visibility state,
and that entity.update_visibility() recomputes it.

API updates (current contract):
  - entity.gridstate  -> entity.perspective_map  (a 3-state DiscreteMap:
    UNKNOWN / DISCOVERED / VISIBLE, lazily allocated once the entity has a grid)
  - the per-cell object no longer carries .visible / .discovered; entity.at(x, y)
    returns a GridPoint only when the cell is currently visible, else None.
    Discovered-but-not-visible cells are read from perspective_map directly.
  - Entity(grid_pos=...) + grid.entities.append(entity) replaces Entity((x,y), grid=grid)
"""

import mcrfpy
import sys

print("Simple visibility test...")

failures = []


def check(label, condition):
    if condition:
        print(f"  PASS: {label}")
    else:
        print(f"  FAIL: {label}")
        failures.append(label)


# Create scene and grid
simple = mcrfpy.Scene("simple")
print("Scene created")

grid = mcrfpy.Grid(grid_size=(5, 5))
print("Grid created")

# Column x == 1 is an opaque wall; everything else is open floor.
for x in range(5):
    for y in range(5):
        point = grid.at(x, y)
        point.walkable = True
        point.transparent = (x != 1)

# Create entity with grid association
entity = mcrfpy.Entity(grid_pos=(3, 2))
grid.entities.append(entity)
print(f"Entity created at {entity.cell_pos}")

# Check that per-entity visibility memory is initialized
state_map = entity.perspective_map
print(f"Perspective map size: {state_map.size}")
check("perspective_map allocated", state_map is not None)
check("perspective_map matches grid size", tuple(state_map.size) == (5, 5))
check("perspective_map starts all UNKNOWN", state_map.count(mcrfpy.Perspective.UNKNOWN) == 25)

# at() before any FOV computation: nothing is visible yet
check("at(0, 0) is None before update_visibility", entity.at(0, 0) is None)

# Compute visibility from (3, 2)
entity.update_visibility()
print("update_visibility() succeeded")

check("own cell is VISIBLE", state_map[3, 2] == mcrfpy.Perspective.VISIBLE)
check("at(3, 2) returns the visible GridPoint", entity.at(3, 2) is not None)
check("cell behind the wall stays UNKNOWN", state_map[0, 2] == mcrfpy.Perspective.UNKNOWN)
check("at(0, 2) is None (occluded)", entity.at(0, 2) is None)

# Move across the wall: previously seen cells must be remembered as DISCOVERED,
# not still reported as visible.
entity.grid_pos = (0, 2)
entity.update_visibility()
print(f"Entity moved to {entity.cell_pos}")

check("new cell is VISIBLE", state_map[0, 2] == mcrfpy.Perspective.VISIBLE)
check("old cell demoted to DISCOVERED", state_map[3, 2] == mcrfpy.Perspective.DISCOVERED)
check("at(3, 2) is None once occluded again", entity.at(3, 2) is None)

if failures:
    print(f"Test complete - {len(failures)} FAILURE(S): {failures}")
    sys.exit(1)

print("Test complete")
print("PASS")
sys.exit(0)
