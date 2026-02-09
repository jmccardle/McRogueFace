#!/usr/bin/env python3
"""
Dijkstra Pathfinding Interactive Demo
=====================================

Interactive visualization showing Dijkstra pathfinding between entities.

Controls:
- Press 1/2/3 to select the first entity
- Press A/B/C to select the second entity  
- Space to clear selection
- Q or ESC to quit

The path between selected entities is automatically highlighted.
"""

import mcrfpy
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
color_layer = None
entities = []
first_point = None
second_point = None

def create_map():
    """Create the interactive map with the layout specified by the user"""
    global grid, color_layer, entities

    dijkstra_interactive = mcrfpy.Scene("dijkstra_interactive")

    # Create grid - 14x10 as specified
    grid = mcrfpy.Grid(grid_w=14, grid_h=10)
    grid.fill_color = mcrfpy.Color(0, 0, 0)

    # Add color layer for cell coloring
    color_layer = grid.add_layer("color", z_index=-1)

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

    # Create the map
    entity_positions = []
    for y, row in enumerate(map_layout):
        for x, char in enumerate(row):
            cell = grid.at(x, y)

            if char == 'W':
                # Wall
                cell.walkable = False
                cell.transparent = False
                color_layer.set(x, y, WALL_COLOR)
            else:
                # Floor
                cell.walkable = True
                cell.transparent = True
                color_layer.set(x, y, FLOOR_COLOR)

                if char == 'E':
                    # Entity position
                    entity_positions.append((x, y))

    # Create entities at marked positions
    entities = []
    for i, (x, y) in enumerate(entity_positions):
        entity = mcrfpy.Entity((x, y), grid=grid)
        entity.sprite_index = 49 + i  # '1', '2', '3'
        entities.append(entity)

    return grid

def clear_path_highlight():
    """Clear any existing path highlighting"""
    # Reset all floor tiles to original color
    for y in range(grid.grid_h):
        for x in range(grid.grid_w):
            cell = grid.at(x, y)
            if cell.walkable:
                color_layer.set(x, y, FLOOR_COLOR)

def highlight_path():
    """Highlight the path between selected entities"""
    if first_point is None or second_point is None:
        return

    # Clear previous highlighting
    clear_path_highlight()

    # Get entities
    entity1 = entities[first_point]
    entity2 = entities[second_point]

    # Compute Dijkstra from first entity
    grid.compute_dijkstra(int(entity1.x), int(entity1.y))

    # Get path to second entity
    path = grid.get_dijkstra_path(int(entity2.x), int(entity2.y))

    if path:
        # Highlight the path
        for x, y in path:
            cell = grid.at(x, y)
            if cell.walkable:
                color_layer.set(x, y, PATH_COLOR)

        # Also highlight start and end with entity colors
        color_layer.set(int(entity1.x), int(entity1.y), ENTITY_COLORS[first_point])
        color_layer.set(int(entity2.x), int(entity2.y), ENTITY_COLORS[second_point])

        # Update info
        distance = grid.get_dijkstra_distance(int(entity2.x), int(entity2.y))
        info_text.text = f"Path: Entity {first_point+1} to Entity {second_point+1} - {len(path)} steps, {distance:.1f} units"
    else:
        info_text.text = f"No path between Entity {first_point+1} and Entity {second_point+1}"

def handle_keypress(scene_name, keycode):
    """Handle keyboard input"""
    global first_point, second_point
    
    # Number keys for first entity
    if keycode == 49:  # '1'
        first_point = 0
        status_text.text = f"First: Entity 1 | Second: {f'Entity {second_point+1}' if second_point is not None else '?'}"
        highlight_path()
    elif keycode == 50:  # '2'
        first_point = 1
        status_text.text = f"First: Entity 2 | Second: {f'Entity {second_point+1}' if second_point is not None else '?'}"
        highlight_path()
    elif keycode == 51:  # '3'
        first_point = 2
        status_text.text = f"First: Entity 3 | Second: {f'Entity {second_point+1}' if second_point is not None else '?'}"
        highlight_path()
    
    # Letter keys for second entity
    elif keycode == 65 or keycode == 97:  # 'A' or 'a'
        second_point = 0
        status_text.text = f"First: {f'Entity {first_point+1}' if first_point is not None else '?'} | Second: Entity 1"
        highlight_path()
    elif keycode == 66 or keycode == 98:  # 'B' or 'b'
        second_point = 1
        status_text.text = f"First: {f'Entity {first_point+1}' if first_point is not None else '?'} | Second: Entity 2"
        highlight_path()
    elif keycode == 67 or keycode == 99:  # 'C' or 'c'
        second_point = 2
        status_text.text = f"First: {f'Entity {first_point+1}' if first_point is not None else '?'} | Second: Entity 3"
        highlight_path()
    
    # Clear selection
    elif keycode == 32:  # Space
        first_point = None
        second_point = None
        clear_path_highlight()
        status_text.text = "Press 1/2/3 for first entity, A/B/C for second"
        info_text.text = "Space to clear, Q to quit"
    
    # Quit
    elif keycode == 81 or keycode == 113 or keycode == 256:  # Q/q/ESC
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

# Create map
grid = create_map()

# Set up UI
ui = dijkstra_interactive.children
ui.append(grid)

# Scale and position grid for better visibility
grid.size = (560, 400)  # 14*40, 10*40
grid.position = (120, 60)

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

legend2 = mcrfpy.Caption(pos=(120, 560), text="Colors: Dark=Wall Light=Floor Cyan=Path")
legend2.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(legend2)

# Mark entity positions with colored indicators
for i, entity in enumerate(entities):
    marker = mcrfpy.Caption(pos=(120 + int(entity.x) * 40 + 15, 60 + int(entity.y) * 40 + 10),
                            text=str(i+1))
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
    print(f"  Entity {i+1}: ({int(entity.x)}, {int(entity.y)})")