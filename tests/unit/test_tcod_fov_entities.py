#!/usr/bin/env python3
"""
Test TCOD Field of View with Two Entities
==========================================

Demonstrates:
1. Grid with obstacles (walls)
2. Two entities at different positions
3. Entity-specific FOV calculation
4. Visual representation of visible/discovered areas
"""

import mcrfpy
from mcrfpy import libtcod
import sys

# Constants
WALL_SPRITE = 219  # Full block character
PLAYER_SPRITE = 64  # @ symbol
ENEMY_SPRITE = 69   # E character
FLOOR_SPRITE = 46   # . period

def setup_scene():
    """Create the demo scene with grid and entities"""
    mcrfpy.createScene("fov_demo")
    
    # Create grid
    grid = mcrfpy.Grid(0, 0, grid_size=(40, 25))
    grid.background_color = mcrfpy.Color(20, 20, 20)
    
    # Initialize all cells as floor
    for y in range(grid.grid_y):
        for x in range(grid.grid_x):
            cell = grid.at(x, y)
            cell.walkable = True
            cell.transparent = True
            cell.tilesprite = FLOOR_SPRITE
            cell.color = mcrfpy.Color(50, 50, 50)
    
    # Create walls (horizontal wall)
    for x in range(10, 30):
        cell = grid.at(x, 10)
        cell.walkable = False
        cell.transparent = False
        cell.tilesprite = WALL_SPRITE
        cell.color = mcrfpy.Color(100, 100, 100)
    
    # Create walls (vertical wall)
    for y in range(5, 20):
        cell = grid.at(20, y)
        cell.walkable = False
        cell.transparent = False
        cell.tilesprite = WALL_SPRITE
        cell.color = mcrfpy.Color(100, 100, 100)
    
    # Add door gaps
    grid.at(15, 10).walkable = True
    grid.at(15, 10).transparent = True
    grid.at(15, 10).tilesprite = FLOOR_SPRITE
    
    grid.at(20, 15).walkable = True
    grid.at(20, 15).transparent = True
    grid.at(20, 15).tilesprite = FLOOR_SPRITE
    
    # Create two entities
    player = mcrfpy.Entity(5, 5)
    player.sprite = PLAYER_SPRITE
    grid.entities.append(player)
    
    enemy = mcrfpy.Entity(35, 20)
    enemy.sprite = ENEMY_SPRITE
    grid.entities.append(enemy)
    
    # Add grid to scene
    ui = mcrfpy.sceneUI("fov_demo")
    ui.append(grid)
    
    # Add info text
    info = mcrfpy.Caption("TCOD FOV Demo - Blue: Player FOV, Red: Enemy FOV", 10, 430)
    info.fill_color = mcrfpy.Color(255, 255, 255)
    ui.append(info)
    
    controls = mcrfpy.Caption("Arrow keys: Move player | Q: Quit", 10, 450)
    controls.fill_color = mcrfpy.Color(200, 200, 200)
    ui.append(controls)
    
    return grid, player, enemy

def update_fov(grid, player, enemy):
    """Update field of view for both entities"""
    # Clear all overlays first
    for y in range(grid.grid_y):
        for x in range(grid.grid_x):
            cell = grid.at(x, y)
            cell.color_overlay = mcrfpy.Color(0, 0, 0, 200)  # Dark by default
    
    # Compute and display player FOV (blue tint)
    grid.compute_fov(player.x, player.y, radius=10, algorithm=libtcod.FOV_SHADOW)
    for y in range(grid.grid_y):
        for x in range(grid.grid_x):
            if grid.is_in_fov(x, y):
                cell = grid.at(x, y)
                cell.color_overlay = mcrfpy.Color(100, 100, 255, 50)  # Light blue
    
    # Compute and display enemy FOV (red tint) 
    grid.compute_fov(enemy.x, enemy.y, radius=8, algorithm=libtcod.FOV_SHADOW)
    for y in range(grid.grid_y):
        for x in range(grid.grid_x):
            if grid.is_in_fov(x, y):
                cell = grid.at(x, y)
                # Mix colors if both can see
                if cell.color_overlay.r > 0 or cell.color_overlay.g > 0 or cell.color_overlay.b > 200:
                    # Already blue, make purple
                    cell.color_overlay = mcrfpy.Color(255, 100, 255, 50)
                else:
                    # Just red
                    cell.color_overlay = mcrfpy.Color(255, 100, 100, 50)

def test_pathfinding(grid, player, enemy):
    """Test pathfinding between entities"""
    path = grid.find_path(player.x, player.y, enemy.x, enemy.y)
    
    if path:
        print(f"Path found from player to enemy: {len(path)} steps")
        # Highlight path
        for x, y in path[1:-1]:  # Skip start and end
            cell = grid.at(x, y)
            if cell.walkable:
                cell.tile_overlay = 43  # + symbol
    else:
        print("No path found between player and enemy")

def handle_keypress(scene_name, keycode):
    """Handle keyboard input"""
    if keycode == 81 or keycode == 256:  # Q or ESC
        print("\nExiting FOV demo...")
        sys.exit(0)
    
    # Get entities (assumes global access for demo)
    if keycode == 265:  # UP
        if player.y > 0 and grid.at(player.x, player.y - 1).walkable:
            player.y -= 1
    elif keycode == 264:  # DOWN
        if player.y < grid.grid_y - 1 and grid.at(player.x, player.y + 1).walkable:
            player.y += 1
    elif keycode == 263:  # LEFT
        if player.x > 0 and grid.at(player.x - 1, player.y).walkable:
            player.x -= 1
    elif keycode == 262:  # RIGHT
        if player.x < grid.grid_x - 1 and grid.at(player.x + 1, player.y).walkable:
            player.x += 1
    
    # Update FOV after movement
    update_fov(grid, player, enemy)
    test_pathfinding(grid, player, enemy)

# Main execution
print("McRogueFace TCOD FOV Demo")
print("=========================")
print("Testing mcrfpy.libtcod module...")

# Test that libtcod module exists
try:
    print(f"libtcod module: {libtcod}")
    print(f"FOV constants: FOV_BASIC={libtcod.FOV_BASIC}, FOV_SHADOW={libtcod.FOV_SHADOW}")
except Exception as e:
    print(f"ERROR: Could not access libtcod module: {e}")
    sys.exit(1)

# Create scene
grid, player, enemy = setup_scene()

# Make these global for keypress handler (demo only)
globals()['grid'] = grid
globals()['player'] = player
globals()['enemy'] = enemy

# Initial FOV calculation
update_fov(grid, player, enemy)

# Test pathfinding
test_pathfinding(grid, player, enemy)

# Test line drawing
line = libtcod.line(player.x, player.y, enemy.x, enemy.y)
print(f"Line from player to enemy: {len(line)} cells")

# Set up input handling
mcrfpy.keypressScene(handle_keypress)

# Show the scene
mcrfpy.setScene("fov_demo")

print("\nFOV demo running. Use arrow keys to move player (@)")
print("Blue areas are visible to player, red to enemy, purple to both")
print("Press Q to quit")