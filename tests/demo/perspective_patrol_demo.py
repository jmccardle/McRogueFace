#!/usr/bin/env python3
"""
Perspective Patrol Demo
=======================

Demonstrates the FOV/perspective system with an animated patrolling entity.

Features:
- 20x20 grid with 10x10 opaque obstacle in center
- Entity patrols around the obstacle in a square pattern
- ColorLayer shows fog of war (visible/discovered/unknown)
- Press 'R' to reset vision (shows unknown vs discovered difference)
- Press 'Space' to pause/resume patrol
"""

import mcrfpy

# Patrol waypoints (clockwise around the center obstacle)
WAYPOINTS = [
    (3, 3),    # Top-left
    (16, 3),   # Top-right
    (16, 16),  # Bottom-right
    (3, 16),   # Bottom-left
]

# State
current_waypoint = 0
patrol_paused = False
move_timer_ms = 150  # Time between moves

# Global references
g_grid = None
g_patrol = None
g_fov_layer = None

def setup_scene():
    """Create the demo scene"""
    global g_grid, g_patrol, g_fov_layer

    patrol_demo = mcrfpy.Scene("patrol_demo")
    patrol_demo.activate()

    ui = patrol_demo.children

    # Title
    title = mcrfpy.Caption(text="Perspective Patrol Demo", pos=(10, 10))
    title.fill_color = mcrfpy.Color(255, 255, 255)
    ui.append(title)

    # Instructions
    instructions = mcrfpy.Caption(text="[R] Reset vision  [Space] Pause/Resume  [Q] Quit", pos=(10, 35))
    instructions.fill_color = mcrfpy.Color(180, 180, 180)
    ui.append(instructions)

    # Create grid (20x20, each cell 24px) - centered in 1024x768 window
    grid_size_px = 480
    grid = mcrfpy.Grid(
        pos=((1024 - grid_size_px) // 2, (768 - grid_size_px) // 2),
        size=(grid_size_px, grid_size_px),
        grid_size=(20, 20),
        texture=None
    )
    grid.center = (10*16, 10*16)
    grid.fill_color = mcrfpy.Color(40, 40, 50)  # Dark floor background
    ui.append(grid)

    # Set FOV settings
    grid.fov = mcrfpy.FOV.SHADOW
    grid.fov_radius = 8

    # Initialize all cells as walkable/transparent (floor)
    for y in range(20):
        for x in range(20):
            point = grid.at(x, y)
            point.walkable = True
            point.transparent = True

    # Create 10x10 obstacle box in center (cells 5-14 in both dimensions)
    for y in range(5, 15):
        for x in range(5, 15):
            point = grid.at(x, y)
            point.walkable = False
            point.transparent = False

    # Create a color layer for the walls (so we can see them)
    wall_layer = grid.add_layer('color', z_index=-2)
    wall_layer.fill((40, 40, 50, 255))  # Match floor color

    # Draw walls on the wall layer
    for y in range(5, 15):
        for x in range(5, 15):
            wall_layer.set(x, y, mcrfpy.Color(100, 70, 50, 255))  # Brown walls

    # Create FOV layer (above walls, below entities)
    fov_layer = grid.add_layer('color', z_index=-1)
    fov_layer.fill((0, 0, 0, 255))  # Start completely black (unknown)

    # Create patrolling entity
    patrol = mcrfpy.Entity(WAYPOINTS[0])
    patrol.sprite_index = 64  # '@' character typically
    grid.entities.append(patrol)

    # Bind FOV layer to entity
    fov_layer.apply_perspective(
        entity=patrol,
        visible=(0, 0, 0, 0),              # Fully transparent when visible
        discovered=(20, 20, 40, 180),       # Dark blue-gray when discovered
        unknown=(0, 0, 0, 255)              # Black when never seen
    )

    # Initial visibility update
    patrol.update_visibility()

    # Store references for timer callbacks
    g_grid = grid
    g_patrol = patrol
    g_fov_layer = fov_layer

    # Status caption (below centered grid)
    status = mcrfpy.Caption(text="Status: Patrolling", pos=(10, 720))
    status.fill_color = mcrfpy.Color(100, 255, 100)
    status.name = "status"
    ui.append(status)

    # Set up keyboard handler
    patrol_demo.on_key = on_keypress

    # Start patrol timer
    global patrol_timer
    patrol_timer = mcrfpy.Timer("patrol", patrol_step, move_timer_ms)

def patrol_step(timer, runtime):
    """Move entity one step toward current waypoint"""
    global current_waypoint, patrol_paused

    if patrol_paused:
        return

    # Get current position and target
    px, py = int(g_patrol.x), int(g_patrol.y)
    tx, ty = WAYPOINTS[current_waypoint]

    # Calculate direction
    dx = 0 if tx == px else (1 if tx > px else -1)
    dy = 0 if ty == py else (1 if ty > py else -1)

    # Move one step (prefer horizontal, then vertical)
    if dx != 0:
        g_patrol.x = px + dx
    elif dy != 0:
        g_patrol.y = py + dy

    # Update visibility after move
    g_patrol.update_visibility()

    # Check if reached waypoint
    if int(g_patrol.x) == tx and int(g_patrol.y) == ty:
        current_waypoint = (current_waypoint + 1) % len(WAYPOINTS)
        update_status(f"Reached waypoint, heading to {WAYPOINTS[current_waypoint]}")

def on_keypress(key, state):
    """Handle keyboard input"""
    global patrol_paused

    if state != "start":
        return

    if key == "R":
        reset_vision()
    elif key == "Space":
        patrol_paused = not patrol_paused
        if patrol_paused:
            update_status("Status: PAUSED")
        else:
            update_status("Status: Patrolling")
    elif key == "Q":
        mcrfpy.current_scene = None

def reset_vision():
    """Reset entity's discovered state to demonstrate unknown vs discovered"""
    global g_patrol, g_fov_layer

    # Clear entity's gridstate (forget everything)
    for state in g_patrol.gridstate:
        state.visible = False
        state.discovered = False

    # Re-fill the layer with unknown color
    g_fov_layer.fill((0, 0, 0, 255))

    # Update visibility from current position (will mark current FOV as visible)
    g_patrol.update_visibility()

    update_status("Vision RESET - watch discovered vs unknown!")

def update_status(text):
    """Update status caption"""
    ui = patrol_demo.children
    for element in ui:
        if hasattr(element, 'name') and element.name == "status":
            element.text = text
            break

# Run the demo
setup_scene()
