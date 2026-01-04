#!/usr/bin/env python3
"""Debug empty paths issue"""

import mcrfpy
import sys

print("Debugging empty paths...")

# Create scene and grid
debug = mcrfpy.Scene("debug")
grid = mcrfpy.Grid(grid_x=10, grid_y=10)

# Initialize grid - all walkable
print("\nInitializing grid...")
for y in range(10):
    for x in range(10):
        grid.at(x, y).walkable = True

# Test simple path
print("\nTest 1: Simple path from (0,0) to (5,5)")
path = grid.compute_astar_path(0, 0, 5, 5)
print(f"  A* path: {path}")
print(f"  Path length: {len(path)}")

# Test with Dijkstra
print("\nTest 2: Same path with Dijkstra")
grid.compute_dijkstra(0, 0)
dpath = grid.get_dijkstra_path(5, 5)
print(f"  Dijkstra path: {dpath}")
print(f"  Path length: {len(dpath)}")

# Check if grid is properly initialized
print("\nTest 3: Checking grid cells")
for y in range(3):
    for x in range(3):
        cell = grid.at(x, y)
        print(f"  Cell ({x},{y}): walkable={cell.walkable}")

# Test with walls
print("\nTest 4: Path with wall")
grid.at(2, 2).walkable = False
grid.at(3, 2).walkable = False
grid.at(4, 2).walkable = False
print("  Added wall at y=2, x=2,3,4")

path2 = grid.compute_astar_path(0, 0, 5, 5)
print(f"  A* path with wall: {path2}")
print(f"  Path length: {len(path2)}")

# Test invalid paths
print("\nTest 5: Path to blocked cell")
grid.at(9, 9).walkable = False
path3 = grid.compute_astar_path(0, 0, 9, 9)
print(f"  Path to blocked cell: {path3}")

# Check TCOD map sync
print("\nTest 6: Verify TCOD map is synced")
# Try to force a sync
print("  Checking if syncTCODMap exists...")
if hasattr(grid, 'sync_tcod_map'):
    print("  Calling sync_tcod_map()")
    grid.sync_tcod_map()
else:
    print("  No sync_tcod_map method found")

# Try path again
print("\nTest 7: Path after potential sync")
path4 = grid.compute_astar_path(0, 0, 5, 5)
print(f"  A* path: {path4}")

def timer_cb(timer, runtime):
    sys.exit(0)

# Quick UI setup
ui = debug.children
ui.append(grid)
debug.activate()
exit_timer = mcrfpy.Timer("exit", timer_cb, 100, once=True)

print("\nStarting timer...")