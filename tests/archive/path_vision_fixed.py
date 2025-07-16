#!/usr/bin/env python3
"""
Path & Vision Sizzle Reel (Fixed)
=================================

Fixed version with proper animation chaining to prevent glitches.
"""

import mcrfpy
import sys

class PathAnimator:
    """Handles step-by-step animation with proper completion tracking"""
    
    def __init__(self, entity, name="animator"):
        self.entity = entity
        self.name = name
        self.path = []
        self.current_index = 0
        self.step_duration = 0.4
        self.animating = False
        self.on_step = None
        self.on_complete = None
        
    def set_path(self, path):
        """Set the path to animate along"""
        self.path = path
        self.current_index = 0
        
    def start(self):
        """Start animating"""
        if not self.path:
            return
            
        self.animating = True
        self.current_index = 0
        self._move_to_next()
        
    def stop(self):
        """Stop animating"""
        self.animating = False
        mcrfpy.delTimer(f"{self.name}_check")
        
    def _move_to_next(self):
        """Move to next position in path"""
        if not self.animating or self.current_index >= len(self.path):
            self.animating = False
            if self.on_complete:
                self.on_complete()
            return
            
        # Get next position
        x, y = self.path[self.current_index]
        
        # Create animations
        anim_x = mcrfpy.Animation("x", float(x), self.step_duration, "easeInOut")
        anim_y = mcrfpy.Animation("y", float(y), self.step_duration, "easeInOut")
        
        anim_x.start(self.entity)
        anim_y.start(self.entity)
        
        # Update visibility
        self.entity.update_visibility()
        
        # Callback for each step
        if self.on_step:
            self.on_step(self.current_index, x, y)
        
        # Schedule next move
        delay = int(self.step_duration * 1000) + 50  # Add small buffer
        mcrfpy.setTimer(f"{self.name}_next", self._handle_next, delay)
        
    def _handle_next(self, dt):
        """Timer callback to move to next position"""
        self.current_index += 1
        mcrfpy.delTimer(f"{self.name}_next")
        self._move_to_next()

# Global state
grid = None
player = None
enemy = None
player_animator = None
enemy_animator = None
demo_phase = 0

def create_scene():
    """Create the demo environment"""
    global grid, player, enemy
    
    mcrfpy.createScene("fixed_demo")
    
    # Create grid
    grid = mcrfpy.Grid(grid_x=30, grid_y=20)
    grid.fill_color = mcrfpy.Color(20, 20, 30)
    
    # Simple dungeon layout
    map_layout = [
        "##############################",
        "#......#########.....#########",
        "#......#########.....#########",
        "#......#.........#...#########",
        "#......#.........#...#########",
        "####.###.........#.###########",
        "####.............#.###########",
        "####.............#.###########",
        "####.###.........#.###########",
        "#......#.........#...#########",
        "#......#.........#...#########",
        "#......#########.#...........#",
        "#......#########.#...........#",
        "#......#########.#...........#",
        "#......#########.#############",
        "####.###########.............#",
        "####.........................#",
        "####.###########.............#",
        "#......#########.............#",
        "##############################",
    ]
    
    # Build map
    for y, row in enumerate(map_layout):
        for x, char in enumerate(row):
            cell = grid.at(x, y)
            if char == '#':
                cell.walkable = False
                cell.transparent = False
                cell.color = mcrfpy.Color(40, 30, 30)
            else:
                cell.walkable = True
                cell.transparent = True
                cell.color = mcrfpy.Color(80, 80, 100)
    
    # Create entities
    player = mcrfpy.Entity(3, 3, grid=grid)
    player.sprite_index = 64  # @
    
    enemy = mcrfpy.Entity(26, 16, grid=grid)
    enemy.sprite_index = 69  # E
    
    # Initial visibility
    player.update_visibility()
    enemy.update_visibility()
    
    # Set initial perspective
    grid.perspective = 0

def setup_ui():
    """Create UI elements"""
    ui = mcrfpy.sceneUI("fixed_demo")
    ui.append(grid)
    
    grid.position = (50, 80)
    grid.size = (700, 500)
    
    title = mcrfpy.Caption("Path & Vision Demo (Fixed)", 300, 20)
    title.fill_color = mcrfpy.Color(255, 255, 255)
    ui.append(title)
    
    global status_text, perspective_text
    status_text = mcrfpy.Caption("Initializing...", 50, 50)
    status_text.fill_color = mcrfpy.Color(200, 200, 200)
    ui.append(status_text)
    
    perspective_text = mcrfpy.Caption("Perspective: Player", 550, 50)
    perspective_text.fill_color = mcrfpy.Color(100, 255, 100)
    ui.append(perspective_text)
    
    controls = mcrfpy.Caption("Space: Start/Pause | R: Restart | Q: Quit", 250, 600)
    controls.fill_color = mcrfpy.Color(150, 150, 150)
    ui.append(controls)

def update_camera_smooth(target, duration=0.3):
    """Smoothly move camera to entity"""
    center_x = target.x * 23  # Approximate pixel size
    center_y = target.y * 23
    
    cam_anim = mcrfpy.Animation("center", (center_x, center_y), duration, "easeOut")
    cam_anim.start(grid)

def start_demo():
    """Start the demo sequence"""
    global demo_phase, player_animator, enemy_animator
    
    demo_phase = 1
    status_text.text = "Phase 1: Player movement with camera follow"
    
    # Player path
    player_path = [
        (3, 3), (3, 6), (4, 6), (7, 6), (7, 8),
        (10, 8), (13, 8), (16, 8), (16, 10),
        (16, 13), (16, 16), (20, 16), (24, 16)
    ]
    
    # Setup player animator
    player_animator = PathAnimator(player, "player")
    player_animator.set_path(player_path)
    player_animator.step_duration = 0.5
    
    def on_player_step(index, x, y):
        """Called for each player step"""
        status_text.text = f"Player step {index+1}/{len(player_path)}"
        if grid.perspective == 0:
            update_camera_smooth(player, 0.4)
    
    def on_player_complete():
        """Called when player path is complete"""
        start_phase_2()
    
    player_animator.on_step = on_player_step
    player_animator.on_complete = on_player_complete
    player_animator.start()

def start_phase_2():
    """Start enemy movement phase"""
    global demo_phase
    
    demo_phase = 2
    status_text.text = "Phase 2: Enemy movement (may enter player's view)"
    
    # Enemy path
    enemy_path = [
        (26, 16), (22, 16), (18, 16), (16, 16),
        (16, 13), (16, 10), (16, 8), (13, 8),
        (10, 8), (7, 8), (7, 6), (4, 6)
    ]
    
    # Setup enemy animator
    enemy_animator.set_path(enemy_path)
    enemy_animator.step_duration = 0.4
    
    def on_enemy_step(index, x, y):
        """Check if enemy is visible to player"""
        if grid.perspective == 0:
            # Check if enemy is in player's view
            enemy_idx = int(y) * grid.grid_x + int(x)
            if enemy_idx < len(player.gridstate) and player.gridstate[enemy_idx].visible:
                status_text.text = "Enemy spotted in player's view!"
    
    def on_enemy_complete():
        """Start perspective transition"""
        start_phase_3()
    
    enemy_animator.on_step = on_enemy_step
    enemy_animator.on_complete = on_enemy_complete
    enemy_animator.start()

def start_phase_3():
    """Dramatic perspective shift"""
    global demo_phase
    
    demo_phase = 3
    status_text.text = "Phase 3: Perspective shift..."
    
    # Stop any ongoing animations
    player_animator.stop()
    enemy_animator.stop()
    
    # Zoom out
    zoom_out = mcrfpy.Animation("zoom", 0.6, 2.0, "easeInExpo")
    zoom_out.start(grid)
    
    # Schedule perspective switch
    mcrfpy.setTimer("switch_persp", switch_perspective, 2100)

def switch_perspective(dt):
    """Switch to enemy perspective"""
    grid.perspective = 1
    perspective_text.text = "Perspective: Enemy"
    perspective_text.fill_color = mcrfpy.Color(255, 100, 100)
    
    # Update camera
    update_camera_smooth(enemy, 0.5)
    
    # Zoom back in
    zoom_in = mcrfpy.Animation("zoom", 1.0, 2.0, "easeOutExpo")
    zoom_in.start(grid)
    
    status_text.text = "Now following enemy perspective"
    
    # Clean up timer
    mcrfpy.delTimer("switch_persp")
    
    # Continue enemy movement after transition
    mcrfpy.setTimer("continue_enemy", continue_enemy_movement, 2500)

def continue_enemy_movement(dt):
    """Continue enemy movement after perspective shift"""
    mcrfpy.delTimer("continue_enemy")
    
    # Continue path
    enemy_path_2 = [
        (4, 6), (3, 6), (3, 3), (3, 2), (3, 1)
    ]
    
    enemy_animator.set_path(enemy_path_2)
    
    def on_step(index, x, y):
        update_camera_smooth(enemy, 0.4)
        status_text.text = f"Following enemy: step {index+1}"
    
    def on_complete():
        status_text.text = "Demo complete! Press R to restart"
    
    enemy_animator.on_step = on_step
    enemy_animator.on_complete = on_complete
    enemy_animator.start()

# Control state
running = False

def handle_keys(key, state):
    """Handle keyboard input"""
    global running
    
    if state != "start":
        return
    
    key = key.lower()
    
    if key == "q":
        sys.exit(0)
    elif key == "space":
        if not running:
            running = True
            start_demo()
        else:
            running = False
            player_animator.stop()
            enemy_animator.stop()
            status_text.text = "Paused"
    elif key == "r":
        # Reset everything
        player.x, player.y = 3, 3
        enemy.x, enemy.y = 26, 16
        grid.perspective = 0
        perspective_text.text = "Perspective: Player"
        perspective_text.fill_color = mcrfpy.Color(100, 255, 100)
        grid.zoom = 1.0
        update_camera_smooth(player, 0.5)
        
        if running:
            player_animator.stop()
            enemy_animator.stop()
            running = False
        
        status_text.text = "Reset - Press SPACE to start"

# Initialize
create_scene()
setup_ui()

# Setup animators
player_animator = PathAnimator(player, "player")
enemy_animator = PathAnimator(enemy, "enemy")

# Set scene
mcrfpy.setScene("fixed_demo")
mcrfpy.keypressScene(handle_keys)

# Initial camera
grid.zoom = 1.0
update_camera_smooth(player, 0.5)

print("Path & Vision Demo (Fixed)")
print("==========================")
print("This version properly chains animations to prevent glitches.")
print()
print("The demo will:")
print("1. Move player with camera following")
print("2. Move enemy (may enter player's view)")
print("3. Dramatic perspective shift to enemy")
print("4. Continue following enemy")
print()
print("Press SPACE to start, Q to quit")