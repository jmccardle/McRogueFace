#!/usr/bin/env python3
"""
A* vs Dijkstra Comparison
=========================

Verifies that A* (single target) and Dijkstra (multi-target flood) agree on the
cost of the shortest route through an obstacle course, that both produce legal,
contiguous, walkable paths, and that the Dijkstra distance field is consistent
with the paths it hands back.

API notes (updated for the current engine):
  * Pathfinding lives on GridData: grid.find_path(start, end) -> AStarPath|None,
    grid.get_dijkstra_map(root=...) -> DijkstraMap (.distance(pos), .path_from(pos)).
    The old grid.compute_astar_path / compute_dijkstra / get_dijkstra_path are gone.
  * GridPoint has no .color -- cell coloring is done with a ColorLayer.
  * add_layer() takes a layer OBJECT and no keyword arguments.
"""

import mcrfpy
import sys

# Colors
WALL_COLOR = mcrfpy.Color(40, 20, 20)
FLOOR_COLOR = mcrfpy.Color(60, 60, 80)
ASTAR_COLOR = mcrfpy.Color(0, 255, 0)      # Green for A*
DIJKSTRA_COLOR = mcrfpy.Color(0, 150, 255) # Blue for Dijkstra
START_COLOR = mcrfpy.Color(255, 100, 100)  # Red for start
END_COLOR = mcrfpy.Color(255, 255, 100)    # Yellow for end

GRID_W, GRID_H = 30, 20

# Global state
grid = None
color_layer = None
start_pos = (5, 10)
end_pos = (27, 10)  # Changed from 25 to 27 to avoid the wall

failures = []

def check(condition, message):
    """Record a failed assertion instead of aborting, so we report every problem."""
    if condition:
        print(f"  PASS: {message}")
    else:
        print(f"  FAIL: {message}")
        failures.append(message)

def create_map():
    """Create a map with obstacles to show pathfinding differences"""
    global grid, color_layer

    # Create grid (view + backing GridData)
    grid = mcrfpy.Grid(grid_size=(GRID_W, GRID_H), pos=(100, 100), size=(600, 400))
    grid.fill_color = mcrfpy.Color(0, 0, 0)

    # Add color layer for cell coloring (GridPoint.color no longer exists)
    color_layer = mcrfpy.ColorLayer(name="color", z_index=-1)
    grid.grid_data.add_layer(color_layer)

    # Initialize all as floor
    for y in range(GRID_H):
        for x in range(GRID_W):
            grid.grid_data.at(x, y).walkable = True
            color_layer.set((x, y), FLOOR_COLOR)

    # Create obstacles that make A* and Dijkstra differ
    obstacles = [
        # Vertical wall with gaps
        [(15, y) for y in range(3, 17) if y not in [8, 12]],
        # Horizontal walls
        [(x, 5) for x in range(10, 20)],
        [(x, 15) for x in range(10, 20)],
        # Maze-like structure
        [(x, 10) for x in range(20, 25)],
        [(25, y) for y in range(5, 15)],
    ]

    walls = set()
    for obstacle_group in obstacles:
        for x, y in obstacle_group:
            grid.grid_data.at(x, y).walkable = False
            color_layer.set((x, y), WALL_COLOR)
            walls.add((x, y))

    # Mark start and end
    color_layer.set(start_pos, START_COLOR)
    color_layer.set(end_pos, END_COLOR)

    # Dijkstra maps are cached; walkability just changed, so invalidate.
    grid.grid_data.clear_dijkstra_maps()
    return walls

def validate_path(cells, label, origin, destination):
    """A path must be contiguous, walkable, and actually arrive at `destination`.

    Both find_path() and DijkstraMap.path_from() use the same convention (#375):
    the returned path EXCLUDES the origin and ENDS at the destination. The two
    differ only in which endpoint is which -- A* is asked start->end, while a
    Dijkstra map rooted at start is queried from end, so it walks end->start.
    """
    check(len(cells) > 0, f"{label}: path is non-empty")
    if not cells:
        return

    check(cells[-1] == destination,
          f"{label}: path ends at {destination} (got {cells[-1]})")
    check(origin not in cells, f"{label}: path excludes its origin {origin}")

    # The first cell must be a single step from the origin.
    prev = origin
    contiguous = True
    walkable = True
    for (x, y) in cells:
        dx, dy = abs(x - prev[0]), abs(y - prev[1])
        if max(dx, dy) != 1:
            contiguous = False
        if not grid.grid_data.at(x, y).walkable:
            walkable = False
        prev = (x, y)
    check(contiguous, f"{label}: every step moves exactly one cell (incl. from start)")
    check(walkable, f"{label}: every cell on the path is walkable")

def path_cells(path):
    return [(int(v.x), int(v.y)) for v in path]

def show_astar():
    """Compute + color the A* path. Returns its cells."""
    path = grid.grid_data.find_path(start_pos, end_pos)
    check(path is not None, "A*: a path exists through the obstacle course")
    if path is None:
        return []

    check((int(path.destination.x), int(path.destination.y)) == end_pos,
          "A*: .destination is the requested end cell")

    # NOTE: AStarPath is a *consuming* iterator -- iterating it walks the path,
    # so .remaining must be read before draining it.
    expected = path.remaining
    cells = path_cells(path)
    check(expected == len(cells),
          f"A*: .remaining ({expected}) matches the iterated length ({len(cells)})")
    check(path.remaining == 0, "A*: iterating the path consumes it (.remaining -> 0)")

    for (x, y) in cells:
        if (x, y) != start_pos and (x, y) != end_pos:
            color_layer.set((x, y), ASTAR_COLOR)

    status_text.text = f"A* Path: {len(cells)} steps (optimized for single target)"
    status_text.fill_color = ASTAR_COLOR
    return cells

def show_dijkstra(walls):
    """Compute the Dijkstra flood from start, color it, return the path cells."""
    dmap = grid.grid_data.get_dijkstra_map(root=start_pos)
    check((int(dmap.root.x), int(dmap.root.y)) == start_pos,
          "Dijkstra: map root is the start cell")

    # The distance field must be defined on reachable floor and undefined on walls.
    check(dmap.distance(start_pos) == 0.0, "Dijkstra: distance to the root itself is 0")
    end_dist = dmap.distance(end_pos)
    check(end_dist is not None and end_dist > 0,
          f"Dijkstra: end cell is reachable (distance={end_dist})")

    wall_distances_defined = [w for w in walls if dmap.distance(w) is not None]
    check(not wall_distances_defined,
          f"Dijkstra: unwalkable cells have no distance ({len(wall_distances_defined)} leaked)")

    # Color cells by distance (showing exploration)
    max_dist = 40.0
    for y in range(GRID_H):
        for x in range(GRID_W):
            if grid.grid_data.at(x, y).walkable:
                dist = dmap.distance((x, y))
                if dist is not None and dist < max_dist:
                    intensity = int(255 * (1 - dist / max_dist))
                    color_layer.set((x, y), mcrfpy.Color(0, intensity // 2, intensity))

    # Get the actual path back to the root
    cells = path_cells(dmap.path_from(end_pos))

    for (x, y) in cells:
        if (x, y) != start_pos and (x, y) != end_pos:
            color_layer.set((x, y), DIJKSTRA_COLOR)

    color_layer.set(start_pos, START_COLOR)
    color_layer.set(end_pos, END_COLOR)

    status_text.text = f"Dijkstra: {len(cells)} steps (explores all directions)"
    status_text.fill_color = DIJKSTRA_COLOR
    return cells, dmap

def show_both(astar_cells, dijkstra_cells, dmap):
    """Compare the two routes. Different cells are fine; different COST is not."""
    print(f"  A*      : {astar_cells}")
    print(f"  Dijkstra: {dijkstra_cells}")

    # Both algorithms are optimal, so they must agree on the number of steps
    # even if they break ties through different cells.
    check(len(astar_cells) == len(dijkstra_cells),
          f"A* and Dijkstra agree on path length (A*={len(astar_cells)}, "
          f"Dijkstra={len(dijkstra_cells)})")

    # The Dijkstra distance field must be monotonically increasing along the
    # A* route - i.e. the flood is consistent with the single-target search.
    monotonic = True
    prev = dmap.distance(start_pos)
    for cell in astar_cells:
        d = dmap.distance(cell)
        if d is None or d <= prev:
            monotonic = False
            break
        prev = d
    check(monotonic, "Dijkstra distance increases at every step along the A* path")

    different_cells = [c for c in dijkstra_cells if c not in astar_cells]

    status_text.text = (f"Both paths: A*={len(astar_cells)} steps, "
                        f"Dijkstra={len(dijkstra_cells)} steps")
    if different_cells:
        info_text.text = f"Paths differ at {len(different_cells)} cells"
    else:
        info_text.text = "Paths are identical"
    print(f"  {info_text.text}")

# ---------------------------------------------------------------------------
print("A* vs Dijkstra Pathfinding Comparison")
print("=====================================")
print("A* is optimized for single-target pathfinding")
print("Dijkstra explores in all directions (good for multiple targets)")
print()

walls = create_map()

# Set up UI
pathfinding_comparison = mcrfpy.Scene("pathfinding_comparison")
ui = pathfinding_comparison.children
ui.append(grid)

title = mcrfpy.Caption(pos=(250, 20), text="A* vs Dijkstra Pathfinding")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

status_text = mcrfpy.Caption(pos=(100, 60), text="Comparing A* and Dijkstra")
status_text.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(status_text)

info_text = mcrfpy.Caption(pos=(100, 520), text="")
info_text.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(info_text)

legend1 = mcrfpy.Caption(pos=(100, 540), text="Red=Start, Yellow=End, Green=A*, Blue=Dijkstra")
legend1.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(legend1)

legend2 = mcrfpy.Caption(pos=(100, 560), text="Dark=Walls, Light=Floor")
legend2.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(legend2)

pathfinding_comparison.activate()

# Sanity: the ColorLayer really is the coloring mechanism now.
color_layer.set((0, 0), START_COLOR)
_c = color_layer.at((0, 0))
check((_c.r, _c.g, _c.b) == (255, 100, 100),
      "ColorLayer.set/.at round-trips a cell color")
color_layer.set((0, 0), FLOOR_COLOR)

print("\n[A*]")
astar_cells = show_astar()
# A* is asked start -> end.
validate_path(astar_cells, "A*", origin=start_pos, destination=end_pos)

print("\n[Dijkstra]")
dijkstra_cells, dmap = show_dijkstra(walls)
# The Dijkstra map is ROOTED at start_pos and queried FROM end_pos, so its path
# runs end -> start: the origin and destination are the mirror of A*'s.
validate_path(dijkstra_cells, "Dijkstra", origin=end_pos, destination=start_pos)

print("\n[Both]")
show_both(astar_cells, dijkstra_cells, dmap)

# Force a render so the colored comparison is actually drawn.
mcrfpy.automation.screenshot("astar_vs_dijkstra.png")

print()
if failures:
    print(f"FAIL: {len(failures)} check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("PASS")
sys.exit(0)
