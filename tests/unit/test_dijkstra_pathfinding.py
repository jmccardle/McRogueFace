#!/usr/bin/env python3
"""
Test Dijkstra Pathfinding Implementation
========================================

Demonstrates:
1. Computing Dijkstra distance map from a root position
2. Getting distances to any position
3. Finding paths from any position back to the root
4. Multi-target pathfinding (flee/approach scenarios)

API notes (updated for current mcrfpy):
- The `mcrfpy.libtcod` module is gone. Its successor is the GridData Dijkstra API:
    grid.grid_data.get_dijkstra_map(root=(x, y)) -> DijkstraMap
    dmap.root / dmap.distance((x, y)) / dmap.path_from((x, y))
    grid.grid_data.clear_dijkstra_maps()   (invalidate after walkability changes)
- GridPoint has no .tilesprite/.color; tiles go on a TileLayer, colors on a ColorLayer.
"""

import mcrfpy
import sys

failures = []

def check(cond, message):
    """Record a failed check instead of aborting, so all checks run."""
    if not cond:
        failures.append(message)
        print(f"  FAIL: {message}")
    return cond

def adjacent(a, b):
    """True if a and b are the same cell or 8-way neighbors."""
    return abs(int(a[0]) - int(b[0])) <= 1 and abs(int(a[1]) - int(b[1])) <= 1

def create_test_grid():
    """Create a test grid with obstacles"""
    # Create grid (already has a default tile layer)
    grid = mcrfpy.Grid(grid_size=(20, 20))

    # Add color layer for cell coloring
    color_layer = mcrfpy.ColorLayer(name="color", z_index=-1)
    grid.add_layer(color_layer)

    data = grid.grid_data

    # Initialize all cells as walkable
    for y in range(data.grid_h):
        for x in range(data.grid_w):
            cell = grid.at(x, y)
            cell.walkable = True
            cell.transparent = True
            color_layer.set((x, y), mcrfpy.Color(50, 50, 50))

    # Create some walls to make pathfinding interesting
    # Vertical wall
    for y in range(5, 15):
        cell = grid.at(10, y)
        cell.walkable = False
        cell.transparent = False
        color_layer.set((10, y), mcrfpy.Color(100, 100, 100))

    # Horizontal wall
    for x in range(5, 15):
        if x != 10:  # (10, 10) is already part of the vertical wall
            cell = grid.at(x, 10)
            cell.walkable = False
            cell.transparent = False
            color_layer.set((x, 10), mcrfpy.Color(100, 100, 100))

    # Walkability changed after construction; drop any cached maps
    data.clear_dijkstra_maps()

    return grid, color_layer

def test_basic_dijkstra():
    """Test basic Dijkstra functionality"""
    print("\n=== Testing Basic Dijkstra ===")

    grid, _color_layer = create_test_grid()
    data = grid.grid_data

    # Compute Dijkstra map from position (5, 5)
    root_x, root_y = 5, 5
    print(f"Computing Dijkstra map from root ({root_x}, {root_y})")
    dmap = data.get_dijkstra_map(root=(root_x, root_y))
    check(dmap is not None, "get_dijkstra_map returned None")
    check((dmap.root.x, dmap.root.y) == (root_x, root_y),
          f"dmap.root {dmap.root} != root ({root_x}, {root_y})")

    # Test getting distances to various points
    # (x, y, expected) -- expected None means "unreachable"
    test_points = [
        (5, 5, 0.0),      # Root position
        (6, 5, 1.0),      # Adjacent
        (7, 5, 2.0),      # Two steps away
        (15, 15, None),   # Far corner: reachable, distance checked below
        (10, 10, None),   # On a wall: unreachable
    ]

    print("\nDistances from root:")
    for x, y, expected in test_points:
        distance = dmap.distance((x, y))
        if distance is None:
            print(f"  ({x:2}, {y:2}): UNREACHABLE")
        else:
            print(f"  ({x:2}, {y:2}): {distance:.1f}")

        if (x, y) == (10, 10):
            check(distance is None, "wall cell (10, 10) should be unreachable")
        elif (x, y) == (15, 15):
            # Reachable by going around the walls; exact cost depends on
            # diagonal_cost, but it must be finite and clearly non-trivial.
            check(distance is not None, "(15, 15) should be reachable around the walls")
            if distance is not None:
                check(distance > 10.0, f"(15, 15) distance {distance} implausibly short")
        else:
            check(distance is not None, f"({x}, {y}) should be reachable")
            if distance is not None:
                check(abs(distance - expected) < 0.001,
                      f"({x}, {y}) distance {distance} != expected {expected}")

    # Test getting paths
    print("\nPaths to root:")
    for x, y in [(15, 5), (15, 15), (5, 15)]:
        path = dmap.path_from((x, y))
        steps = list(path) if path else []
        if steps:
            print(f"  From ({x}, {y}): {len(steps)} steps")
            for i, step in enumerate(steps[:3]):
                print(f"    Step {i+1}: ({step.x}, {step.y})")
            if len(steps) > 3:
                print(f"    ... {len(steps)-3} more steps")
        else:
            print(f"  From ({x}, {y}): No path found")

        check(len(steps) > 0, f"no path from ({x}, {y}) back to root")
        if steps:
            # An AStarPath walks origin -> destination: successive steps must be
            # adjacent, the first step must neighbor the query position, and the
            # last step must be the root. (This is what find_path() returns.)
            cells = [(int(s.x), int(s.y)) for s in steps]
            check(adjacent(cells[0], (x, y)),
                  f"path from ({x}, {y}): first step {cells[0]} is not adjacent to the start")
            check(cells[-1] == (root_x, root_y),
                  f"path from ({x}, {y}) ends at {cells[-1]}, not the root ({root_x}, {root_y})")
            for a, b in zip(cells, cells[1:]):
                check(adjacent(a, b),
                      f"path from ({x}, {y}) jumps from {a} to {b} (not adjacent)")
            for cell in cells:
                check(grid.at(cell[0], cell[1]).walkable,
                      f"path from ({x}, {y}) crosses wall at {cell}")

def test_dijkstra_map_interface():
    """Test the DijkstraMap object interface (successor to the old libtcod module)"""
    print("\n=== Testing DijkstraMap Interface ===")

    grid, _color_layer = create_test_grid()
    data = grid.grid_data

    # Create dijkstra map (successor of libtcod.dijkstra_new + dijkstra_compute)
    dijkstra = data.get_dijkstra_map(root=(10, 2))
    print(f"Created Dijkstra map: {type(dijkstra).__name__}, root={dijkstra.root}")
    check(isinstance(dijkstra, mcrfpy.DijkstraMap),
          "get_dijkstra_map did not return a DijkstraMap")

    # Get distance (successor of libtcod.dijkstra_get_distance)
    distance = dijkstra.distance((10, 17))
    print(f"Distance to (10, 17): {distance}")
    check(distance is not None, "(10, 17) should be reachable from (10, 2)")

    # Get path (successor of libtcod.dijkstra_path_to)
    path = dijkstra.path_from((10, 17))
    steps = [(int(s.x), int(s.y)) for s in path] if path else []
    print(f"Path from (10, 17) to root: {len(steps)} steps -> {steps[:4]}...")
    check(len(steps) > 0, "no path from (10, 17) to root (10, 2)")
    if steps:
        check((path.origin.x, path.origin.y) == (10, 17), "AStarPath.origin is not the query pos")
        check((path.destination.x, path.destination.y) == (10, 2),
              "AStarPath.destination is not the root")
        check(adjacent(steps[0], (10, 17)),
              f"first step {steps[0]} is not adjacent to the start (10, 17)")
        check(steps[-1] == (10, 2), f"path ends at {steps[-1]}, not root (10, 2)")

    # step_from(pos) is documented as "single step from position toward root":
    # it must be the same as the first element of path_from(pos), and adjacent.
    step = dijkstra.step_from((10, 17))
    print(f"step_from((10, 17)) -> {step}")
    check(step is not None, "step_from returned None for a reachable cell")
    if step is not None:
        check(adjacent((int(step.x), int(step.y)), (10, 17)),
              f"step_from((10, 17)) returned ({int(step.x)}, {int(step.y)}), which is not adjacent")

    # Maps are cached per-root; asking again yields an equivalent map
    again = data.get_dijkstra_map(root=(10, 2))
    check((again.root.x, again.root.y) == (10, 2), "cached map lost its root")
    check(again.distance((10, 17)) == distance, "cached map distance changed")

def test_multi_target_scenario():
    """Test fleeing/approaching multiple targets"""
    print("\n=== Testing Multi-Target Scenario ===")

    grid, color_layer = create_test_grid()
    data = grid.grid_data

    # Place three "threats" and compute their Dijkstra maps
    threats = [(3, 3), (17, 3), (10, 17)]

    print("Computing threat distances...")
    threat_distances = []

    for i, (tx, ty) in enumerate(threats):
        # Mark threat position
        color_layer.set((tx, ty), mcrfpy.Color(255, 0, 0))

        # Compute Dijkstra from this threat
        dmap = data.get_dijkstra_map(root=(tx, ty))

        # Store distances for all cells
        distances = {}
        for y in range(data.grid_h):
            for x in range(data.grid_w):
                d = dmap.distance((x, y))
                if d is not None:
                    distances[(x, y)] = d

        threat_distances.append(distances)
        print(f"  Threat {i+1} at ({tx}, {ty}): {len(distances)} reachable cells")

        check(distances.get((tx, ty)) == 0.0,
              f"threat {i+1} root ({tx}, {ty}) should have distance 0")
        check(len(distances) > 100,
              f"threat {i+1} only reached {len(distances)} cells; map looks broken")
        check((10, 10) not in distances,
              f"threat {i+1} reached wall cell (10, 10)")

    # Find safest position (farthest from all threats)
    print("\nFinding safest position...")
    best_pos = None
    best_min_dist = 0

    for y in range(data.grid_h):
        for x in range(data.grid_w):
            # Skip if not walkable
            if not grid.at(x, y).walkable:
                continue

            # Get minimum distance to any threat
            min_dist = float('inf')
            for threat_dist in threat_distances:
                if (x, y) in threat_dist:
                    min_dist = min(min_dist, threat_dist[(x, y)])

            # Track best position
            if min_dist > best_min_dist and min_dist != float('inf'):
                best_min_dist = min_dist
                best_pos = (x, y)

    check(best_pos is not None, "no safest position found (all cells unreachable?)")
    if best_pos:
        print(f"Safest position: {best_pos} (min distance to threats: {best_min_dist:.1f})")
        check(grid.at(best_pos[0], best_pos[1]).walkable, "safest position is a wall")
        check(best_min_dist > 0, "safest position sits on top of a threat")
        # Mark safe position
        color_layer.set((best_pos[0], best_pos[1]), mcrfpy.Color(0, 255, 0))

    # Multi-source Dijkstra: one map rooted at ALL threats at once. Its distance
    # to any cell must equal the min over the individual per-threat maps.
    multi = data.get_dijkstra_map(roots=threats)
    mismatches = 0
    for (x, y), _ in list(threat_distances[0].items())[:200]:
        expected = min(td[(x, y)] for td in threat_distances if (x, y) in td)
        got = multi.distance((x, y))
        if got is None or abs(got - expected) > 0.001:
            mismatches += 1
    check(mismatches == 0,
          f"multi-source Dijkstra disagrees with min-of-single-source on {mismatches} cells")

def main():
    print("McRogueFace Dijkstra Pathfinding Test")
    print("=====================================")

    # Set up scene so the grid is actually attached to a live UI tree
    dijkstra_test = mcrfpy.Scene("dijkstra_test")
    grid, _color_layer = create_test_grid()
    grid.pos = (0, 0)
    grid.size = (400, 400)
    ui = dijkstra_test.children
    ui.append(grid)

    title = mcrfpy.Caption(text="Dijkstra Pathfinding Test", pos=(10, 10))
    title.fill_color = mcrfpy.Color(255, 255, 255)
    ui.append(title)

    dijkstra_test.activate()

    test_basic_dijkstra()
    test_dijkstra_map_interface()
    test_multi_target_scenario()

    print("\n=== Dijkstra Implementation Test Complete ===")
    if failures:
        print(f"\n{len(failures)} check(s) FAILED:")
        for f in failures:
            print(f"  - {f}")
        print("FAIL")
        sys.exit(1)

    print("Basic Dijkstra computation works")
    print("Distance queries work")
    print("Path finding works")
    print("DijkstraMap interface works")
    print("Multi-target scenarios work")
    print("PASS")
    sys.exit(0)

if __name__ == "__main__":
    main()
