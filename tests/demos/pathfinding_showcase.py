#!/usr/bin/env python3
"""
Pathfinding Showcase Demo
=========================

Demonstrates various pathfinding scenarios with multiple entities.

Features:
- Multiple entities pathfinding simultaneously
- Chase mode: entities pursue targets
- Flee mode: entities avoid threats
- Patrol mode: entities follow waypoints
- Visual debugging: show Dijkstra distance field
"""

import mcrfpy
import sys
import random

# Colors
WALL_COLOR = mcrfpy.Color(40, 40, 40)
FLOOR_COLOR = mcrfpy.Color(220, 220, 240)
PATH_COLOR = mcrfpy.Color(180, 250, 180)
THREAT_COLOR = mcrfpy.Color(255, 100, 100)
GOAL_COLOR = mcrfpy.Color(100, 255, 100)
DIJKSTRA_COLORS = [
    mcrfpy.Color(50, 50, 100),    # Far
    mcrfpy.Color(70, 70, 150),
    mcrfpy.Color(90, 90, 200),
    mcrfpy.Color(110, 110, 250),
    mcrfpy.Color(150, 150, 255),
    mcrfpy.Color(200, 200, 255),  # Near
]

# Entity types
PLAYER = 64      # @
ENEMY = 69       # E
TREASURE = 36    # $
PATROL = 80      # P

# Global state
grid = None
player = None
enemies = []
treasures = []
patrol_entities = []
mode = "CHASE"
show_dijkstra = False
animation_speed = 3.0

# Track waypoints separately since Entity doesn't have custom attributes
entity_waypoints = {}  # entity -> [(x, y), ...]
entity_waypoint_indices = {}  # entity -> current index

def create_dungeon():
    """Create a dungeon-like map"""
    global grid
    
    mcrfpy.createScene("pathfinding_showcase")
    
    # Create larger grid for showcase
    grid = mcrfpy.Grid(grid_x=30, grid_y=20)
    grid.fill_color = mcrfpy.Color(0, 0, 0)
    
    # Initialize all as floor
    for y in range(20):
        for x in range(30):
            grid.at(x, y).walkable = True
            grid.at(x, y).transparent = True
            grid.at(x, y).color = FLOOR_COLOR
    
    # Create rooms and corridors
    rooms = [
        (2, 2, 8, 6),    # Top-left room
        (20, 2, 8, 6),   # Top-right room
        (11, 8, 8, 6),   # Center room
        (2, 14, 8, 5),   # Bottom-left room
        (20, 14, 8, 5),  # Bottom-right room
    ]
    
    # Create room walls
    for rx, ry, rw, rh in rooms:
        # Top and bottom walls
        for x in range(rx, rx + rw):
            if 0 <= x < 30:
                grid.at(x, ry).walkable = False
                grid.at(x, ry).color = WALL_COLOR
                grid.at(x, ry + rh - 1).walkable = False
                grid.at(x, ry + rh - 1).color = WALL_COLOR
        
        # Left and right walls
        for y in range(ry, ry + rh):
            if 0 <= y < 20:
                grid.at(rx, y).walkable = False
                grid.at(rx, y).color = WALL_COLOR
                grid.at(rx + rw - 1, y).walkable = False
                grid.at(rx + rw - 1, y).color = WALL_COLOR
    
    # Create doorways
    doorways = [
        (6, 2), (24, 2),      # Top room doors
        (6, 7), (24, 7),      # Top room doors bottom
        (15, 8), (15, 13),    # Center room doors
        (6, 14), (24, 14),    # Bottom room doors
        (11, 11), (18, 11),   # Center room side doors
    ]
    
    for x, y in doorways:
        if 0 <= x < 30 and 0 <= y < 20:
            grid.at(x, y).walkable = True
            grid.at(x, y).color = FLOOR_COLOR
    
    # Add some corridors
    # Horizontal corridors
    for x in range(10, 20):
        grid.at(x, 5).walkable = True
        grid.at(x, 5).color = FLOOR_COLOR
        grid.at(x, 16).walkable = True
        grid.at(x, 16).color = FLOOR_COLOR
    
    # Vertical corridors
    for y in range(5, 17):
        grid.at(10, y).walkable = True
        grid.at(10, y).color = FLOOR_COLOR
        grid.at(19, y).walkable = True
        grid.at(19, y).color = FLOOR_COLOR

def spawn_entities():
    """Spawn various entity types"""
    global player, enemies, treasures, patrol_entities
    
    # Clear existing entities
    #grid.entities.clear()
    enemies = []
    treasures = []
    patrol_entities = []
    
    # Spawn player in center room
    player = mcrfpy.Entity((15, 11), mcrfpy.default_texture, PLAYER)
    grid.entities.append(player)
    
    # Spawn enemies in corners
    enemy_positions = [(4, 4), (24, 4), (4, 16), (24, 16)]
    for x, y in enemy_positions:
        enemy = mcrfpy.Entity((x, y), mcrfpy.default_texture, ENEMY)
        grid.entities.append(enemy)
        enemies.append(enemy)
    
    # Spawn treasures
    treasure_positions = [(6, 5), (24, 5), (15, 10)]
    for x, y in treasure_positions:
        treasure = mcrfpy.Entity((x, y), mcrfpy.default_texture, TREASURE)
        grid.entities.append(treasure)
        treasures.append(treasure)
    
    # Spawn patrol entities
    patrol = mcrfpy.Entity((10, 10), mcrfpy.default_texture, PATROL)
    # Store waypoints separately since Entity doesn't support custom attributes
    entity_waypoints[patrol] = [(10, 10), (19, 10), (19, 16), (10, 16)]  # Square patrol
    entity_waypoint_indices[patrol] = 0
    grid.entities.append(patrol)
    patrol_entities.append(patrol)

def visualize_dijkstra(target_x, target_y):
    """Visualize Dijkstra distance field"""
    if not show_dijkstra:
        return
    
    # Compute Dijkstra from target
    grid.compute_dijkstra(target_x, target_y)
    
    # Color tiles based on distance
    max_dist = 30.0
    for y in range(20):
        for x in range(30):
            if grid.at(x, y).walkable:
                dist = grid.get_dijkstra_distance(x, y)
                if dist is not None and dist < max_dist:
                    # Map distance to color index
                    color_idx = int((dist / max_dist) * len(DIJKSTRA_COLORS))
                    color_idx = min(color_idx, len(DIJKSTRA_COLORS) - 1)
                    grid.at(x, y).color = DIJKSTRA_COLORS[color_idx]

def move_enemies(dt):
    """Move enemies based on current mode"""
    if mode == "CHASE":
        # Enemies chase player
        for enemy in enemies:
            path = enemy.path_to(int(player.x), int(player.y))
            if path and len(path) > 1:  # Don't move onto player
                # Move towards player
                next_x, next_y = path[1]
                # Smooth movement
                dx = next_x - enemy.x
                dy = next_y - enemy.y
                enemy.x += dx * dt * animation_speed
                enemy.y += dy * dt * animation_speed
                
    elif mode == "FLEE":
        # Enemies flee from player
        for enemy in enemies:
            # Compute opposite direction
            dx = enemy.x - player.x
            dy = enemy.y - player.y
            
            # Find safe spot in that direction
            target_x = int(enemy.x + dx * 2)
            target_y = int(enemy.y + dy * 2)
            
            # Clamp to grid
            target_x = max(0, min(29, target_x))
            target_y = max(0, min(19, target_y))
            
            path = enemy.path_to(target_x, target_y)
            if path and len(path) > 0:
                next_x, next_y = path[0]
                # Move away from player
                dx = next_x - enemy.x
                dy = next_y - enemy.y
                enemy.x += dx * dt * animation_speed
                enemy.y += dy * dt * animation_speed

def move_patrols(dt):
    """Move patrol entities along waypoints"""
    for patrol in patrol_entities:
        if patrol not in entity_waypoints:
            continue
            
        # Get current waypoint
        waypoints = entity_waypoints[patrol]
        waypoint_index = entity_waypoint_indices[patrol]
        target_x, target_y = waypoints[waypoint_index]
        
        # Check if reached waypoint
        dist = abs(patrol.x - target_x) + abs(patrol.y - target_y)
        if dist < 0.5:
            # Move to next waypoint
            entity_waypoint_indices[patrol] = (waypoint_index + 1) % len(waypoints)
            waypoint_index = entity_waypoint_indices[patrol]
            target_x, target_y = waypoints[waypoint_index]
        
        # Path to waypoint
        path = patrol.path_to(target_x, target_y)
        if path and len(path) > 0:
            next_x, next_y = path[0]
            dx = next_x - patrol.x
            dy = next_y - patrol.y
            patrol.x += dx * dt * animation_speed * 0.5  # Slower patrol speed
            patrol.y += dy * dt * animation_speed * 0.5

def update_entities(dt):
    """Update all entity movements"""
    move_enemies(dt / 1000.0)  # Convert to seconds
    move_patrols(dt / 1000.0)
    
    # Update Dijkstra visualization
    if show_dijkstra and player:
        visualize_dijkstra(int(player.x), int(player.y))

def handle_keypress(scene_name, keycode):
    """Handle keyboard input"""
    global mode, show_dijkstra, player
    
    # Mode switching
    if keycode == 49:  # '1'
        mode = "CHASE"
        mode_text.text = "Mode: CHASE - Enemies pursue player"
        clear_colors()
    elif keycode == 50:  # '2'
        mode = "FLEE"
        mode_text.text = "Mode: FLEE - Enemies avoid player"
        clear_colors()
    elif keycode == 51:  # '3'
        mode = "PATROL"
        mode_text.text = "Mode: PATROL - Entities follow waypoints"
        clear_colors()
    
    # Toggle Dijkstra visualization
    elif keycode == 68 or keycode == 100:  # 'D' or 'd'
        show_dijkstra = not show_dijkstra
        debug_text.text = f"Dijkstra Debug: {'ON' if show_dijkstra else 'OFF'}"
        if not show_dijkstra:
            clear_colors()
    
    # Move player with arrow keys or WASD
    elif keycode in [87, 119]:  # W/w - Up
        if player.y > 0:
            path = player.path_to(int(player.x), int(player.y) - 1)
            if path:
                player.y -= 1
    elif keycode in [83, 115]:  # S/s - Down
        if player.y < 19:
            path = player.path_to(int(player.x), int(player.y) + 1)
            if path:
                player.y += 1
    elif keycode in [65, 97]:  # A/a - Left
        if player.x > 0:
            path = player.path_to(int(player.x) - 1, int(player.y))
            if path:
                player.x -= 1
    elif keycode in [68, 100]:  # D/d - Right
        if player.x < 29:
            path = player.path_to(int(player.x) + 1, int(player.y))
            if path:
                player.x += 1
    
    # Reset
    elif keycode == 82 or keycode == 114:  # 'R' or 'r'
        spawn_entities()
        clear_colors()
    
    # Quit
    elif keycode == 81 or keycode == 113 or keycode == 256:  # Q/q/ESC
        print("\nExiting pathfinding showcase...")
        sys.exit(0)

def clear_colors():
    """Reset floor colors"""
    for y in range(20):
        for x in range(30):
            if grid.at(x, y).walkable:
                grid.at(x, y).color = FLOOR_COLOR

# Create the showcase
print("Pathfinding Showcase Demo")
print("=========================")
print("Controls:")
print("  WASD    - Move player")
print("  1       - Chase mode (enemies pursue)")
print("  2       - Flee mode (enemies avoid)")
print("  3       - Patrol mode")
print("  D       - Toggle Dijkstra visualization")
print("  R       - Reset entities")
print("  Q/ESC   - Quit")

# Create dungeon
create_dungeon()
spawn_entities()

# Set up UI
ui = mcrfpy.sceneUI("pathfinding_showcase")
ui.append(grid)

# Scale and position
grid.size = (750, 500)  # 30*25, 20*25
grid.position = (25, 60)

# Add title
title = mcrfpy.Caption("Pathfinding Showcase", 300, 10)
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Add mode text
mode_text = mcrfpy.Caption("Mode: CHASE - Enemies pursue player", 25, 580)
mode_text.fill_color = mcrfpy.Color(255, 255, 200)
ui.append(mode_text)

# Add debug text
debug_text = mcrfpy.Caption("Dijkstra Debug: OFF", 25, 600)
debug_text.fill_color = mcrfpy.Color(200, 200, 255)
ui.append(debug_text)

# Add legend
legend = mcrfpy.Caption("@ Player  E Enemy  $ Treasure  P Patrol", 25, 620)
legend.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(legend)

# Set up input handling
mcrfpy.keypressScene(handle_keypress)

# Set up animation timer
mcrfpy.setTimer("entities", update_entities, 16)  # 60 FPS

# Show scene
mcrfpy.setScene("pathfinding_showcase")

print("\nShowcase ready! Move with WASD and watch entities react.")
