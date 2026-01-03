#!/usr/bin/env python3
"""
Dijkstra Demo - Cycles Through Different Path Combinations
==========================================================

Shows paths between different entity pairs, skipping impossible paths.
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
color_layer = None
entities = []
current_path_index = 0
path_combinations = []
current_path = []

def create_map():
    """Create the map with entities"""
    global grid, color_layer, entities

    dijkstra_cycle = mcrfpy.Scene("dijkstra_cycle")

    # Create grid
    grid = mcrfpy.Grid(grid_x=14, grid_y=10)
    grid.fill_color = mcrfpy.Color(0, 0, 0)

    # Add color layer for cell coloring
    color_layer = grid.add_layer("color", z_index=-1)

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
            cell = grid.at(x, y)

            if char == 'W':
                cell.walkable = False
                color_layer.set(x, y, WALL_COLOR)
            else:
                cell.walkable = True
                color_layer.set(x, y, FLOOR_COLOR)

                if char == 'E':
                    entity_positions.append((x, y))

    # Create entities
    entities = []
    for i, (x, y) in enumerate(entity_positions):
        entity = mcrfpy.Entity((x, y), grid=grid)
        entity.sprite_index = 49 + i  # '1', '2', '3'
        entities.append(entity)
    
    print("Entities created:")
    for i, (x, y) in enumerate(entity_positions):
        print(f"  Entity {i+1} at ({x}, {y})")
    
    # Check which entity is trapped
    print("\nChecking accessibility:")
    for i, e in enumerate(entities):
        # Try to path to each other entity
        can_reach = []
        for j, other in enumerate(entities):
            if i != j:
                path = e.path_to(int(other.x), int(other.y))
                if path:
                    can_reach.append(j+1)
        
        if not can_reach:
            print(f"  Entity {i+1} at ({int(e.x)}, {int(e.y)}) is TRAPPED!")
        else:
            print(f"  Entity {i+1} can reach entities: {can_reach}")
    
    # Generate valid path combinations (excluding trapped entity)
    global path_combinations
    path_combinations = []
    
    # Only paths between entities 2 and 3 (indices 1 and 2) will work
    # since entity 1 (index 0) is trapped
    if len(entities) >= 3:
        # Entity 2 to Entity 3
        path = entities[1].path_to(int(entities[2].x), int(entities[2].y))
        if path:
            path_combinations.append((1, 2, path))
        
        # Entity 3 to Entity 2
        path = entities[2].path_to(int(entities[1].x), int(entities[1].y))
        if path:
            path_combinations.append((2, 1, path))
    
    print(f"\nFound {len(path_combinations)} valid paths")

def clear_path_colors():
    """Reset all floor tiles to original color"""
    global current_path

    for y in range(grid.grid_y):
        for x in range(grid.grid_x):
            cell = grid.at(x, y)
            if cell.walkable:
                color_layer.set(x, y, FLOOR_COLOR)

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
        color_layer.set(int(e_from.x), int(e_from.y), START_COLOR)
        color_layer.set(int(e_to.x), int(e_to.y), END_COLOR)

        # Color intermediate steps
        for i, (x, y) in enumerate(path):
            if i > 0 and i < len(path) - 1:
                color_layer.set(x, y, PATH_COLOR)

    # Update status
    status_text.text = f"Path {current_path_index + 1}/{len(path_combinations)}: Entity {from_idx+1} → Entity {to_idx+1} ({len(path)} steps)"

    # Update path display
    path_display = []
    for i, (x, y) in enumerate(path[:5]):  # Show first 5 steps
        path_display.append(f"({x},{y})")
    if len(path) > 5:
        path_display.append("...")
    path_text.text = "Path: " + " → ".join(path_display) if path_display else "Path: None"

def handle_keypress(key_str, state):
    """Handle keyboard input"""
    global current_path_index
    if state == "end": return
    if key_str == "Esc":
        print("\nExiting...")
        sys.exit(0)
    elif key_str == "N" or key_str == "Space":
        show_path(current_path_index + 1)
    elif key_str == "P":
        show_path(current_path_index - 1)
    elif key_str == "R":
        show_path(current_path_index)

# Create the demo
print("Dijkstra Path Cycling Demo")
print("==========================")
print("Note: Entity 1 is trapped by walls!")
print()

create_map()

# Set up UI
ui = dijkstra_cycle.children
ui.append(grid)

# Scale and position
grid.size = (560, 400)
grid.position = (120, 100)

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

print("\nDemo ready!")
print("Controls:")
print("  SPACE or N - Next path")
print("  P - Previous path")
print("  R - Refresh current path")
print("  Q - Quit")
