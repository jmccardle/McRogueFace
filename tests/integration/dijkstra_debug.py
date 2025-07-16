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
entities = []
first_point = None
second_point = None

def create_simple_map():
    """Create a simple test map"""
    global grid, entities
    
    mcrfpy.createScene("dijkstra_debug")
    
    # Small grid for easy debugging
    grid = mcrfpy.Grid(grid_x=10, grid_y=10)
    grid.fill_color = mcrfpy.Color(0, 0, 0)
    
    print("Initializing 10x10 grid...")
    
    # Initialize all as floor
    for y in range(10):
        for x in range(10):
            grid.at(x, y).walkable = True
            grid.at(x, y).transparent = True
            grid.at(x, y).color = FLOOR_COLOR
    
    # Add a simple wall
    print("Adding walls at:")
    walls = [(5, 2), (5, 3), (5, 4), (5, 5), (5, 6)]
    for x, y in walls:
        print(f"  Wall at ({x}, {y})")
        grid.at(x, y).walkable = False
        grid.at(x, y).color = WALL_COLOR
    
    # Create 3 entities
    entity_positions = [(2, 5), (8, 5), (5, 8)]
    entities = []
    
    print("\nCreating entities at:")
    for i, (x, y) in enumerate(entity_positions):
        print(f"  Entity {i+1} at ({x}, {y})")
        entity = mcrfpy.Entity(x, y)
        entity.sprite_index = 49 + i  # '1', '2', '3'
        grid.entities.append(entity)
        entities.append(entity)
    
    return grid

def test_path_highlighting():
    """Test path highlighting with debug output"""
    print("\n" + "="*50)
    print("Testing path highlighting...")
    
    # Select first two entities
    e1 = entities[0]
    e2 = entities[1]
    
    print(f"\nEntity 1 position: ({e1.x}, {e1.y})")
    print(f"Entity 2 position: ({e2.x}, {e2.y})")
    
    # Use entity.path_to()
    print("\nCalling entity.path_to()...")
    path = e1.path_to(int(e2.x), int(e2.y))
    
    print(f"Path returned: {path}")
    print(f"Path length: {len(path)} steps")
    
    if path:
        print("\nHighlighting path cells:")
        for i, (x, y) in enumerate(path):
            print(f"  Step {i}: ({x}, {y})")
            # Get current color for debugging
            cell = grid.at(x, y)
            old_color = (cell.color.r, cell.color.g, cell.color.b)
            
            # Set new color
            cell.color = PATH_COLOR
            new_color = (cell.color.r, cell.color.g, cell.color.b)
            
            print(f"    Color changed from {old_color} to {new_color}")
            print(f"    Walkable: {cell.walkable}")
    
    # Also test grid's Dijkstra methods
    print("\n" + "-"*30)
    print("Testing grid Dijkstra methods...")
    
    grid.compute_dijkstra(int(e1.x), int(e1.y))
    grid_path = grid.get_dijkstra_path(int(e2.x), int(e2.y))
    distance = grid.get_dijkstra_distance(int(e2.x), int(e2.y))
    
    print(f"Grid path: {grid_path}")
    print(f"Grid distance: {distance}")
    
    # Verify colors were set
    print("\nVerifying cell colors after highlighting:")
    for x, y in path[:3]:  # Check first 3 cells
        cell = grid.at(x, y)
        color = (cell.color.r, cell.color.g, cell.color.b)
        expected = (PATH_COLOR.r, PATH_COLOR.g, PATH_COLOR.b)
        match = color == expected
        print(f"  Cell ({x}, {y}): color={color}, expected={expected}, match={match}")

def handle_keypress(scene_name, keycode):
    """Simple keypress handler"""
    if keycode == 81 or keycode == 113 or keycode == 256:  # Q/q/ESC
        print("\nExiting debug...")
        sys.exit(0)
    elif keycode == 32:  # Space
        print("\nSpace pressed - retesting path highlighting...")
        test_path_highlighting()

# Create the map
print("Dijkstra Debug Test")
print("===================")
grid = create_simple_map()

# Initial path test
test_path_highlighting()

# Set up UI
ui = mcrfpy.sceneUI("dijkstra_debug")
ui.append(grid)

# Position and scale
grid.position = (50, 50)
grid.size = (400, 400)  # 10*40

# Add title
title = mcrfpy.Caption("Dijkstra Debug - Press SPACE to retest, Q to quit", 50, 10)
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Add debug info
info = mcrfpy.Caption("Check console for debug output", 50, 470)
info.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(info)

# Set up scene
mcrfpy.keypressScene(handle_keypress)
mcrfpy.setScene("dijkstra_debug")

print("\nScene ready. The path should be highlighted in cyan.")
print("If you don't see the path, there may be a rendering issue.")
print("Press SPACE to retest, Q to quit.")