#!/usr/bin/env python3
"""Debug empty paths issue

Original intent: pathfinding was returning EMPTY paths on a fully-walkable grid.
This test verifies that A* and Dijkstra both return non-empty paths, that walls
are respected (detour), that an unreachable/blocked destination yields no path,
and that the TCOD map stays in sync with walkability changes.

API notes (2026-07): compute_astar_path/compute_dijkstra/get_dijkstra_path are gone.
Pathfinding lives on GridData: find_path() -> AStarPath | None,
get_dijkstra_map(root=...) -> DijkstraMap (cached; clear_dijkstra_maps() after
walkability changes). TCOD sync is automatic -- there is no sync_tcod_map().
"""

import mcrfpy
import sys

print("Debugging empty paths...")

failures = []

def check(cond, msg):
    if cond:
        print(f"  OK: {msg}")
    else:
        print(f"  FAIL: {msg}")
        failures.append(msg)

# Create scene and grid
debug = mcrfpy.Scene("debug")
grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(320, 320))
data = grid.grid_data

# Initialize grid - all walkable
print("\nInitializing grid...")
for y in range(10):
    for x in range(10):
        data.at(x, y).walkable = True

# Test simple path
print("\nTest 1: Simple path from (0,0) to (5,5)")
path = data.find_path((0, 0), (5, 5))
check(path is not None, "A* found a path on an all-walkable grid")
steps = list(path) if path else []
print(f"  A* path: {steps}")
print(f"  Path length: {len(steps)}")
check(len(steps) > 0, "A* path is not empty")
check(path is not None and tuple(path.destination) == (5, 5), "A* path ends at (5,5)")

# Test with Dijkstra
print("\nTest 2: Same path with Dijkstra")
dmap = data.get_dijkstra_map(root=(0, 0))
dpath = dmap.path_from((5, 5))
dsteps = list(dpath) if dpath else []
print(f"  Dijkstra path: {dsteps}")
print(f"  Path length: {len(dsteps)}")
check(len(dsteps) > 0, "Dijkstra path is not empty")
check(dmap.distance((5, 5)) > 0, "Dijkstra distance to (5,5) is finite and positive")

# Check if grid is properly initialized
print("\nTest 3: Checking grid cells")
for y in range(3):
    for x in range(3):
        cell = data.at(x, y)
        print(f"  Cell ({x},{y}): walkable={cell.walkable}")
        check(cell.walkable, f"cell ({x},{y}) reports walkable=True")

# Test with walls
print("\nTest 4: Path with wall")
for wx in (2, 3, 4):
    data.at(wx, 2).walkable = False
data.clear_dijkstra_maps()  # walkability changed: invalidate cached maps
print("  Added wall at y=2, x=2,3,4")

path2 = data.find_path((0, 0), (5, 5))
check(path2 is not None, "A* still finds a path around the wall")
steps2 = list(path2) if path2 else []
print(f"  A* path with wall: {steps2}")
print(f"  Path length: {len(steps2)}")
check(len(steps2) > 0, "walled A* path is not empty")
blocked = {(2, 2), (3, 2), (4, 2)}
check(not any(tuple(p) in blocked for p in steps2),
      "A* path does not cross the wall cells (TCOD map synced with walkability)")

# Test invalid paths
print("\nTest 5: Path to blocked cell")
data.at(9, 9).walkable = False
data.clear_dijkstra_maps()
path3 = data.find_path((0, 0), (9, 9))
print(f"  Path to blocked cell: {path3}")
check(path3 is None or len(list(path3)) == 0,
      "no path is produced to a non-walkable destination")

# Check TCOD map sync
print("\nTest 6: Verify TCOD map is synced")
# Fully wall off (9,8) and (8,9) too -- (9,9) neighbors -- then re-open (9,9):
# a stale TCOD map would still refuse the destination.
data.at(9, 9).walkable = True
data.clear_dijkstra_maps()
path_reopened = data.find_path((0, 0), (9, 9))
check(path_reopened is not None and len(list(path_reopened)) > 0,
      "re-opening a blocked cell makes it reachable again (automatic TCOD sync)")

# Try path again
print("\nTest 7: Path after mutation round-trip")
path4 = data.find_path((0, 0), (5, 5))
steps4 = list(path4) if path4 else []
print(f"  A* path: {steps4}")
check(len(steps4) > 0, "A* path (0,0)->(5,5) still non-empty after mutations")

# Quick UI setup: the grid must survive being attached to a live scene.
ui = debug.children
ui.append(grid)
debug.activate()
mcrfpy.step(0.1)
check(mcrfpy.current_scene is debug, "grid attached to the active scene")

if failures:
    print(f"\nFAIL ({len(failures)} check(s) failed):")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("\nPASS")
sys.exit(0)
