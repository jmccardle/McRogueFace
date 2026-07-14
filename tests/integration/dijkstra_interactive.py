#!/usr/bin/env python3
"""
Dijkstra Pathfinding Interactive Demo (headless self-test)
==========================================================

Visualization + verification of Dijkstra pathfinding between entities.

Controls (when run with a window):
- Press 1/2/3 to select the first entity
- Press A/B/C to select the second entity
- Space to clear selection
- Q or ESC to quit

The path between selected entities is highlighted on a ColorLayer.

Under --headless the same selection logic is driven programmatically through the
key handler and the resulting paths / distances / highlight colors are asserted.
Entity 1 lives in a sealed room, so it must be unreachable from the others;
entities 2 and 3 are separated by a long wall and must be reachable around it.
"""

import mcrfpy
from mcrfpy import automation
import sys

# Colors - using more distinct values
WALL_COLOR = mcrfpy.Color(60, 30, 30)
FLOOR_COLOR = mcrfpy.Color(100, 100, 120)  # Darker floor for better contrast
PATH_COLOR = mcrfpy.Color(50, 255, 50)     # Bright green for path
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
first_point = None
second_point = None
last_path = None
failures = []

def check(condition, message):
    """Record a failed assertion without aborting the run"""
    if not condition:
        failures.append(message)
        print(f"FAIL: {message}")
    return condition

# Define the map layout from user's specification
# . = floor, W = wall, E = entity position
map_layout = [
    "..............",  # Row 0
    "..W.....WWWW..",  # Row 1
    "..W.W...W.EW..",  # Row 2
    "..W.....W..W..",  # Row 3
    "..W...E.WWWW..",  # Row 4
    "E.W...........",  # Row 5
    "..W...........",  # Row 6
    "..W...........",  # Row 7
    "..W.WWW.......",  # Row 8
    "..............",  # Row 9
]

def create_map():
    """Create the interactive map with the layout specified by the user"""
    global grid, grid_data, color_layer, entities

    # Create grid - 14x10 as specified
    grid = mcrfpy.Grid(grid_size=(14, 10))
    grid.fill_color = mcrfpy.Color(0, 0, 0)
    grid_data = grid.grid_data

    # Add color layer for cell coloring (GridPoint has no .color anymore)
    color_layer = mcrfpy.ColorLayer(name="color", z_index=-1)
    grid_data.add_layer(color_layer)

    # Create the map
    entity_positions = []
    for y, row in enumerate(map_layout):
        for x, char in enumerate(row):
            cell = grid_data.at(x, y)

            if char == 'W':
                # Wall
                cell.walkable = False
                cell.transparent = False
                color_layer.set((x, y), WALL_COLOR)
            else:
                # Floor
                cell.walkable = True
                cell.transparent = True
                color_layer.set((x, y), FLOOR_COLOR)

                if char == 'E':
                    # Entity position
                    entity_positions.append((x, y))

    # Create entities at marked positions
    entities = []
    for i, (x, y) in enumerate(entity_positions):
        entity = mcrfpy.Entity(grid_pos=(x, y))
        entity.sprite_index = 49 + i  # '1', '2', '3'
        grid_data.entities.append(entity)
        entities.append(entity)

    return grid

def entity_cell(entity):
    """Logical cell of an entity as an (x, y) int tuple"""
    cp = entity.cell_pos
    return (int(cp.x), int(cp.y))

def clear_path_highlight():
    """Clear any existing path highlighting"""
    # Reset all floor tiles to original color
    for y in range(grid_data.grid_h):
        for x in range(grid_data.grid_w):
            if grid_data.at(x, y).walkable:
                color_layer.set((x, y), FLOOR_COLOR)

def highlight_path():
    """Highlight the path between selected entities. Returns the path (may be empty)."""
    global last_path
    last_path = None
    if first_point is None or second_point is None:
        return None

    # Clear previous highlighting
    clear_path_highlight()

    # Get entities
    entity1 = entities[first_point]
    entity2 = entities[second_point]
    start = entity_cell(entity1)
    end = entity_cell(entity2)

    # Compute Dijkstra from first entity; walkability is static, but clear the
    # cache so each selection recomputes against the current grid.
    grid_data.clear_dijkstra_maps()
    dijkstra = grid_data.get_dijkstra_map(root=start)

    distance = dijkstra.distance(end)
    path = [] if distance is None else [(int(v.x), int(v.y)) for v in dijkstra.path_from(end)]

    if path:
        # Highlight the path
        for x, y in path:
            if grid_data.at(x, y).walkable:
                color_layer.set((x, y), PATH_COLOR)

        # Also highlight start and end with entity colors
        color_layer.set(start, ENTITY_COLORS[first_point])
        color_layer.set(end, ENTITY_COLORS[second_point])

        info_text.text = (f"Path: Entity {first_point+1} to Entity {second_point+1} - "
                          f"{len(path)} steps, {distance:.1f} units")
    else:
        info_text.text = f"No path between Entity {first_point+1} and Entity {second_point+1}"

    print(f"  {info_text.text}")
    last_path = path
    return path

def handle_keypress(key, action):
    """Handle keyboard input"""
    global first_point, second_point

    if action != mcrfpy.InputState.PRESSED:
        return

    # Number keys for first entity
    if key in (mcrfpy.Key.NUM_1, mcrfpy.Key.NUM_2, mcrfpy.Key.NUM_3):
        first_point = {mcrfpy.Key.NUM_1: 0, mcrfpy.Key.NUM_2: 1, mcrfpy.Key.NUM_3: 2}[key]
        status_text.text = (f"First: Entity {first_point+1} | "
                            f"Second: {f'Entity {second_point+1}' if second_point is not None else '?'}")
        highlight_path()

    # Letter keys for second entity
    elif key in (mcrfpy.Key.A, mcrfpy.Key.B, mcrfpy.Key.C):
        second_point = {mcrfpy.Key.A: 0, mcrfpy.Key.B: 1, mcrfpy.Key.C: 2}[key]
        status_text.text = (f"First: {f'Entity {first_point+1}' if first_point is not None else '?'} | "
                            f"Second: Entity {second_point+1}")
        highlight_path()

    # Clear selection
    elif key == mcrfpy.Key.SPACE:
        first_point = None
        second_point = None
        clear_path_highlight()
        status_text.text = "Press 1/2/3 for first entity, A/B/C for second"
        info_text.text = "Space to clear, Q to quit"

    # Quit
    elif key in (mcrfpy.Key.Q, mcrfpy.Key.ESCAPE):
        print("\nExiting Dijkstra interactive demo...")
        sys.exit(0)

# Create the visualization
print("Dijkstra Pathfinding Interactive Demo")
print("=====================================")
print("Controls:")
print("  1/2/3 - Select first entity")
print("  A/B/C - Select second entity")
print("  Space - Clear selection")
print("  Q/ESC - Quit")

dijkstra_interactive = mcrfpy.Scene("dijkstra_interactive")

# Create map
grid = create_map()

# Set up UI
ui = dijkstra_interactive.children
ui.append(grid)

# Scale and position grid for better visibility
grid.size = (560, 400)  # 14*40, 10*40
grid.pos = (120, 60)

# Add title
title = mcrfpy.Caption(pos=(250, 10), text="Dijkstra Pathfinding Interactive")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Add status text
status_text = mcrfpy.Caption(pos=(120, 480), text="Press 1/2/3 for first entity, A/B/C for second")
status_text.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(status_text)

# Add info text
info_text = mcrfpy.Caption(pos=(120, 500), text="Space to clear, Q to quit")
info_text.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(info_text)

# Add legend
legend1 = mcrfpy.Caption(pos=(120, 540), text="Entities: 1=Red 2=Green 3=Blue")
legend1.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(legend1)

legend2 = mcrfpy.Caption(pos=(120, 560), text="Colors: Dark=Wall Light=Floor Green=Path")
legend2.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(legend2)

# Mark entity positions with colored indicators
for i, entity in enumerate(entities):
    ex, ey = entity_cell(entity)
    marker = mcrfpy.Caption(pos=(120 + ex * 40 + 15, 60 + ey * 40 + 10), text=str(i+1))
    marker.fill_color = ENTITY_COLORS[i]
    marker.outline = 1
    marker.outline_color = mcrfpy.Color(0, 0, 0)
    ui.append(marker)

# Set up input handling
dijkstra_interactive.on_key = handle_keypress

# Show the scene
dijkstra_interactive.activate()

print("\nVisualization ready!")
print("Entities are at:")
for i, entity in enumerate(entities):
    print(f"  Entity {i+1}: {entity_cell(entity)}")

# --- Verification: drive the same selection logic the keyboard would ---

check(len(entities) == 3, f"expected 3 entities from map layout, got {len(entities)}")
check(entity_cell(entities[0]) == (10, 2), f"entity 1 at {entity_cell(entities[0])}, expected (10, 2)")
check(entity_cell(entities[1]) == (6, 4), f"entity 2 at {entity_cell(entities[1])}, expected (6, 4)")
check(entity_cell(entities[2]) == (0, 5), f"entity 3 at {entity_cell(entities[2])}, expected (0, 5)")

def press(key):
    handle_keypress(key, mcrfpy.InputState.PRESSED)

# Entity 2 -> Entity 3: reachable, but only by going around the long x=2 wall.
print("\nSelect: first=2 (key '2'), second=C (entity 3)")
press(mcrfpy.Key.NUM_2)
press(mcrfpy.Key.C)
path_2_3 = last_path
check(path_2_3,"expected a Dijkstra path between entity 2 (6,4) and entity 3 (0,5)")
if path_2_3:
    # The map is ROOTED at the first selection (entity 2) and queried FROM the second
    # (entity 3), so the walk runs entity3 -> entity2: per #375 it excludes its origin
    # (0,5) and ends at the root (6,4).
    check(path_2_3[-1] == (6, 4),
          f"path should end at the root, entity 2 (6,4); ended at {path_2_3[-1]}")
    check((0, 5) not in path_2_3, "path should exclude its origin, entity 3 (0,5)")
    check(all(grid_data.at(x, y).walkable for x, y in path_2_3),
          "Dijkstra path crosses a non-walkable cell")
    # The wall at x=2 spans rows 1..8, so the path must detour through row 0 or row 9
    check(any(y in (0, 9) for x, y in path_2_3),
          "path should detour around the x=2 wall via row 0 or row 9")
    # Path cells must have been repainted with PATH_COLOR (except the entity endpoints)
    mid = path_2_3[len(path_2_3) // 2]
    if mid not in ((0, 5), (6, 4)):
        c = color_layer.at(*mid)
        check((c.r, c.g, c.b) == (PATH_COLOR.r, PATH_COLOR.g, PATH_COLOR.b),
              f"path cell {mid} not highlighted with PATH_COLOR, got ({c.r},{c.g},{c.b})")
    ec = color_layer.at(0, 5)
    check((ec.r, ec.g, ec.b) == (ENTITY_COLORS[2].r, ENTITY_COLORS[2].g, ENTITY_COLORS[2].b),
          "destination entity cell not painted with its entity color")

# Entity 1 is sealed inside the walled room: no path in or out.
print("\nSelect: first=1 (key '1'), second=C (entity 3)")
press(mcrfpy.Key.NUM_1)
press(mcrfpy.Key.C)
path_1_3 = last_path
check(not path_1_3, f"entity 1 is walled in; expected no path to entity 3, got {path_1_3}")
check("No path" in info_text.text, f"info text should report no path, got {info_text.text!r}")

grid_data.clear_dijkstra_maps()
d_sealed = grid_data.get_dijkstra_map(root=entity_cell(entities[0])).distance(entity_cell(entities[1]))
check(d_sealed is None, f"distance from sealed entity 1 to entity 2 should be None, got {d_sealed}")

# Space clears the selection and restores floor colors
print("\nSelect: Space (clear)")
press(mcrfpy.Key.SPACE)
check(first_point is None and second_point is None, "Space should clear both selections")
fc = color_layer.at(0, 0)
check((fc.r, fc.g, fc.b) == (FLOOR_COLOR.r, FLOOR_COLOR.g, FLOOR_COLOR.b),
      "clear_path_highlight should restore FLOOR_COLOR on walkable cells")
wc = color_layer.at(2, 1)
check((wc.r, wc.g, wc.b) == (WALL_COLOR.r, WALL_COLOR.g, WALL_COLOR.b),
      "wall cells must keep WALL_COLOR after clearing the path")

# Render once (headless render is free of sim time) to prove the scene draws.
press(mcrfpy.Key.NUM_2)
press(mcrfpy.Key.C)
automation.screenshot("dijkstra_interactive.png")

if failures:
    print(f"\nFAIL: {len(failures)} check(s) failed")
    sys.exit(1)

print("\nPASS")
sys.exit(0)
