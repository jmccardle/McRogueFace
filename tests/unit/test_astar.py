#!/usr/bin/env python3
"""
Test A* Pathfinding Implementation
==================================

Compares A* (GridData.find_path) with Dijkstra (GridData.get_dijkstra_map)
and verifies path validity around obstacles.

API notes (current contract):
  - The old grid.compute_astar_path/compute_dijkstra/get_dijkstra_path methods are gone.
    A* is now GridData.find_path(start, end, ...) -> AStarPath | None
    Dijkstra is now GridData.get_dijkstra_map(root=...) -> DijkstraMap (.path_from/.distance)
  - Pathfinding lives on GridData, not on the Grid view (mcrfpy.Grid is a GridView).
  - Headless has no automatic clock: timers only fire from mcrfpy.step().
"""

import mcrfpy
import sys
import time

print("A* Pathfinding Test")
print("==================")

failures = []

def check(cond, msg):
    if cond:
        print(f"   PASS: {msg}")
    else:
        print(f"   FAIL: {msg}")
        failures.append(msg)

# Create scene and grid
astar_test = mcrfpy.Scene("astar_test")
grid = mcrfpy.Grid(grid_size=(20, 20), pos=(50, 50), size=(400, 400))
data = grid.grid_data  # pathfinding lives on GridData

# Initialize grid - all walkable
for y in range(20):
    for x in range(20):
        data.at(x, y).walkable = True

# Create a wall barrier with a narrow passage.
# The barrier is 4 cells thick (x 8..11) and spans the full grid height, with a
# 1-cell-tall corridor carved through it at y == 10. Two corrections vs. the
# original test: (a) a partial-height wall could simply be rounded diagonally for
# the same cost, and (b) a single free cell inside a 4-thick wall is not a passage
# at all -- every neighbour is wall, so it can never be entered.
print("\nCreating wall with narrow passage...")
walls = set()
for y in range(20):
    for x in range(8, 12):
        if y == 10:  # corridor through the barrier, including (10, 10)
            continue
        data.at(x, y).walkable = False
        walls.add((x, y))

print(f"Wall cells: {len(walls)}, passage at (10, 10)")
data.clear_dijkstra_maps()

# Test points
start = (2, 10)
end = (18, 10)

print(f"\nFinding path from {start} to {end}")


def as_cells(path):
    return [(int(v.x), int(v.y)) for v in path]


def is_contiguous(cells):
    for a, b in zip(cells, cells[1:]):
        if max(abs(a[0] - b[0]), abs(a[1] - b[1])) != 1:
            return False
    return True


# Test 1: A* pathfinding
print("\n1. Testing A* pathfinding (find_path):")
start_time = time.time()
astar_path = data.find_path(start, end)
astar_time = time.time() - start_time
check(astar_path is not None, "A* found a path through the barrier")
# NOTE: iterating an AStarPath consumes it, so read .remaining before as_cells().
astar_remaining = astar_path.remaining if astar_path else 0
astar_cells = as_cells(astar_path) if astar_path else []
print(f"   A* path length: {len(astar_cells)}")
print(f"   A* time: {astar_time*1000:.3f} ms")
print(f"   First 5 steps: {astar_cells[:5]}")
check(bool(astar_cells) and astar_cells[-1] == end, "A* path terminates at the destination")
check(not (walls & set(astar_cells)), "A* path never enters a wall cell")
check(is_contiguous([start] + astar_cells), "A* path is contiguous from the start cell")
check((10, 10) in astar_cells, "A* path uses the narrow passage at (10, 10)")

# Test 2: A* path costs/endpoints via the AStarPath object
print("\n2. Testing AStarPath object:")
check(as_cells([astar_path.origin])[0] == start, "AStarPath.origin is the start cell")
check(as_cells([astar_path.destination])[0] == end, "AStarPath.destination is the end cell")
check(astar_remaining == len(astar_cells), "AStarPath.remaining matches path length")
check(astar_path.remaining == 0, "AStarPath is consumed once fully walked/iterated")

# Test 3: Dijkstra pathfinding for comparison
print("\n3. Testing Dijkstra pathfinding:")
start_time = time.time()
dmap = data.get_dijkstra_map(root=start)
dijkstra_path = dmap.path_from(end)
dijkstra_time = time.time() - start_time
dijkstra_cells = as_cells(dijkstra_path) if dijkstra_path else []
print(f"   Dijkstra path length: {len(dijkstra_cells)}")
print(f"   Dijkstra time: {dijkstra_time*1000:.3f} ms")
print(f"   First 5 steps: {dijkstra_cells[:5]}")
check(bool(dijkstra_cells), "Dijkstra found a path back to the root")
check(not (walls & set(dijkstra_cells)), "Dijkstra path never enters a wall cell")
check((10, 10) in dijkstra_cells, "Dijkstra path uses the narrow passage at (10, 10)")
check(dmap.distance(end) is not None, "Dijkstra distance to the destination is defined")

# Compare results - both are optimal, so step counts must agree
print("\nComparison:")
print(f"  A* steps: {len(astar_cells)}, Dijkstra steps: {len(dijkstra_cells)}")
check(len(astar_cells) == len(dijkstra_cells),
      "A* and Dijkstra agree on optimal step count")

# Test 4: no path (blocked destination inside the wall)
print("\n4. Testing with blocked destination:")
blocked_end = (10, 8)  # inside the wall
check(data.at(*blocked_end).walkable is False, "blocked destination is unwalkable")
no_path = data.find_path(start, blocked_end)
print(f"   Path to blocked cell: {no_path}")
check(no_path is None or len(no_path) == 0, "no path is returned for a blocked destination")

# Test 5: diagonal movement
print("\n5. Testing diagonal paths:")
diag_start = (0, 0)
diag_end = (5, 5)
diag_path = data.find_path(diag_start, diag_end)
diag_cells = as_cells(diag_path) if diag_path else []
print(f"   Diagonal path from {diag_start} to {diag_end}: {diag_cells}")
# Optimal diagonal path is 5 moves (one diagonal step per cell)
check(len(diag_cells) == 5, "diagonal path from (0,0) to (5,5) takes 5 steps")
check(diag_cells and diag_cells[-1] == diag_end, "diagonal path reaches the destination")

# Test 6: performance / corner-to-corner agreement
print("\n6. Performance test (corner to corner):")
results = {}
start_time = time.time()
corner_astar = as_cells(data.find_path((0, 0), (19, 19)) or [])
results["A*"] = (len(corner_astar), time.time() - start_time)
start_time = time.time()
corner_dmap = data.get_dijkstra_map(root=(0, 0))
corner_dijkstra = as_cells(corner_dmap.path_from((19, 19)) or [])
results["Dijkstra"] = (len(corner_dijkstra), time.time() - start_time)
for name, (steps, elapsed) in results.items():
    print(f"   {name}: {steps} steps in {elapsed*1000:.3f} ms")
check(len(corner_astar) > 0 and len(corner_dijkstra) > 0,
      "corner-to-corner path found by both algorithms")
check(len(corner_astar) == len(corner_dijkstra),
      "corner-to-corner step counts agree between A* and Dijkstra")

# Quick smoke test that the grid renders in a scene and the clock advances.
# Headless: mcrfpy.step() is the only clock; a Timer never fires on its own.
timer_fired = []


def visual_test(timer, runtime):
    print("\nVisual test timer fired")
    timer_fired.append(runtime)


ui = astar_test.children
ui.append(grid)
astar_test.activate()
visual_test_timer = mcrfpy.Timer("visual", visual_test, 100, once=True)

print("\nStarting visual test...")
for _ in range(10):
    mcrfpy.step(0.05)
check(bool(timer_fired), "scene timer fired after stepping the headless clock")

print("\nA* pathfinding tests completed!")
if failures:
    print(f"\nFAIL: {len(failures)} check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("PASS")
sys.exit(0)
