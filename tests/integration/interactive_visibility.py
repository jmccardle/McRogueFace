#!/usr/bin/env python3
"""
Interactive Visibility Demo
==========================

Controls:
  - WASD: Move the player (green @)
  - Arrow keys: Move enemy (red E)
  - Tab: Cycle perspective (Omniscient → Player → Enemy → Omniscient)
  - Space: Update visibility for current entity
  - R: Reset positions
"""

import mcrfpy
import sys

# Create scene and grid
visibility_demo = mcrfpy.Scene("visibility_demo")
grid = mcrfpy.Grid(grid_x=30, grid_y=20)
grid.fill_color = mcrfpy.Color(20, 20, 30)  # Dark background

# Add color layer for cell coloring
color_layer = grid.add_layer("color", z_index=-1)

# Initialize grid - all walkable and transparent
for y in range(20):
    for x in range(30):
        cell = grid.at(x, y)
        cell.walkable = True
        cell.transparent = True
        color_layer.set(x, y, mcrfpy.Color(100, 100, 120))  # Floor color

# Create walls
walls = [
    # Central cross
    [(15, y) for y in range(8, 12)],
    [(x, 10) for x in range(13, 18)],

    # Rooms
    # Top-left room
    [(x, 5) for x in range(2, 8)] + [(8, y) for y in range(2, 6)],
    [(2, y) for y in range(2, 6)] + [(x, 2) for x in range(2, 8)],

    # Top-right room
    [(x, 5) for x in range(22, 28)] + [(22, y) for y in range(2, 6)],
    [(28, y) for y in range(2, 6)] + [(x, 2) for x in range(22, 28)],

    # Bottom-left room
    [(x, 15) for x in range(2, 8)] + [(8, y) for y in range(15, 18)],
    [(2, y) for y in range(15, 18)] + [(x, 18) for x in range(2, 8)],

    # Bottom-right room
    [(x, 15) for x in range(22, 28)] + [(22, y) for y in range(15, 18)],
    [(28, y) for y in range(15, 18)] + [(x, 18) for x in range(22, 28)],
]

for wall_group in walls:
    for x, y in wall_group:
        if 0 <= x < 30 and 0 <= y < 20:
            cell = grid.at(x, y)
            cell.walkable = False
            cell.transparent = False
            color_layer.set(x, y, mcrfpy.Color(40, 20, 20))  # Wall color

# Create entities
player = mcrfpy.Entity((5, 10), grid=grid)
player.sprite_index = 64  # @
enemy = mcrfpy.Entity((25, 10), grid=grid)
enemy.sprite_index = 69  # E

# Update initial visibility
player.update_visibility()
enemy.update_visibility()

# Global state
current_perspective = -1
perspective_names = ["Omniscient", "Player", "Enemy"]

# UI Setup
ui = visibility_demo.children
ui.append(grid)
grid.position = (50, 100)
grid.size = (900, 600)  # 30*30, 20*30

# Title
title = mcrfpy.Caption(pos=(350, 20), text="Interactive Visibility Demo")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Info displays
perspective_label = mcrfpy.Caption(pos=(50, 50), text="Perspective: Omniscient")
perspective_label.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(perspective_label)

controls = mcrfpy.Caption(pos=(50, 730), text="WASD: Move player | Arrows: Move enemy | Tab: Cycle perspective | Space: Update visibility | R: Reset")
controls.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(controls)

player_info = mcrfpy.Caption(pos=(700, 50), text="Player: (5, 10)")
player_info.fill_color = mcrfpy.Color(100, 255, 100)
ui.append(player_info)

enemy_info = mcrfpy.Caption(pos=(700, 70), text="Enemy: (25, 10)")
enemy_info.fill_color = mcrfpy.Color(255, 100, 100)
ui.append(enemy_info)

# Helper functions
def move_entity(entity, dx, dy):
    """Move entity if target is walkable"""
    new_x = int(entity.x + dx)
    new_y = int(entity.y + dy)
    
    if 0 <= new_x < 30 and 0 <= new_y < 20:
        cell = grid.at(new_x, new_y)
        if cell.walkable:
            entity.x = new_x
            entity.y = new_y
            entity.update_visibility()
            return True
    return False

def update_info():
    """Update info displays"""
    player_info.text = f"Player: ({int(player.x)}, {int(player.y)})"
    enemy_info.text = f"Enemy: ({int(enemy.x)}, {int(enemy.y)})"

def cycle_perspective():
    """Cycle through perspectives"""
    global current_perspective
    
    # Cycle: -1 → 0 → 1 → -1
    current_perspective = (current_perspective + 2) % 3 - 1
    
    grid.perspective = current_perspective
    name = perspective_names[current_perspective + 1]
    perspective_label.text = f"Perspective: {name}"

# Key handlers
def handle_keys(key, state):
    """Handle keyboard input"""
    if state == "end": return
    key = key.lower()
    # Player movement (WASD)
    if key == "w":
        move_entity(player, 0, -1)
    elif key == "s":
        move_entity(player, 0, 1)
    elif key == "a":
        move_entity(player, -1, 0)
    elif key == "d":
        move_entity(player, 1, 0)
    
    # Enemy movement (Arrows)
    elif key == "up":
        move_entity(enemy, 0, -1)
    elif key == "down":
        move_entity(enemy, 0, 1)
    elif key == "left":
        move_entity(enemy, -1, 0)
    elif key == "right":
        move_entity(enemy, 1, 0)
    
    # Tab to cycle perspective
    elif key == "tab":
        cycle_perspective()
    
    # Space to update visibility
    elif key == "space":
        player.update_visibility()
        enemy.update_visibility()
        print("Updated visibility for both entities")
    
    # R to reset
    elif key == "r":
        player.x, player.y = 5, 10
        enemy.x, enemy.y = 25, 10
        player.update_visibility()
        enemy.update_visibility()
        update_info()
        print("Reset positions")
    
    # Q to quit
    elif key == "q":
        print("Exiting...")
        sys.exit(0)
    
    update_info()

# Set scene first
visibility_demo.activate()

# Register key handler (operates on current scene)
visibility_demo.on_key = handle_keys

print("Interactive Visibility Demo")
print("===========================")
print("WASD: Move player (green @)")
print("Arrows: Move enemy (red E)")
print("Tab: Cycle perspective")
print("Space: Update visibility")
print("R: Reset positions")
print("Q: Quit")
print("\nCurrent perspective: Omniscient (shows all)")
print("Try moving entities and switching perspectives!")
