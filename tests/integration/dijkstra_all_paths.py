#!/usr/bin/env python3
"""
Dijkstra Demo - Shows ALL Path Combinations (Including Invalid)
===============================================================

Cycles through every possible entity pair to demonstrate both
valid paths and properly handled invalid paths (empty lists).
"""

import mcrfpy
import sys

# High contrast colors
WALL_COLOR = mcrfpy.Color(40, 20, 20)      # Very dark red/brown
FLOOR_COLOR = mcrfpy.Color(60, 60, 80)     # Dark blue-gray
PATH_COLOR = mcrfpy.Color(0, 255, 0)       # Bright green
START_COLOR = mcrfpy.Color(255, 100, 100)  # Light red
END_COLOR = mcrfpy.Color(100, 100, 255)    # Light blue
NO_PATH_COLOR = mcrfpy.Color(255, 0, 0)    # Pure red for unreachable

# Global state
grid = None
entities = []
current_combo_index = 0
all_combinations = []  # All possible pairs
current_path = []

def create_map():
    """Create the map with entities"""
    global grid, entities, all_combinations
    
    mcrfpy.createScene("dijkstra_all")
    
    # Create grid
    grid = mcrfpy.Grid(grid_x=14, grid_y=10)
    grid.fill_color = mcrfpy.Color(0, 0, 0)
    
    # Map layout - Entity 1 is intentionally trapped!
    map_layout = [
        "..............",  # Row 0
        "..W.....WWWW..",  # Row 1
        "..W.W...W.EW..",  # Row 2 - Entity 1 TRAPPED at (10,2)
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
                cell.color = WALL_COLOR
            else:
                cell.walkable = True
                cell.color = FLOOR_COLOR
                
                if char == 'E':
                    entity_positions.append((x, y))
    
    # Create entities
    entities = []
    for i, (x, y) in enumerate(entity_positions):
        entity = mcrfpy.Entity(x, y)
        entity.sprite_index = 49 + i  # '1', '2', '3'
        grid.entities.append(entity)
        entities.append(entity)
    
    print("Map Analysis:")
    print("=============")
    for i, (x, y) in enumerate(entity_positions):
        print(f"Entity {i+1} at ({x}, {y})")
    
    # Generate ALL combinations (including invalid ones)
    all_combinations = []
    for i in range(len(entities)):
        for j in range(len(entities)):
            if i != j:  # Skip self-paths
                all_combinations.append((i, j))
    
    print(f"\nTotal path combinations to test: {len(all_combinations)}")

def clear_path_colors():
    """Reset all floor tiles to original color"""
    global current_path
    
    for y in range(grid.grid_y):
        for x in range(grid.grid_x):
            cell = grid.at(x, y)
            if cell.walkable:
                cell.color = FLOOR_COLOR
    
    current_path = []

def show_combination(index):
    """Show a specific path combination (valid or invalid)"""
    global current_combo_index, current_path
    
    current_combo_index = index % len(all_combinations)
    from_idx, to_idx = all_combinations[current_combo_index]
    
    # Clear previous path
    clear_path_colors()
    
    # Get entities
    e_from = entities[from_idx]
    e_to = entities[to_idx]
    
    # Calculate path
    path = e_from.path_to(int(e_to.x), int(e_to.y))
    current_path = path if path else []
    
    # Always color start and end positions
    grid.at(int(e_from.x), int(e_from.y)).color = START_COLOR
    grid.at(int(e_to.x), int(e_to.y)).color = NO_PATH_COLOR if not path else END_COLOR
    
    # Color the path if it exists
    if path:
        # Color intermediate steps
        for i, (x, y) in enumerate(path):
            if i > 0 and i < len(path) - 1:
                grid.at(x, y).color = PATH_COLOR
        
        status_text.text = f"Path {current_combo_index + 1}/{len(all_combinations)}: Entity {from_idx+1} → Entity {to_idx+1} = {len(path)} steps"
        status_text.fill_color = mcrfpy.Color(100, 255, 100)  # Green for valid
        
        # Show path steps
        path_display = []
        for i, (x, y) in enumerate(path[:5]):
            path_display.append(f"({x},{y})")
        if len(path) > 5:
            path_display.append("...")
        path_text.text = "Path: " + " → ".join(path_display)
    else:
        status_text.text = f"Path {current_combo_index + 1}/{len(all_combinations)}: Entity {from_idx+1} → Entity {to_idx+1} = NO PATH!"
        status_text.fill_color = mcrfpy.Color(255, 100, 100)  # Red for invalid
        path_text.text = "Path: [] (No valid path exists)"
    
    # Update info
    info_text.text = f"From: Entity {from_idx+1} at ({int(e_from.x)}, {int(e_from.y)}) | To: Entity {to_idx+1} at ({int(e_to.x)}, {int(e_to.y)})"

def handle_keypress(key_str, state):
    """Handle keyboard input"""
    global current_combo_index
    if state == "end": return
    
    if key_str == "Esc" or key_str == "Q":
        print("\nExiting...")
        sys.exit(0)
    elif key_str == "Space" or key_str == "N":
        show_combination(current_combo_index + 1)
    elif key_str == "P":
        show_combination(current_combo_index - 1)
    elif key_str == "R":
        show_combination(current_combo_index)
    elif key_str in "123456":
        combo_num = int(key_str) - 1  # 0-based index
        if combo_num < len(all_combinations):
            show_combination(combo_num)

# Create the demo
print("Dijkstra All Paths Demo")
print("=======================")
print("Shows ALL path combinations including invalid ones")
print("Entity 1 is trapped - paths to/from it will be empty!")
print()

create_map()

# Set up UI
ui = mcrfpy.sceneUI("dijkstra_all")
ui.append(grid)

# Scale and position
grid.size = (560, 400)
grid.position = (120, 100)

# Add title
title = mcrfpy.Caption("Dijkstra - All Paths (Valid & Invalid)", 200, 20)
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Add status (will change color based on validity)
status_text = mcrfpy.Caption("Ready", 120, 60)
status_text.fill_color = mcrfpy.Color(255, 255, 100)
ui.append(status_text)

# Add info
info_text = mcrfpy.Caption("", 120, 80)
info_text.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(info_text)

# Add path display
path_text = mcrfpy.Caption("Path: None", 120, 520)
path_text.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(path_text)

# Add controls
controls = mcrfpy.Caption("SPACE/N=Next, P=Previous, 1-6=Jump to path, Q=Quit", 120, 540)
controls.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(controls)

# Add legend
legend = mcrfpy.Caption("Red Start→Blue End (valid) | Red Start→Red End (invalid)", 120, 560)
legend.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(legend)

# Expected results info
expected = mcrfpy.Caption("Entity 1 is trapped: paths 1→2, 1→3, 2→1, 3→1 will fail", 120, 580)
expected.fill_color = mcrfpy.Color(255, 150, 150)
ui.append(expected)

# Set scene first, then set up input handler
mcrfpy.setScene("dijkstra_all")
mcrfpy.keypressScene(handle_keypress)

# Show first combination
show_combination(0)

print("\nDemo ready!")
print("Expected results:")
print("  Path 1: Entity 1→2 = NO PATH (Entity 1 is trapped)")
print("  Path 2: Entity 1→3 = NO PATH (Entity 1 is trapped)")
print("  Path 3: Entity 2→1 = NO PATH (Entity 1 is trapped)")
print("  Path 4: Entity 2→3 = Valid path")
print("  Path 5: Entity 3→1 = NO PATH (Entity 1 is trapped)")
print("  Path 6: Entity 3→2 = Valid path")