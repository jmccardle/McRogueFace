#!/usr/bin/env python3
"""
Dijkstra Pathfinding Test - Headless
====================================

Tests all Dijkstra functionality and generates a screenshot.

API notes (updated for the current engine):
  - Dijkstra maps come from grid.get_dijkstra_map(root=...) -> DijkstraMap.
    The old compute_dijkstra / get_dijkstra_distance / get_dijkstra_path
    methods are gone; DijkstraMap.distance(pos) and .path_from(pos) replace them.
  - GridPoint has no .color; per-cell coloring is done with a ColorLayer.
  - Entity.x/.y are pixel coordinates; the logical cell is entity.cell_pos.
  - Headless has no clock of its own: mcrfpy.step(dt) drives timers.
"""

import mcrfpy
from mcrfpy import automation
import sys

failures = []

def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"FAIL: {msg}")
    return cond

def create_test_map():
    """Create a test map with obstacles"""
    # Create grid
    grid = mcrfpy.Grid(grid_size=(20, 12))
    grid.fill_color = mcrfpy.Color(0, 0, 0)

    # Per-cell coloring now lives on a ColorLayer, not on GridPoint
    color_layer = mcrfpy.ColorLayer(name="cells")
    grid.add_layer(color_layer)

    # Initialize all cells as walkable floor
    for y in range(12):
        for x in range(20):
            grid.at(x, y).walkable = True
            grid.at(x, y).transparent = True
            color_layer.set((x, y), mcrfpy.Color(200, 200, 220))

    # Add walls to create interesting paths
    walls = [
        # Vertical wall in the middle
        (10, 1), (10, 2), (10, 3), (10, 4), (10, 5), (10, 6), (10, 7), (10, 8),
        # Horizontal walls
        (2, 6), (3, 6), (4, 6), (5, 6), (6, 6),
        (14, 6), (15, 6), (16, 6), (17, 6),
        # Some scattered obstacles
        (5, 2), (15, 2), (5, 9), (15, 9)
    ]

    for x, y in walls:
        grid.at(x, y).walkable = False
        color_layer.set((x, y), mcrfpy.Color(60, 30, 30))

    # Place test entities
    entities = []
    positions = [(2, 2), (17, 2), (9, 10)]
    colors = [
        mcrfpy.Color(255, 100, 100),  # Red
        mcrfpy.Color(100, 255, 100),  # Green
        mcrfpy.Color(100, 100, 255)   # Blue
    ]

    for i, (x, y) in enumerate(positions):
        entity = mcrfpy.Entity(grid_pos=(x, y))
        entity.sprite_index = 49 + i  # '1', '2', '3'
        grid.entities.append(entity)
        entities.append(entity)
        # Mark entity positions
        color_layer.set((x, y), colors[i])

    # Walkability was mutated after grid construction; drop any cached maps
    grid.clear_dijkstra_maps()

    return grid, color_layer, entities, walls


def test_dijkstra(grid, color_layer, entities, walls):
    """Test Dijkstra pathfinding between all entity pairs"""
    results = []

    for i in range(len(entities)):
        for j in range(len(entities)):
            if i != j:
                # Compute Dijkstra from entity i
                e1 = entities[i]
                e2 = entities[j]
                src = (int(e1.cell_pos.x), int(e1.cell_pos.y))
                dst = (int(e2.cell_pos.x), int(e2.cell_pos.y))

                dmap = grid.get_dijkstra_map(root=src)
                check(dmap.root == mcrfpy.Vector(src[0], src[1]),
                      f"dijkstra map root should be {src}, got {dmap.root}")

                # Get distance and path to entity j
                distance = dmap.distance(dst)
                path = list(dmap.path_from(dst))

                check(distance is not None, f"no distance from {src} to {dst}")
                check(len(path) > 0, f"no path from {src} to {dst}")

                if path:
                    # Root is reachable and the path is a real, connected walk
                    check(distance > 0, f"distance {src}->{dst} should be positive")
                    # Number of steps can't be fewer than the Chebyshev distance
                    cheb = max(abs(src[0] - dst[0]), abs(src[1] - dst[1]))
                    check(len(path) >= cheb,
                          f"path {src}->{dst} too short: {len(path)} < {cheb}")

                    cells = [(int(v.x), int(v.y)) for v in path]
                    for cx, cy in cells:
                        check(grid.at(cx, cy).walkable,
                              f"path {src}->{dst} crosses unwalkable cell {(cx, cy)}")
                        check((cx, cy) not in walls,
                              f"path {src}->{dst} crosses wall {(cx, cy)}")

                    # Consecutive path cells must be adjacent (8-way)
                    for a, b in zip(cells, cells[1:]):
                        check(max(abs(a[0] - b[0]), abs(a[1] - b[1])) == 1,
                              f"path {src}->{dst} jumps from {a} to {b}")

                    # The map is ROOTED at src and queried FROM dst, so the walk runs
                    # dst -> src. Per the #375 convention (shared with find_path) it
                    # EXCLUDES its origin (dst) and ENDS at its destination (src).
                    check(cells[-1] == src,
                          f"path from {dst} should end at the root {src}, ended at {cells[-1]}")
                    check(dst not in cells,
                          f"path from {dst} should exclude its origin {dst}")
                    check(max(abs(cells[0][0] - dst[0]), abs(cells[0][1] - dst[1])) == 1,
                          f"path from {dst} should begin one step away, began at {cells[0]}")

                    results.append(f"Path {i+1}→{j+1}: {len(path)} steps, {distance:.1f} units")

                    # Color one interesting path
                    if i == 0 and j == 2:  # Path from 1 to 3
                        for cx, cy in cells:
                            if (cx, cy) not in (src, dst) and grid.at(cx, cy).walkable:
                                color_layer.set((cx, cy), mcrfpy.Color(200, 250, 220))
                else:
                    results.append(f"Path {i+1}→{j+1}: No path found!")

    # Walls are unreachable: distance must be None, not a bogus number
    root = (int(entities[0].cell_pos.x), int(entities[0].cell_pos.y))
    dmap = grid.get_dijkstra_map(root=root)
    check(dmap.distance((10, 4)) is None,
          "distance to an unwalkable wall cell should be None")
    check(dmap.distance(root) == 0.0,
          f"distance from root to itself should be 0, got {dmap.distance(root)}")

    # Dijkstra distances are symmetric on a uniform-cost grid
    a = (int(entities[0].cell_pos.x), int(entities[0].cell_pos.y))
    b = (int(entities[1].cell_pos.x), int(entities[1].cell_pos.y))
    d_ab = grid.get_dijkstra_map(root=a).distance(b)
    d_ba = grid.get_dijkstra_map(root=b).distance(a)
    check(abs(d_ab - d_ba) < 0.01,
          f"distance should be symmetric: {a}->{b}={d_ab}, {b}->{a}={d_ba}")

    return results


def run_test(timer, runtime):
    """Timer callback to run tests"""
    global results
    results = test_dijkstra(grid, color_layer, entities, walls)

    # Update display with results
    y_pos = 380
    for result in results:
        caption = mcrfpy.Caption(text=result, pos=(50, y_pos))
        caption.fill_color = mcrfpy.Color(200, 200, 200)
        ui.append(caption)
        y_pos += 20


# Create test map
print("Creating Dijkstra pathfinding test...")
grid, color_layer, entities, walls = create_test_map()
results = None

# Set up UI
dijkstra_test = mcrfpy.Scene("dijkstra_test")
ui = dijkstra_test.children
ui.append(grid)

# Position and scale grid
grid.pos = (50, 50)
grid.size = (500, 300)

# Add title
title = mcrfpy.Caption(pos=(200, 10), text="Dijkstra Pathfinding Test")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Add legend
legend = mcrfpy.Caption(pos=(50, 360), text="Red=Entity1  Green=Entity2  Blue=Entity3  Cyan=Path 1->3")
legend.fill_color = mcrfpy.Color(180, 180, 180)
ui.append(legend)

# Set scene
dijkstra_test.activate()

# Run test after scene loads (one-shot timer). Headless has no clock of its own,
# so drive the timer forward explicitly with mcrfpy.step().
test_timer = mcrfpy.Timer("test", run_test, 100, once=True)
print("Running Dijkstra tests...")
for _ in range(10):
    mcrfpy.step(0.05)
    if results is not None:
        break

check(results is not None, "timer callback never fired; Dijkstra tests did not run")
if results:
    for line in results:
        print(line)
    check(len(results) == 6, f"expected 6 entity-pair results, got {len(results)}")
    check(all("No path found" not in r for r in results),
          "every entity pair should be mutually reachable")

# Rendering is orthogonal to sim time; force a render for the screenshot
try:
    automation.screenshot("dijkstra_test.png")
    print("Screenshot saved: dijkstra_test.png")
except Exception as e:
    check(False, f"Screenshot failed: {e}")

if failures:
    print(f"FAILED ({len(failures)} checks)")
    sys.exit(1)

print("PASS")
sys.exit(0)
