#!/usr/bin/env python3
"""
Test Animation Chaining
=======================

Demonstrates proper animation chaining to avoid glitches.
"""

import mcrfpy
import sys

class PathAnimator:
    """Handles step-by-step path animation with proper chaining"""
    
    def __init__(self, entity, path, step_duration=0.3, on_complete=None):
        self.entity = entity
        self.path = path
        self.current_index = 0
        self.step_duration = step_duration
        self.on_complete = on_complete
        self.animating = False
        self.check_timer_name = f"path_check_{id(self)}"
        
    def start(self):
        """Start animating along the path"""
        if not self.path or self.animating:
            return
        
        self.current_index = 0
        self.animating = True
        self._animate_next_step()
        
    def _animate_next_step(self):
        """Animate to the next position in the path"""
        if self.current_index >= len(self.path):
            # Path complete
            self.animating = False
            mcrfpy.delTimer(self.check_timer_name)
            if self.on_complete:
                self.on_complete()
            return
            
        # Get target position
        target_x, target_y = self.path[self.current_index]
        
        # Create animations
        self.anim_x = mcrfpy.Animation("x", float(target_x), self.step_duration, "easeInOut")
        self.anim_y = mcrfpy.Animation("y", float(target_y), self.step_duration, "easeInOut")
        
        # Start animations
        self.anim_x.start(self.entity)
        self.anim_y.start(self.entity)
        
        # Update visibility if entity has this method
        if hasattr(self.entity, 'update_visibility'):
            self.entity.update_visibility()
        
        # Set timer to check completion
        mcrfpy.setTimer(self.check_timer_name, self._check_completion, 50)
        
    def _check_completion(self, dt):
        """Check if current animation is complete"""
        if hasattr(self.anim_x, 'is_complete') and self.anim_x.is_complete:
            # Move to next step
            self.current_index += 1
            mcrfpy.delTimer(self.check_timer_name)
            self._animate_next_step()

# Create test scene
mcrfpy.createScene("chain_test")

# Create grid
grid = mcrfpy.Grid(grid_x=20, grid_y=15)
grid.fill_color = mcrfpy.Color(20, 20, 30)

# Add a color layer for cell coloring
color_layer = grid.add_layer("color", z_index=-1)

# Simple map
for y in range(15):
    for x in range(20):
        cell = grid.at(x, y)
        if x == 0 or x == 19 or y == 0 or y == 14:
            cell.walkable = False
            cell.transparent = False
            color_layer.set(x, y, mcrfpy.Color(60, 40, 40))
        else:
            cell.walkable = True
            cell.transparent = True
            color_layer.set(x, y, mcrfpy.Color(100, 100, 120))

# Create entities
player = mcrfpy.Entity((2, 2), grid=grid)
player.sprite_index = 64  # @

enemy = mcrfpy.Entity((17, 12), grid=grid)
enemy.sprite_index = 69  # E

# UI setup
ui = mcrfpy.sceneUI("chain_test")
ui.append(grid)
grid.position = (100, 100)
grid.size = (600, 450)

title = mcrfpy.Caption(pos=(300, 20), text="Animation Chaining Test")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

status = mcrfpy.Caption(pos=(100, 50), text="Press 1: Animate Player | 2: Animate Enemy | 3: Both | Q: Quit")
status.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(status)

info = mcrfpy.Caption(pos=(100, 70), text="Status: Ready")
info.fill_color = mcrfpy.Color(100, 255, 100)
ui.append(info)

# Path animators
player_animator = None
enemy_animator = None

def animate_player():
    """Animate player along a path"""
    global player_animator
    
    # Define path
    path = [
        (2, 2), (3, 2), (4, 2), (5, 2), (6, 2),  # Right
        (6, 3), (6, 4), (6, 5), (6, 6),          # Down
        (7, 6), (8, 6), (9, 6), (10, 6),         # Right
        (10, 7), (10, 8), (10, 9),               # Down
    ]
    
    def on_complete():
        info.text = "Player animation complete!"
        
    player_animator = PathAnimator(player, path, step_duration=0.2, on_complete=on_complete)
    player_animator.start()
    info.text = "Animating player..."

def animate_enemy():
    """Animate enemy along a path"""
    global enemy_animator
    
    # Define path
    path = [
        (17, 12), (16, 12), (15, 12), (14, 12),  # Left
        (14, 11), (14, 10), (14, 9),             # Up
        (13, 9), (12, 9), (11, 9), (10, 9),      # Left
        (10, 8), (10, 7), (10, 6),               # Up
    ]
    
    def on_complete():
        info.text = "Enemy animation complete!"
        
    enemy_animator = PathAnimator(enemy, path, step_duration=0.25, on_complete=on_complete)
    enemy_animator.start()
    info.text = "Animating enemy..."

def animate_both():
    """Animate both entities simultaneously"""
    info.text = "Animating both entities..."
    animate_player()
    animate_enemy()

# Camera follow test
camera_follow = False

def update_camera(dt):
    """Update camera to follow player if enabled"""
    if camera_follow and player_animator and player_animator.animating:
        # Smooth camera follow
        center_x = player.x * 30  # Assuming ~30 pixels per cell
        center_y = player.y * 30
        cam_anim = mcrfpy.Animation("center", (center_x, center_y), 0.25, "linear")
        cam_anim.start(grid)

# Input handler
def handle_input(key, state):
    global camera_follow
    
    if state != "start":
        return
    
    key = key.lower()
    
    if key == "q":
        sys.exit(0)
    elif key == "num1":
        animate_player()
    elif key == "num2":
        animate_enemy()
    elif key == "num3":
        animate_both()
    elif key == "c":
        camera_follow = not camera_follow
        info.text = f"Camera follow: {'ON' if camera_follow else 'OFF'}"
    elif key == "r":
        # Reset positions
        player.x, player.y = 2, 2
        enemy.x, enemy.y = 17, 12
        info.text = "Positions reset"

# Setup
mcrfpy.setScene("chain_test")
mcrfpy.keypressScene(handle_input)

# Camera update timer
mcrfpy.setTimer("cam_update", update_camera, 100)

print("Animation Chaining Test")
print("=======================")
print("This test demonstrates proper animation chaining")
print("to avoid simultaneous position updates.")
print()
print("Controls:")
print("  1 - Animate player step by step")
print("  2 - Animate enemy step by step")
print("  3 - Animate both (simultaneous)")
print("  C - Toggle camera follow")
print("  R - Reset positions")
print("  Q - Quit")
print()
print("Notice how each entity moves one tile at a time,")
print("waiting for each step to complete before the next.")
