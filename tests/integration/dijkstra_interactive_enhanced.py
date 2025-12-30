#!/usr/bin/env python3
"""
Enhanced Dijkstra Pathfinding Interactive Demo
==============================================

Interactive visualization with entity pathfinding animations.

Controls:
- Press 1/2/3 to select the first entity
- Press A/B/C to select the second entity  
- Space to clear selection
- M to make selected entity move along path
- P to pause/resume animation
- R to reset entity positions
- Q or ESC to quit
"""

import mcrfpy
import sys
import math

# Colors
WALL_COLOR = mcrfpy.Color(60, 30, 30)
FLOOR_COLOR = mcrfpy.Color(200, 200, 220)
PATH_COLOR = mcrfpy.Color(200, 250, 220)
VISITED_COLOR = mcrfpy.Color(180, 230, 200)
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
current_path = []
animating = False
animation_progress = 0.0
animation_speed = 2.0  # cells per second
original_positions = []  # Store original entity positions

def create_map():
    """Create the interactive map with the layout specified by the user"""
    global grid, color_layer, entities, original_positions

    mcrfpy.createScene("dijkstra_enhanced")

    # Create grid - 14x10 as specified
    grid = mcrfpy.Grid(grid_x=14, grid_y=10)
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
    original_positions = []
    for i, (x, y) in enumerate(entity_positions):
        entity = mcrfpy.Entity((x, y), grid=grid)
        entity.sprite_index = 49 + i  # '1', '2', '3'
        entities.append(entity)
        original_positions.append((x, y))

    return grid

def clear_path_highlight():
    """Clear any existing path highlighting"""
    global current_path

    # Reset all floor tiles to original color
    for y in range(grid.grid_y):
        for x in range(grid.grid_x):
            cell = grid.at(x, y)
            if cell.walkable:
                color_layer.set(x, y, FLOOR_COLOR)

    current_path = []

def highlight_path():
    """Highlight the path between selected entities using entity.path_to()"""
    global current_path

    if first_point is None or second_point is None:
        return

    # Clear previous highlighting
    clear_path_highlight()

    # Get entities
    entity1 = entities[first_point]
    entity2 = entities[second_point]

    # Use the new path_to method!
    path = entity1.path_to(int(entity2.x), int(entity2.y))

    if path:
        current_path = path

        # Highlight the path
        for i, (x, y) in enumerate(path):
            cell = grid.at(x, y)
            if cell.walkable:
                # Use gradient for path visualization
                if i < len(path) - 1:
                    color_layer.set(x, y, PATH_COLOR)
                else:
                    color_layer.set(x, y, VISITED_COLOR)

        # Highlight start and end with entity colors
        color_layer.set(int(entity1.x), int(entity1.y), ENTITY_COLORS[first_point])
        color_layer.set(int(entity2.x), int(entity2.y), ENTITY_COLORS[second_point])

        # Update info
        info_text.text = f"Path: Entity {first_point+1} to Entity {second_point+1} - {len(path)} steps"
    else:
        info_text.text = f"No path between Entity {first_point+1} and Entity {second_point+1}"
        current_path = []

def animate_movement(dt):
    """Animate entity movement along path"""
    global animation_progress, animating, current_path
    
    if not animating or not current_path or first_point is None:
        return
    
    entity = entities[first_point]
    
    # Update animation progress
    animation_progress += animation_speed * dt
    
    # Calculate current position along path
    path_index = int(animation_progress)
    
    if path_index >= len(current_path):
        # Animation complete
        animating = False
        animation_progress = 0.0
        # Snap to final position
        if current_path:
            final_x, final_y = current_path[-1]
            entity.x = float(final_x)
            entity.y = float(final_y)
        return
    
    # Interpolate between path points
    if path_index < len(current_path) - 1:
        curr_x, curr_y = current_path[path_index]
        next_x, next_y = current_path[path_index + 1]
        
        # Calculate interpolation factor
        t = animation_progress - path_index
        
        # Smooth interpolation
        entity.x = curr_x + (next_x - curr_x) * t
        entity.y = curr_y + (next_y - curr_y) * t
    else:
        # At last point
        entity.x, entity.y = current_path[path_index]

def handle_keypress(scene_name, keycode):
    """Handle keyboard input"""
    global first_point, second_point, animating, animation_progress
    
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
    
    # Movement control
    elif keycode == 77 or keycode == 109:  # 'M' or 'm'
        if current_path and first_point is not None:
            animating = True
            animation_progress = 0.0
            control_text.text = "Animation: MOVING (press P to pause)"
    
    # Pause/Resume
    elif keycode == 80 or keycode == 112:  # 'P' or 'p'
        animating = not animating
        control_text.text = f"Animation: {'MOVING' if animating else 'PAUSED'} (press P to {'pause' if animating else 'resume'})"
    
    # Reset positions
    elif keycode == 82 or keycode == 114:  # 'R' or 'r'
        animating = False
        animation_progress = 0.0
        for i, entity in enumerate(entities):
            entity.x, entity.y = original_positions[i]
        control_text.text = "Entities reset to original positions"
        highlight_path()  # Re-highlight path after reset
    
    # Clear selection
    elif keycode == 32:  # Space
        first_point = None
        second_point = None
        animating = False
        animation_progress = 0.0
        clear_path_highlight()
        status_text.text = "Press 1/2/3 for first entity, A/B/C for second"
        info_text.text = "Space to clear, Q to quit"
        control_text.text = "Press M to move, P to pause, R to reset"
    
    # Quit
    elif keycode == 81 or keycode == 113 or keycode == 256:  # Q/q/ESC
        print("\nExiting enhanced Dijkstra demo...")
        sys.exit(0)

# Timer callback for animation
def update_animation(dt):
    """Update animation state"""
    animate_movement(dt / 1000.0)  # Convert ms to seconds

# Create the visualization
print("Enhanced Dijkstra Pathfinding Demo")
print("==================================")
print("Controls:")
print("  1/2/3 - Select first entity")
print("  A/B/C - Select second entity")
print("  M     - Move first entity along path")
print("  P     - Pause/Resume animation")
print("  R     - Reset entity positions")
print("  Space - Clear selection")
print("  Q/ESC - Quit")

# Create map
grid = create_map()

# Set up UI
ui = mcrfpy.sceneUI("dijkstra_enhanced")
ui.append(grid)

# Scale and position grid for better visibility
grid.size = (560, 400)  # 14*40, 10*40
grid.position = (120, 60)

# Add title
title = mcrfpy.Caption(pos=(250, 10), text="Enhanced Dijkstra Pathfinding")
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

# Add control text
control_text = mcrfpy.Caption(pos=(120, 520), text="Press M to move, P to pause, R to reset")
control_text.fill_color = mcrfpy.Color(150, 200, 150)
ui.append(control_text)

# Add legend
legend1 = mcrfpy.Caption(pos=(120, 560), text="Entities: 1=Red 2=Green 3=Blue")
legend1.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(legend1)

legend2 = mcrfpy.Caption(pos=(120, 580), text="Colors: Dark=Wall Light=Floor Cyan=Path")
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
mcrfpy.keypressScene(handle_keypress)

# Set up animation timer (60 FPS)
mcrfpy.setTimer("animation", update_animation, 16)

# Show the scene
mcrfpy.setScene("dijkstra_enhanced")

print("\nVisualization ready!")
print("Entities are at:")
for i, entity in enumerate(entities):
    print(f"  Entity {i+1}: ({int(entity.x)}, {int(entity.y)})")