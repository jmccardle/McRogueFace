#!/usr/bin/env python3
"""
Debug version of Dijkstra pathfinding to diagnose visualization issues
"""

import mcrfpy
import sys

# Colors
WALL_COLOR = mcrfpy.Color(60, 30, 30)
FLOOR_COLOR = mcrfpy.Color(200, 200, 220)
PATH_COLOR = mcrfpy.Color(200, 250, 220)
ENTITY_COLORS = [
    mcrfpy.Color(255, 100, 100),  # Entity 1 - Red
    mcrfpy.Color(100, 255, 100),  # Entity 2 - Green
    mcrfpy.Color(100, 100, 255),  # Entity 3 - Blue
]

# Global state
grid = None
grid_data = None
color_layer = None
entities = []
failures = []

WALLS = [(5, 2), (5, 3), (5, 4), (5, 5), (5, 6)]

def check(condition, message):
    """Record a failed check instead of dying at the first one."""
    if not condition:
        print(f"  FAIL: {message}")
        failures.append(message)
    return condition

def create_simple_map():
    """Create a simple test map"""
    global grid, grid_data, color_layer, entities

    # Small grid for easy debugging
    grid = mcrfpy.Grid(grid_size=(10, 10))
    grid.fill_color = mcrfpy.Color(0, 0, 0)
    # Pathfinding + layers live on the shared GridData (#313/#361)
    grid_data = grid.grid_data

    # Add color layer for cell coloring
    color_layer = mcrfpy.ColorLayer(name="color", z_index=-1)
    grid_data.add_layer(color_layer)

    print("Initializing 10x10 grid...")

    # Initialize all as floor
    for y in range(10):
        for x in range(10):
            grid_data.at(x, y).walkable = True
            grid_data.at(x, y).transparent = True
            color_layer.set((x, y), FLOOR_COLOR)

    # Add a simple wall
    print("Adding walls at:")
    for x, y in WALLS:
        print(f"  Wall at ({x}, {y})")
        grid_data.at(x, y).walkable = False
        color_layer.set((x, y), WALL_COLOR)

    # Create 3 entities
    entity_positions = [(2, 5), (8, 5), (5, 8)]
    entities = []

    print("\nCreating entities at:")
    for i, (x, y) in enumerate(entity_positions):
        print(f"  Entity {i+1} at ({x}, {y})")
        entity = mcrfpy.Entity(grid_pos=(x, y), grid=grid)
        entity.sprite_index = 49 + i  # '1', '2', '3'
        entities.append(entity)

    return grid

def test_path_highlighting():
    """Test path highlighting with debug output"""
    print("\n" + "="*50)
    print("Testing path highlighting...")

    # Select first two entities
    e1 = entities[0]
    e2 = entities[1]

    # NOTE: entity.x/.y are PIXEL coordinates now; tile coords are grid_x/grid_y.
    print(f"\nEntity 1 position: ({e1.grid_x}, {e1.grid_y})")
    print(f"Entity 2 position: ({e2.grid_x}, {e2.grid_y})")

    # Use entity.path_to()
    print("\nCalling entity.path_to()...")
    path = e1.path_to(e2.grid_x, e2.grid_y)

    print(f"Path returned: {path}")
    print(f"Path length: {len(path)} steps")

    check(len(path) > 0, "entity.path_to() returned an empty path")
    if path:
        check(tuple(path[-1]) == (e2.grid_x, e2.grid_y),
              f"path does not end at the target: {path[-1]}")

        print("\nHighlighting path cells:")
        for i, (x, y) in enumerate(path):
            print(f"  Step {i}: ({x}, {y})")
            # Get current color for debugging
            cell = grid_data.at(x, y)
            old_c = color_layer.at((x, y))
            old_color = (old_c.r, old_c.g, old_c.b)

            # Set new color
            color_layer.set((x, y), PATH_COLOR)
            new_c = color_layer.at((x, y))
            new_color = (new_c.r, new_c.g, new_c.b)

            print(f"    Color changed from {old_color} to {new_color}")
            print(f"    Walkable: {cell.walkable}")
            check(cell.walkable, f"path routed through non-walkable cell ({x}, {y})")
            check((x, y) not in WALLS, f"path routed through a wall at ({x}, {y})")

    # Also test grid's Dijkstra methods
    print("\n" + "-"*30)
    print("Testing grid Dijkstra methods...")

    # compute_dijkstra/get_dijkstra_path/get_dijkstra_distance were replaced by
    # GridData.get_dijkstra_map() -> DijkstraMap.path_from()/.distance()
    dmap = grid_data.get_dijkstra_map(root=(e1.grid_x, e1.grid_y))
    grid_path = list(dmap.path_from((e2.grid_x, e2.grid_y)))
    distance = dmap.distance((e2.grid_x, e2.grid_y))

    print(f"Grid path: {grid_path}")
    print(f"Grid distance: {distance}")

    check(distance is not None, "Dijkstra distance to entity 2 is unreachable")
    check(len(grid_path) > 0, "Dijkstra path_from() returned an empty path")
    for x, y in grid_path:
        check(grid_data.at(x, y).walkable,
              f"Dijkstra path routed through non-walkable cell ({x}, {y})")
    # Dijkstra distance must be at least the straight-line-blocked A* step count
    check(distance is None or distance >= len(path) - 0.001,
          f"Dijkstra distance {distance} shorter than A* path length {len(path)}")

    # Verify colors were set
    print("\nVerifying cell colors after highlighting:")
    for x, y in path[:3]:  # Check first 3 cells
        c = color_layer.at((x, y))
        color = (c.r, c.g, c.b)
        expected = (PATH_COLOR.r, PATH_COLOR.g, PATH_COLOR.b)
        match = color == expected
        print(f"  Cell ({x}, {y}): color={color}, expected={expected}, match={match}")
        check(match, f"ColorLayer did not retain PATH_COLOR at ({x}, {y})")

    # Cells that were never on the path must keep their original color
    wall_c = color_layer.at(WALLS[0])
    check((wall_c.r, wall_c.g, wall_c.b) == (WALL_COLOR.r, WALL_COLOR.g, WALL_COLOR.b),
          "wall cell color was clobbered by path highlighting")

def handle_keypress(key, action):
    """Simple keypress handler"""
    if key == mcrfpy.Key.Q or key == mcrfpy.Key.Escape:
        print("\nExiting debug...")
        sys.exit(0)
    elif key == mcrfpy.Key.Space:
        print("\nSpace pressed - retesting path highlighting...")
        test_path_highlighting()

# Create the map
print("Dijkstra Debug Test")
print("===================")
dijkstra_debug = mcrfpy.Scene("dijkstra_debug")
grid = create_simple_map()

# Initial path test
test_path_highlighting()

# Set up UI
ui = dijkstra_debug.children
ui.append(grid)

# Position and scale
grid.pos = (50, 50)
grid.size = (400, 400)  # 10*40

# Add title
title = mcrfpy.Caption(pos=(50, 10), text="Dijkstra Debug - Press SPACE to retest, Q to quit")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Add debug info
info = mcrfpy.Caption(pos=(50, 470), text="Check console for debug output")
info.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(info)

# Set up scene
dijkstra_debug.on_key = handle_keypress
dijkstra_debug.activate()

# Render once to prove the highlighted grid actually draws (the original test's
# "if you don't see the path there may be a rendering issue" concern).
mcrfpy.step(0.016)
mcrfpy.automation.screenshot("dijkstra_debug.png")

print("\n" + "="*50)
if failures:
    print(f"FAIL: {len(failures)} check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("PASS")
sys.exit(0)
