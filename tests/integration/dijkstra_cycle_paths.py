#!/usr/bin/env python3
"""
Dijkstra Demo - Cycles Through Different Path Combinations
==========================================================

Shows paths between different entity pairs, skipping impossible paths.

Headless verification of the original demo's claims:
  - Entity 1 is walled into a pocket and can reach nobody.
  - Entities 2 and 3 can reach each other (both directions), so exactly two
    path combinations exist.
  - Each generated path is a contiguous chain of walkable cells ending on the
    target entity.
  - Cycling through the combinations recolors the ColorLayer accordingly.
"""

import mcrfpy
import sys

# High contrast colors
WALL_COLOR = mcrfpy.Color(40, 20, 20)      # Very dark red/brown
FLOOR_COLOR = mcrfpy.Color(60, 60, 80)     # Dark blue-gray
PATH_COLOR = mcrfpy.Color(0, 255, 0)       # Bright green
START_COLOR = mcrfpy.Color(255, 100, 100)  # Light red
END_COLOR = mcrfpy.Color(100, 100, 255)    # Light blue

# Global state
grid = None
grid_data = None
color_layer = None
entities = []
current_path_index = 0
path_combinations = []
current_path = []
failures = []

def check(condition, message):
    """Record a failed assertion without aborting the demo"""
    if not condition:
        failures.append(message)
        print(f"  FAIL: {message}")
    return condition

def create_map():
    """Create the map with entities"""
    global grid, grid_data, color_layer, entities

    # Create grid (grid_size= replaces the old grid_w=/grid_h= kwargs)
    grid = mcrfpy.Grid(grid_size=(14, 10))
    grid_data = grid.grid_data
    grid.fill_color = mcrfpy.Color(0, 0, 0)

    # Add color layer for cell coloring. Cells no longer have a .color;
    # ColorLayer objects are constructed then attached (add_layer takes no kwargs).
    color_layer = grid_data.add_layer(mcrfpy.ColorLayer(name="color", z_index=-1))

    # Map layout
    map_layout = [
        "..............",  # Row 0
        "..W.....WWWW..",  # Row 1
        "..W.W...W.EW..",  # Row 2 - Entity 1 at (10,2) is TRAPPED!
        "..W.....W..W..",  # Row 3
        "..W...E.WWWW..",  # Row 4 - Entity 2 at (6,4)
        "E.W...........",  # Row 5 - Entity 3 at (0,5)
        "..W...........",  # Row 6
        "..W...........",  # Row 7
        "..W.WWW.......",  # Row 8
        "..............",  # Row 9
    ]

    # Create the map
    entity_positions = []
    for y, row in enumerate(map_layout):
        for x, char in enumerate(row):
            cell = grid_data.at(x, y)

            if char == 'W':
                cell.walkable = False
                color_layer.set((x, y), WALL_COLOR)
            else:
                cell.walkable = True
                color_layer.set((x, y), FLOOR_COLOR)

                if char == 'E':
                    entity_positions.append((x, y))

    # Create entities
    entities = []
    for i, (x, y) in enumerate(entity_positions):
        entity = mcrfpy.Entity(grid_pos=(x, y), grid=grid)
        entity.sprite_index = 49 + i  # '1', '2', '3'
        entities.append(entity)

    print("Entities created:")
    for i, (x, y) in enumerate(entity_positions):
        print(f"  Entity {i+1} at ({x}, {y})")

    check(entity_positions == [(10, 2), (6, 4), (0, 5)],
          f"expected entities at [(10,2),(6,4),(0,5)], got {entity_positions}")

    # Check which entity is trapped
    print("\nChecking accessibility:")
    reachability = []
    for i, e in enumerate(entities):
        # Try to path to each other entity
        can_reach = []
        for j, other in enumerate(entities):
            if i != j:
                path = e.path_to(other.grid_x, other.grid_y)
                if path:
                    can_reach.append(j+1)

        reachability.append(can_reach)
        if not can_reach:
            print(f"  Entity {i+1} at ({e.grid_x}, {e.grid_y}) is TRAPPED!")
        else:
            print(f"  Entity {i+1} can reach entities: {can_reach}")

    # Entity 1 sits in a sealed pocket; entities 2 and 3 share the open area.
    check(reachability[0] == [], "Entity 1 should be trapped (no reachable entities)")
    check(reachability[1] == [3], f"Entity 2 should reach only Entity 3, got {reachability[1]}")
    check(reachability[2] == [2], f"Entity 3 should reach only Entity 2, got {reachability[2]}")

    # Generate valid path combinations (excluding trapped entity)
    global path_combinations
    path_combinations = []

    # Only paths between entities 2 and 3 (indices 1 and 2) will work
    # since entity 1 (index 0) is trapped
    if len(entities) >= 3:
        # Entity 2 to Entity 3
        path = entities[1].path_to(entities[2].grid_x, entities[2].grid_y)
        if path:
            path_combinations.append((1, 2, path))

        # Entity 3 to Entity 2
        path = entities[2].path_to(entities[1].grid_x, entities[1].grid_y)
        if path:
            path_combinations.append((2, 1, path))

    print(f"\nFound {len(path_combinations)} valid paths")
    check(len(path_combinations) == 2, f"expected 2 valid path combinations, got {len(path_combinations)}")

def validate_path(from_idx, to_idx, path):
    """A path must be a contiguous chain of walkable cells ending on the target"""
    e_from = entities[from_idx]
    e_to = entities[to_idx]

    check(len(path) > 0, f"path {from_idx+1}->{to_idx+1} is empty")
    if not path:
        return

    check(tuple(path[-1]) == (e_to.grid_x, e_to.grid_y),
          f"path {from_idx+1}->{to_idx+1} does not end on target: {path[-1]}")

    # path_to() excludes the entity's own cell, so walk from the entity position
    prev = (e_from.grid_x, e_from.grid_y)
    for (x, y) in path:
        check(grid_data.at(x, y).walkable, f"path crosses non-walkable cell ({x}, {y})")
        step = max(abs(x - prev[0]), abs(y - prev[1]))
        check(step == 1, f"path is not contiguous: {prev} -> ({x}, {y})")
        prev = (x, y)

def clear_path_colors():
    """Reset all floor tiles to original color"""
    global current_path

    for y in range(grid_data.grid_h):
        for x in range(grid_data.grid_w):
            cell = grid_data.at(x, y)
            if cell.walkable:
                color_layer.set((x, y), FLOOR_COLOR)

    current_path = []

def show_path(index):
    """Show a specific path combination"""
    global current_path_index, current_path

    if not path_combinations:
        status_text.text = "No valid paths available (Entity 1 is trapped!)"
        return

    current_path_index = index % len(path_combinations)
    from_idx, to_idx, path = path_combinations[current_path_index]

    # Clear previous path
    clear_path_colors()

    # Get entities
    e_from = entities[from_idx]
    e_to = entities[to_idx]

    # Color the path
    current_path = path
    if path:
        # Color start and end
        color_layer.set((e_from.grid_x, e_from.grid_y), START_COLOR)
        color_layer.set((e_to.grid_x, e_to.grid_y), END_COLOR)

        # Color intermediate steps. path_to() excludes the entity's own cell,
        # so every element except the last (the target) is an intermediate step.
        for (x, y) in path[:-1]:
            color_layer.set((x, y), PATH_COLOR)

    # Update status
    status_text.text = f"Path {current_path_index + 1}/{len(path_combinations)}: Entity {from_idx+1} -> Entity {to_idx+1} ({len(path)} steps)"

    # Update path display
    path_display = []
    for i, (x, y) in enumerate(path[:5]):  # Show first 5 steps
        path_display.append(f"({x},{y})")
    if len(path) > 5:
        path_display.append("...")
    path_text.text = "Path: " + " -> ".join(path_display) if path_display else "Path: None"

def handle_keypress(key_str, state):
    """Handle keyboard input"""
    global current_path_index
    if state == mcrfpy.InputState.RELEASED: return
    if key_str == mcrfpy.Key.ESCAPE:
        print("\nExiting...")
        sys.exit(0)
    elif key_str == mcrfpy.Key.N or key_str == mcrfpy.Key.SPACE:
        show_path(current_path_index + 1)
    elif key_str == mcrfpy.Key.P:
        show_path(current_path_index - 1)
    elif key_str == mcrfpy.Key.R:
        show_path(current_path_index)

# Create the demo
print("Dijkstra Path Cycling Demo")
print("==========================")
print("Note: Entity 1 is trapped by walls!")
print()

dijkstra_cycle = mcrfpy.Scene("dijkstra_cycle")

create_map()

# Set up UI
ui = dijkstra_cycle.children
ui.append(grid)

# Scale and position
grid.size = (560, 400)
grid.pos = (120, 100)

# Add title
title = mcrfpy.Caption(pos=(200, 20), text="Dijkstra Pathfinding - Cycle Paths")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Add status
status_text = mcrfpy.Caption(pos=(120, 60), text="Press SPACE to cycle paths")
status_text.fill_color = mcrfpy.Color(255, 255, 100)
ui.append(status_text)

# Add path display
path_text = mcrfpy.Caption(pos=(120, 520), text="Path: None")
path_text.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(path_text)

# Add controls
controls = mcrfpy.Caption(pos=(120, 540), text="SPACE/N=Next, P=Previous, R=Refresh, Q=Quit")
controls.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(controls)

# Add legend
legend = mcrfpy.Caption(pos=(120, 560), text="Red=Start, Blue=End, Green=Path, Dark=Wall")
legend.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(legend)

# Show first valid path
dijkstra_cycle.activate()
dijkstra_cycle.on_key = handle_keypress

# Display initial path
if path_combinations:
    show_path(0)
else:
    status_text.text = "No valid paths! Entity 1 is trapped!"

# --- Headless verification: cycle every combination the demo would show ---
print("\nCycling paths:")
for i in range(len(path_combinations)):
    show_path(i)
    from_idx, to_idx, path = path_combinations[current_path_index]
    print(f"  {status_text.text}")
    check(current_path_index == i, f"show_path({i}) selected index {current_path_index}")
    validate_path(from_idx, to_idx, path)

    # The colored overlay must reflect the displayed path
    e_from, e_to = entities[from_idx], entities[to_idx]
    check(color_layer.at((e_from.grid_x, e_from.grid_y)) == START_COLOR,
          "start cell not colored START_COLOR")
    check(color_layer.at((e_to.grid_x, e_to.grid_y)) == END_COLOR,
          "end cell not colored END_COLOR")
    for (x, y) in path[:-1]:
        check(color_layer.at((x, y)) == PATH_COLOR, f"path cell ({x},{y}) not colored PATH_COLOR")

# Cycling wraps around (what SPACE/N does)
show_path(len(path_combinations))
check(current_path_index == 0, "cycling past the last path should wrap to 0")

# Render once to prove the scene is drawable with the layers attached
mcrfpy.automation.screenshot("dijkstra_cycle_paths.png")

if failures:
    print(f"\nFAIL: {len(failures)} check(s) failed")
    sys.exit(1)

print("\nPASS")
sys.exit(0)
