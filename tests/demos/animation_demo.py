#!/usr/bin/env python3
"""
Animation Demo: Grid Center & Entity Movement
=============================================

Demonstrates:
- Animated grid centering following entity
- Smooth entity movement along paths
- Perspective shifts with zoom transitions
- Field of view updates
"""

import mcrfpy
import sys

# Setup scene
mcrfpy.createScene("anim_demo")

# Create grid
grid = mcrfpy.Grid(grid_x=30, grid_y=20)
grid.fill_color = mcrfpy.Color(20, 20, 30)

# Simple map
for y in range(20):
    for x in range(30):
        cell = grid.at(x, y)
        # Create walls around edges and some obstacles
        if x == 0 or x == 29 or y == 0 or y == 19:
            cell.walkable = False
            cell.transparent = False
            cell.color = mcrfpy.Color(40, 30, 30)
        elif (x == 10 and 5 <= y <= 15) or (y == 10 and 5 <= x <= 25):
            cell.walkable = False
            cell.transparent = False
            cell.color = mcrfpy.Color(60, 40, 40)
        else:
            cell.walkable = True
            cell.transparent = True
            cell.color = mcrfpy.Color(80, 80, 100)

# Create entities
player = mcrfpy.Entity(5, 5, grid=grid)
player.sprite_index = 64  # @

enemy = mcrfpy.Entity(25, 15, grid=grid)
enemy.sprite_index = 69  # E

# Update visibility
player.update_visibility()
enemy.update_visibility()

# UI setup
ui = mcrfpy.sceneUI("anim_demo")
ui.append(grid)
grid.position = (100, 100)
grid.size = (600, 400)

title = mcrfpy.Caption("Animation Demo - Grid Center & Entity Movement", 200, 20)
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

status = mcrfpy.Caption("Press 1: Move Player | 2: Move Enemy | 3: Perspective Shift | Q: Quit", 100, 50)
status.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(status)

info = mcrfpy.Caption("Perspective: Player", 500, 70)
info.fill_color = mcrfpy.Color(100, 255, 100)
ui.append(info)

# Movement functions
def move_player_demo():
    """Demo player movement with camera follow"""
    # Calculate path to a destination
    path = player.path_to(20, 10)
    if not path:
        status.text = "No path available!"
        return
    
    status.text = f"Moving player along {len(path)} steps..."
    
    # Animate along path
    for i, (x, y) in enumerate(path[:5]):  # First 5 steps
        delay = i * 500  # 500ms between steps
        
        # Schedule movement
        def move_step(dt, px=x, py=y):
            # Animate entity position
            anim_x = mcrfpy.Animation("x", float(px), 0.4, "easeInOut")
            anim_y = mcrfpy.Animation("y", float(py), 0.4, "easeInOut")
            anim_x.start(player)
            anim_y.start(player)
            
            # Update visibility
            player.update_visibility()
            
            # Animate camera to follow
            center_x = px * 16  # Assuming 16x16 tiles
            center_y = py * 16
            cam_anim = mcrfpy.Animation("center", (center_x, center_y), 0.4, "easeOut")
            cam_anim.start(grid)
        
        mcrfpy.setTimer(f"player_move_{i}", move_step, delay)

def move_enemy_demo():
    """Demo enemy movement"""
    # Calculate path
    path = enemy.path_to(10, 5)
    if not path:
        status.text = "Enemy has no path!"
        return
    
    status.text = f"Moving enemy along {len(path)} steps..."
    
    # Animate along path
    for i, (x, y) in enumerate(path[:5]):  # First 5 steps
        delay = i * 500
        
        def move_step(dt, ex=x, ey=y):
            anim_x = mcrfpy.Animation("x", float(ex), 0.4, "easeInOut")
            anim_y = mcrfpy.Animation("y", float(ey), 0.4, "easeInOut")
            anim_x.start(enemy)
            anim_y.start(enemy)
            enemy.update_visibility()
            
            # If following enemy, update camera
            if grid.perspective == 1:
                center_x = ex * 16
                center_y = ey * 16
                cam_anim = mcrfpy.Animation("center", (center_x, center_y), 0.4, "easeOut")
                cam_anim.start(grid)
        
        mcrfpy.setTimer(f"enemy_move_{i}", move_step, delay)

def perspective_shift_demo():
    """Demo dramatic perspective shift"""
    status.text = "Perspective shift in progress..."
    
    # Phase 1: Zoom out
    zoom_out = mcrfpy.Animation("zoom", 0.5, 1.5, "easeInExpo")
    zoom_out.start(grid)
    
    # Phase 2: Switch perspective at peak
    def switch_perspective(dt):
        if grid.perspective == 0:
            grid.perspective = 1
            info.text = "Perspective: Enemy"
            info.fill_color = mcrfpy.Color(255, 100, 100)
            target = enemy
        else:
            grid.perspective = 0
            info.text = "Perspective: Player"
            info.fill_color = mcrfpy.Color(100, 255, 100)
            target = player
        
        # Update camera to new target
        center_x = target.x * 16
        center_y = target.y * 16
        cam_anim = mcrfpy.Animation("center", (center_x, center_y), 0.5, "linear")
        cam_anim.start(grid)
    
    mcrfpy.setTimer("switch_persp", switch_perspective, 1600)
    
    # Phase 3: Zoom back in
    def zoom_in(dt):
        zoom_in_anim = mcrfpy.Animation("zoom", 1.0, 1.5, "easeOutExpo")
        zoom_in_anim.start(grid)
        status.text = "Perspective shift complete!"
    
    mcrfpy.setTimer("zoom_in", zoom_in, 2100)

# Input handler
def handle_input(key, state):
    if state != "start":
        return
    
    if key == "q":
        print("Exiting demo...")
        sys.exit(0)
    elif key == "1":
        move_player_demo()
    elif key == "2":
        move_enemy_demo()
    elif key == "3":
        perspective_shift_demo()

# Set scene
mcrfpy.setScene("anim_demo")
mcrfpy.keypressScene(handle_input)

# Initial setup
grid.perspective = 0
grid.zoom = 1.0

# Center on player initially
center_x = player.x * 16
center_y = player.y * 16
initial_cam = mcrfpy.Animation("center", (center_x, center_y), 0.5, "easeOut")
initial_cam.start(grid)

print("Animation Demo Started!")
print("======================")
print("Press 1: Animate player movement with camera follow")
print("Press 2: Animate enemy movement")
print("Press 3: Dramatic perspective shift with zoom")
print("Press Q: Quit")
print()
print("Watch how the grid center smoothly follows entities")
print("and how perspective shifts create cinematic effects!")