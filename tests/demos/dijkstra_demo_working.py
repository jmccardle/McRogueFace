#!/usr/bin/env python3
"""
Working Dijkstra Demo with Clear Visual Feedback
================================================

This demo shows pathfinding with high-contrast colors.
"""

import mcrfpy
import sys

# High contrast colors
WALL_COLOR = mcrfpy.Color(40, 20, 20)      # Very dark red/brown for walls
FLOOR_COLOR = mcrfpy.Color(60, 60, 80)     # Dark blue-gray for floors
PATH_COLOR = mcrfpy.Color(0, 255, 0)       # Pure green for paths
START_COLOR = mcrfpy.Color(255, 0, 0)      # Red for start
END_COLOR = mcrfpy.Color(0, 0, 255)        # Blue for end

print("Dijkstra Demo - High Contrast")
print("==============================")

# Create scene
mcrfpy.createScene("dijkstra_demo")

# Create grid with exact layout from user
grid = mcrfpy.Grid(grid_x=14, grid_y=10)
grid.fill_color = mcrfpy.Color(0, 0, 0)

# Map layout
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
            cell.walkable = False
            cell.color = WALL_COLOR
        else:
            cell.walkable = True
            cell.color = FLOOR_COLOR
            
            if char == 'E':
                entity_positions.append((x, y))

print(f"Map created: {grid.grid_x}x{grid.grid_y}")
print(f"Entity positions: {entity_positions}")

# Create entities
entities = []
for i, (x, y) in enumerate(entity_positions):
    entity = mcrfpy.Entity(x, y)
    entity.sprite_index = 49 + i  # '1', '2', '3'
    grid.entities.append(entity)
    entities.append(entity)
    print(f"Entity {i+1} at ({x}, {y})")

# Highlight a path immediately
if len(entities) >= 2:
    e1, e2 = entities[0], entities[1]
    print(f"\nCalculating path from Entity 1 ({e1.x}, {e1.y}) to Entity 2 ({e2.x}, {e2.y})...")
    
    path = e1.path_to(int(e2.x), int(e2.y))
    print(f"Path found: {path}")
    print(f"Path length: {len(path)} steps")
    
    if path:
        print("\nHighlighting path in bright green...")
        # Color start and end specially
        grid.at(int(e1.x), int(e1.y)).color = START_COLOR
        grid.at(int(e2.x), int(e2.y)).color = END_COLOR
        
        # Color the path
        for i, (x, y) in enumerate(path):
            if i > 0 and i < len(path) - 1:  # Skip start and end
                grid.at(x, y).color = PATH_COLOR
                print(f"  Colored ({x}, {y}) green")

# Keypress handler
def handle_keypress(scene_name, keycode):
    if keycode == 81 or keycode == 113 or keycode == 256:  # Q/q/ESC
        print("\nExiting...")
        sys.exit(0)
    elif keycode == 32:  # Space
        print("\nRefreshing path colors...")
        # Re-color the path to ensure it's visible
        if len(entities) >= 2 and path:
            for x, y in path[1:-1]:
                grid.at(x, y).color = PATH_COLOR

# Set up UI
ui = mcrfpy.sceneUI("dijkstra_demo")
ui.append(grid)

# Scale grid
grid.size = (560, 400)  # 14*40, 10*40
grid.position = (120, 100)

# Add title
title = mcrfpy.Caption("Dijkstra Pathfinding - High Contrast", 200, 20)
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Add legend
legend1 = mcrfpy.Caption("Red=Start, Blue=End, Green=Path", 120, 520)
legend1.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(legend1)

legend2 = mcrfpy.Caption("Press Q to quit, SPACE to refresh", 120, 540)
legend2.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(legend2)

# Entity info
info = mcrfpy.Caption(f"Path: Entity 1 to 2 = {len(path) if 'path' in locals() else 0} steps", 120, 60)
info.fill_color = mcrfpy.Color(255, 255, 100)
ui.append(info)

# Set up input
mcrfpy.keypressScene(handle_keypress)
mcrfpy.setScene("dijkstra_demo")

print("\nDemo ready! The path should be clearly visible in bright green.")
print("Red = Start, Blue = End, Green = Path")
print("Press SPACE to refresh colors if needed.")