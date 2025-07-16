#!/usr/bin/env python3
"""
Path & Vision Sizzle Reel
=========================

A choreographed demo showing:
- Smooth entity movement along paths
- Camera following with grid center animation
- Field of view updates as entities move
- Dramatic perspective transitions with zoom effects
"""

import mcrfpy
import sys

# Colors
WALL_COLOR = mcrfpy.Color(40, 30, 30)
FLOOR_COLOR = mcrfpy.Color(80, 80, 100)
PATH_COLOR = mcrfpy.Color(120, 120, 180)
DARK_FLOOR = mcrfpy.Color(40, 40, 50)

# Global state
grid = None
player = None
enemy = None
sequence_step = 0
player_path = []
enemy_path = []
player_path_index = 0
enemy_path_index = 0

def create_scene():
    """Create the demo environment"""
    global grid, player, enemy
    
    mcrfpy.createScene("path_vision_demo")
    
    # Create larger grid for more dramatic movement
    grid = mcrfpy.Grid(grid_x=40, grid_y=25)
    grid.fill_color = mcrfpy.Color(20, 20, 30)
    
    # Map layout - interconnected rooms with corridors
    map_layout = [
        "########################################",  # 0
        "#......##########......################",  # 1
        "#......##########......################",  # 2
        "#......##########......################",  # 3
        "#......#.........#.....################",  # 4
        "#......#.........#.....################",  # 5
        "####.###.........####.#################",  # 6
        "####.....................##############",  # 7
        "####.....................##############",  # 8
        "####.###.........####.#################",  # 9
        "#......#.........#.....################",  # 10
        "#......#.........#.....################",  # 11
        "#......#.........#.....################",  # 12
        "#......###.....###.....################",  # 13
        "#......###.....###.....################",  # 14
        "#......###.....###.....#########......#",  # 15
        "#......###.....###.....#########......#",  # 16
        "#......###.....###.....#########......#",  # 17
        "#####.############.#############......#",  # 18
        "#####...........................#.....#",  # 19
        "#####...........................#.....#",  # 20
        "#####.############.#############......#",  # 21
        "#......###########.##########.........#",  # 22
        "#......###########.##########.........#",  # 23
        "########################################",  # 24
    ]
    
    # Build the map
    for y, row in enumerate(map_layout):
        for x, char in enumerate(row):
            cell = grid.at(x, y)
            if char == '#':
                cell.walkable = False
                cell.transparent = False
                cell.color = WALL_COLOR
            else:
                cell.walkable = True
                cell.transparent = True
                cell.color = FLOOR_COLOR
    
    # Create player in top-left room
    player = mcrfpy.Entity(3, 3, grid=grid)
    player.sprite_index = 64  # @
    
    # Create enemy in bottom-right area
    enemy = mcrfpy.Entity(35, 20, grid=grid)
    enemy.sprite_index = 69  # E
    
    # Initial visibility
    player.update_visibility()
    enemy.update_visibility()
    
    # Set initial perspective to player
    grid.perspective = 0

def setup_paths():
    """Define the paths for entities"""
    global player_path, enemy_path
    
    # Player path: Top-left room → corridor → middle room
    player_waypoints = [
        (3, 3),    # Start
        (3, 8),    # Move down
        (7, 8),    # Enter corridor
        (16, 8),   # Through corridor
        (16, 12),  # Enter middle room
        (12, 12),  # Move in room
        (12, 16),  # Move down
        (16, 16),  # Move right
        (16, 19),  # Exit room
        (25, 19),  # Move right
        (30, 19),  # Continue
        (35, 19),  # Near enemy start
    ]
    
    # Enemy path: Bottom-right → around → approach player area
    enemy_waypoints = [
        (35, 20),  # Start
        (30, 20),  # Move left
        (25, 20),  # Continue
        (20, 20),  # Continue
        (16, 20),  # Corridor junction
        (16, 16),  # Move up (might see player)
        (16, 12),  # Continue up
        (16, 8),   # Top corridor
        (10, 8),   # Move left
        (7, 8),    # Continue
        (3, 8),    # Player's area
        (3, 12),   # Move down
    ]
    
    # Calculate full paths using pathfinding
    player_path = []
    for i in range(len(player_waypoints) - 1):
        x1, y1 = player_waypoints[i]
        x2, y2 = player_waypoints[i + 1]
        
        # Use grid's A* pathfinding
        segment = grid.compute_astar_path(x1, y1, x2, y2)
        if segment:
            # Add segment (avoiding duplicates)
            if not player_path or segment[0] != player_path[-1]:
                player_path.extend(segment)
            else:
                player_path.extend(segment[1:])
    
    enemy_path = []
    for i in range(len(enemy_waypoints) - 1):
        x1, y1 = enemy_waypoints[i]
        x2, y2 = enemy_waypoints[i + 1]
        
        segment = grid.compute_astar_path(x1, y1, x2, y2)
        if segment:
            if not enemy_path or segment[0] != enemy_path[-1]:
                enemy_path.extend(segment)
            else:
                enemy_path.extend(segment[1:])
    
    print(f"Player path: {len(player_path)} steps")
    print(f"Enemy path: {len(enemy_path)} steps")

def setup_ui():
    """Create UI elements"""
    ui = mcrfpy.sceneUI("path_vision_demo")
    ui.append(grid)
    
    # Position and size grid
    grid.position = (50, 80)
    grid.size = (700, 500)  # Adjust based on zoom
    
    # Title
    title = mcrfpy.Caption("Path & Vision Sizzle Reel", 300, 20)
    title.fill_color = mcrfpy.Color(255, 255, 255)
    ui.append(title)
    
    # Status
    global status_text, perspective_text
    status_text = mcrfpy.Caption("Starting demo...", 50, 50)
    status_text.fill_color = mcrfpy.Color(200, 200, 200)
    ui.append(status_text)
    
    perspective_text = mcrfpy.Caption("Perspective: Player", 550, 50)
    perspective_text.fill_color = mcrfpy.Color(100, 255, 100)
    ui.append(perspective_text)
    
    # Controls
    controls = mcrfpy.Caption("Space: Pause/Resume | R: Restart | Q: Quit", 250, 600)
    controls.fill_color = mcrfpy.Color(150, 150, 150)
    ui.append(controls)

# Animation control
paused = False
move_timer = 0
zoom_transition = False

def move_entity_smooth(entity, target_x, target_y, duration=0.3):
    """Smoothly animate entity to position"""
    # Create position animation
    anim_x = mcrfpy.Animation("x", float(target_x), duration, "easeInOut")
    anim_y = mcrfpy.Animation("y", float(target_y), duration, "easeInOut")
    
    anim_x.start(entity)
    anim_y.start(entity)

def update_camera_smooth(center_x, center_y, duration=0.3):
    """Smoothly move camera center"""
    # Convert grid coords to pixel coords (assuming 16x16 tiles)
    pixel_x = center_x * 16
    pixel_y = center_y * 16
    
    anim = mcrfpy.Animation("center", (pixel_x, pixel_y), duration, "easeOut")
    anim.start(grid)

def start_perspective_transition():
    """Begin the dramatic perspective shift"""
    global zoom_transition, sequence_step
    zoom_transition = True
    sequence_step = 100  # Special sequence number
    
    status_text.text = "Perspective shift: Zooming out..."
    
    # Zoom out with elastic easing
    zoom_out = mcrfpy.Animation("zoom", 0.5, 2.0, "easeInExpo")
    zoom_out.start(grid)
    
    # Schedule the perspective switch
    mcrfpy.setTimer("switch_perspective", switch_perspective, 2100)

def switch_perspective(dt):
    """Switch perspective at the peak of zoom"""
    global sequence_step
    
    # Switch to enemy perspective
    grid.perspective = 1
    perspective_text.text = "Perspective: Enemy"
    perspective_text.fill_color = mcrfpy.Color(255, 100, 100)
    
    status_text.text = "Perspective shift: Following enemy..."
    
    # Update camera to enemy position
    update_camera_smooth(enemy.x, enemy.y, 0.1)
    
    # Zoom back in
    zoom_in = mcrfpy.Animation("zoom", 1.2, 2.0, "easeOutExpo")
    zoom_in.start(grid)
    
    # Resume sequence
    mcrfpy.setTimer("resume_enemy", resume_enemy_sequence, 2100)
    
    # Cancel this timer
    mcrfpy.delTimer("switch_perspective")

def resume_enemy_sequence(dt):
    """Resume following enemy after perspective shift"""
    global sequence_step, zoom_transition
    zoom_transition = False
    sequence_step = 101  # Continue with enemy movement
    mcrfpy.delTimer("resume_enemy")

def sequence_tick(dt):
    """Main sequence controller"""
    global sequence_step, player_path_index, enemy_path_index, move_timer
    
    if paused or zoom_transition:
        return
    
    move_timer += dt
    if move_timer < 400:  # Move every 400ms
        return
    move_timer = 0
    
    if sequence_step < 50:
        # Phase 1: Follow player movement
        if player_path_index < len(player_path):
            x, y = player_path[player_path_index]
            move_entity_smooth(player, x, y)
            player.update_visibility()
            
            # Camera follows player
            if grid.perspective == 0:
                update_camera_smooth(player.x, player.y)
            
            player_path_index += 1
            status_text.text = f"Player moving... Step {player_path_index}/{len(player_path)}"
            
            # Start enemy movement after player has moved a bit
            if player_path_index == 10:
                sequence_step = 1  # Enable enemy movement
        else:
            # Player reached destination, start perspective transition
            start_perspective_transition()
    
    if sequence_step >= 1 and sequence_step < 50:
        # Phase 2: Enemy movement (concurrent with player)
        if enemy_path_index < len(enemy_path):
            x, y = enemy_path[enemy_path_index]
            move_entity_smooth(enemy, x, y)
            enemy.update_visibility()
            
            # Check if enemy is visible to player
            if grid.perspective == 0:
                enemy_cell_idx = int(enemy.y) * grid.grid_x + int(enemy.x)
                if enemy_cell_idx < len(player.gridstate) and player.gridstate[enemy_cell_idx].visible:
                    status_text.text = "Enemy spotted!"
                
            enemy_path_index += 1
    
    elif sequence_step == 101:
        # Phase 3: Continue following enemy after perspective shift
        if enemy_path_index < len(enemy_path):
            x, y = enemy_path[enemy_path_index]
            move_entity_smooth(enemy, x, y)
            enemy.update_visibility()
            
            # Camera follows enemy
            update_camera_smooth(enemy.x, enemy.y)
            
            enemy_path_index += 1
            status_text.text = f"Following enemy... Step {enemy_path_index}/{len(enemy_path)}"
        else:
            status_text.text = "Demo complete! Press R to restart"
            sequence_step = 200  # Done

def handle_keys(key, state):
    """Handle keyboard input"""
    global paused, sequence_step, player_path_index, enemy_path_index, move_timer
    key = key.lower()
    if state != "start":
        return
    
    if key == "q":
        print("Exiting sizzle reel...")
        sys.exit(0)
    elif key == "space":
        paused = not paused
        status_text.text = "PAUSED" if paused else "Running..."
    elif key == "r":
        # Reset everything
        player.x, player.y = 3, 3
        enemy.x, enemy.y = 35, 20
        player.update_visibility()
        enemy.update_visibility()
        grid.perspective = 0
        perspective_text.text = "Perspective: Player"
        perspective_text.fill_color = mcrfpy.Color(100, 255, 100)
        sequence_step = 0
        player_path_index = 0
        enemy_path_index = 0
        move_timer = 0
        update_camera_smooth(player.x, player.y, 0.5)
        
        # Reset zoom
        zoom_reset = mcrfpy.Animation("zoom", 1.2, 0.5, "easeOut")
        zoom_reset.start(grid)
        
        status_text.text = "Demo restarted!"

# Initialize everything
print("Path & Vision Sizzle Reel")
print("=========================")
print("Demonstrating:")
print("- Smooth entity movement along calculated paths")
print("- Camera following with animated grid centering")
print("- Field of view updates as entities move")
print("- Dramatic perspective transitions with zoom effects")
print()

create_scene()
setup_paths()
setup_ui()

# Set scene and input
mcrfpy.setScene("path_vision_demo")
mcrfpy.keypressScene(handle_keys)

# Initial camera setup
grid.zoom = 1.2
update_camera_smooth(player.x, player.y, 0.1)

# Start the sequence
mcrfpy.setTimer("sequence", sequence_tick, 50)  # Tick every 50ms

print("Demo started!")
print("- Player (@) will navigate through rooms")
print("- Enemy (E) will move on a different path")
print("- Watch for the dramatic perspective shift!")
print()
print("Controls: Space=Pause, R=Restart, Q=Quit")
