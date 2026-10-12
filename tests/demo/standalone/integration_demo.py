# integration_demo.py - Milestone 8 Integration Demo
# Showcases all 3D features: terrain, entities, pathfinding, FOV, billboards, UI, input

import mcrfpy
import math
import random

DEMO_NAME = "3D Integration Demo"
DEMO_DESCRIPTION = """Complete 3D demo with terrain, player, NPC, FOV, and UI overlay.

Controls:
  Arrow keys: Move player
  Click: Move to clicked position
  ESC: Quit
"""

# Create the main scene
scene = mcrfpy.Scene("integration_demo")

# =============================================================================
# Constants
# =============================================================================
GRID_WIDTH = 32
GRID_DEPTH = 32
CELL_SIZE = 1.0
TERRAIN_Y_SCALE = 3.0
FOV_RADIUS = 10

# =============================================================================
# 3D Viewport
# =============================================================================
viewport = mcrfpy.Viewport3D(
    pos=(10, 10),
    size=(700, 550),
    render_resolution=(350, 275),
    fov=60.0,
    camera_pos=(16.0, 15.0, 25.0),
    camera_target=(16.0, 0.0, 16.0),
    bg_color=mcrfpy.Color(40, 60, 100)
)
viewport.enable_fog = True
viewport.fog_near = 10.0
viewport.fog_far = 40.0
viewport.fog_color = mcrfpy.Color(40, 60, 100)
scene.children.append(viewport)

# Set up navigation grid
viewport.set_grid_size(GRID_WIDTH, GRID_DEPTH)

# =============================================================================
# Terrain Generation
# =============================================================================
print("Generating terrain...")

# Create heightmap with hills
hm = mcrfpy.HeightMap((GRID_WIDTH, GRID_DEPTH))
hm.mid_point_displacement(roughness=0.5)
hm.normalize(0.0, 1.0)

# Build terrain mesh
viewport.build_terrain(
    layer_name="terrain",
    heightmap=hm,
    y_scale=TERRAIN_Y_SCALE,
    cell_size=CELL_SIZE
)

# Apply heightmap to navigation grid
viewport.apply_heightmap(hm, TERRAIN_Y_SCALE)

# Mark steep slopes and water as unwalkable
viewport.apply_threshold(hm, 0.0, 0.12, False)  # Low areas = water (unwalkable)
viewport.set_slope_cost(0.4, 2.0)

# Create base terrain colors (green/brown based on height)
r_map = mcrfpy.HeightMap((GRID_WIDTH, GRID_DEPTH))
g_map = mcrfpy.HeightMap((GRID_WIDTH, GRID_DEPTH))
b_map = mcrfpy.HeightMap((GRID_WIDTH, GRID_DEPTH))

# Storage for base colors (for FOV dimming)
base_colors = []

for z in range(GRID_DEPTH):
    row = []
    for x in range(GRID_WIDTH):
        h = hm[x, z]
        if h < 0.12:  # Water
            r, g, b = 0.1, 0.2, 0.4
        elif h < 0.25:  # Sand/beach
            r, g, b = 0.6, 0.5, 0.3
        elif h < 0.6:  # Grass
            r, g, b = 0.2 + random.random() * 0.1, 0.4 + random.random() * 0.15, 0.15
        else:  # Rock/mountain
            r, g, b = 0.4, 0.35, 0.3

        r_map[x, z] = r
        g_map[x, z] = g
        b_map[x, z] = b
        row.append((r, g, b))
    base_colors.append(row)

viewport.apply_terrain_colors("terrain", r_map, g_map, b_map)

# =============================================================================
# Find walkable starting positions
# =============================================================================
def find_walkable_pos():
    """Find a random walkable position"""
    for _ in range(100):
        x = random.randint(2, GRID_WIDTH - 3)
        z = random.randint(2, GRID_DEPTH - 3)
        cell = viewport.at(x, z)
        if cell.walkable:
            return (x, z)
    return (GRID_WIDTH // 2, GRID_DEPTH // 2)

# =============================================================================
# Player Entity
# =============================================================================
player_start = find_walkable_pos()
player = mcrfpy.Entity3D(pos=player_start, scale=0.8, color=mcrfpy.Color(50, 150, 255))
viewport.entities.append(player)
print(f"Player at {player_start}")

# Track discovered cells
discovered = set()
discovered.add(player_start)

# =============================================================================
# NPC Entity with Patrol AI
# =============================================================================
npc_start = find_walkable_pos()
while abs(npc_start[0] - player_start[0]) < 5 and abs(npc_start[1] - player_start[1]) < 5:
    npc_start = find_walkable_pos()

npc = mcrfpy.Entity3D(pos=npc_start, scale=0.7, color=mcrfpy.Color(255, 100, 100))
viewport.entities.append(npc)
print(f"NPC at {npc_start}")

# NPC patrol system
class NPCController:
    def __init__(self, entity, waypoints):
        self.entity = entity
        self.waypoints = waypoints
        self.current_wp = 0
        self.path = []
        self.path_index = 0

    def update(self):
        if self.entity.is_moving:
            return

        # If we have a path, follow it
        if self.path_index < len(self.path):
            next_pos = self.path[self.path_index]
            self.entity.pos = next_pos
            self.path_index += 1
            return

        # Reached waypoint, go to next
        self.current_wp = (self.current_wp + 1) % len(self.waypoints)
        target = self.waypoints[self.current_wp]

        # Compute path to next waypoint
        self.path = self.entity.path_to(target[0], target[1])
        self.path_index = 0

# Create patrol waypoints
npc_waypoints = []
for _ in range(4):
    wp = find_walkable_pos()
    npc_waypoints.append(wp)

npc_controller = NPCController(npc, npc_waypoints)

# =============================================================================
# FOV Visualization
# =============================================================================
def update_fov_colors():
    """Update terrain colors based on FOV"""
    # Compute FOV from player position
    visible_cells = viewport.compute_fov((player.pos[0], player.pos[1]), FOV_RADIUS)
    visible_set = set((c[0], c[1]) for c in visible_cells)

    # Update discovered
    discovered.update(visible_set)

    # Update terrain colors
    r_map = mcrfpy.HeightMap((GRID_WIDTH, GRID_DEPTH))
    g_map = mcrfpy.HeightMap((GRID_WIDTH, GRID_DEPTH))
    b_map = mcrfpy.HeightMap((GRID_WIDTH, GRID_DEPTH))

    for z in range(GRID_DEPTH):
        for x in range(GRID_WIDTH):
            base_r, base_g, base_b = base_colors[z][x]

            if (x, z) in visible_set:
                # Fully visible
                r_map[x, z] = base_r
                g_map[x, z] = base_g
                b_map[x, z] = base_b
            elif (x, z) in discovered:
                # Discovered but not visible - dim
                r_map[x, z] = base_r * 0.4
                g_map[x, z] = base_g * 0.4
                b_map[x, z] = base_b * 0.4
            else:
                # Never seen - very dark
                r_map[x, z] = base_r * 0.1
                g_map[x, z] = base_g * 0.1
                b_map[x, z] = base_b * 0.1

    viewport.apply_terrain_colors("terrain", r_map, g_map, b_map)

# Initial FOV update
update_fov_colors()

# =============================================================================
# UI Overlay
# =============================================================================
ui_frame = mcrfpy.Frame(
    pos=(720, 10),
    size=(260, 200),
    fill_color=mcrfpy.Color(20, 20, 30, 220),
    outline_color=mcrfpy.Color(80, 80, 120),
    outline=2.0
)
scene.children.append(ui_frame)

title_label = mcrfpy.Caption(text="3D Integration Demo", pos=(740, 20))
title_label.fill_color = mcrfpy.Color(255, 255, 150)
scene.children.append(title_label)

status_label = mcrfpy.Caption(text="Status: Idle", pos=(740, 50))
status_label.fill_color = mcrfpy.Color(150, 255, 150)
scene.children.append(status_label)

player_pos_label = mcrfpy.Caption(text="Player: (0, 0)", pos=(740, 75))
player_pos_label.fill_color = mcrfpy.Color(100, 200, 255)
scene.children.append(player_pos_label)

npc_pos_label = mcrfpy.Caption(text="NPC: (0, 0)", pos=(740, 100))
npc_pos_label.fill_color = mcrfpy.Color(255, 150, 150)
scene.children.append(npc_pos_label)

fps_label = mcrfpy.Caption(text="FPS: --", pos=(740, 125))
fps_label.fill_color = mcrfpy.Color(200, 200, 200)
scene.children.append(fps_label)

discovered_label = mcrfpy.Caption(text="Discovered: 0", pos=(740, 150))
discovered_label.fill_color = mcrfpy.Color(180, 180, 100)
scene.children.append(discovered_label)

# Controls info
controls_frame = mcrfpy.Frame(
    pos=(720, 220),
    size=(260, 120),
    fill_color=mcrfpy.Color(20, 20, 30, 200),
    outline_color=mcrfpy.Color(60, 60, 80),
    outline=1.0
)
scene.children.append(controls_frame)

ctrl_title = mcrfpy.Caption(text="Controls:", pos=(740, 230))
ctrl_title.fill_color = mcrfpy.Color(200, 200, 100)
scene.children.append(ctrl_title)

ctrl_lines = [
    "Arrow keys: Move",
    "Click: Pathfind",
    "F: Toggle follow cam",
    "ESC: Quit"
]
for i, line in enumerate(ctrl_lines):
    cap = mcrfpy.Caption(text=line, pos=(740, 255 + i * 20))
    cap.fill_color = mcrfpy.Color(150, 150, 150)
    scene.children.append(cap)

# =============================================================================
# Game State
# =============================================================================
follow_camera = True
frame_count = 0
fps_update_time = 0

# =============================================================================
# Update Function
# =============================================================================
def game_update(timer, runtime):
    global frame_count, fps_update_time

    try:
        # Calculate FPS
        frame_count += 1
        if runtime - fps_update_time >= 1000:  # Update FPS every second
            fps = frame_count
            fps_label.text = f"FPS: {fps}"
            frame_count = 0
            fps_update_time = runtime

        # Update NPC patrol
        npc_controller.update()

        # Update UI labels
        px, pz = player.pos
        player_pos_label.text = f"Player: ({px}, {pz})"
        nx, nz = npc.pos
        npc_pos_label.text = f"NPC: ({nx}, {nz})"
        discovered_label.text = f"Discovered: {len(discovered)}"

        # Camera follow
        if follow_camera:
            viewport.follow(player, distance=12.0, height=8.0, smoothing=0.1)

        # Update status based on player state
        if player.is_moving:
            status_label.text = "Status: Moving"
            status_label.fill_color = mcrfpy.Color(255, 255, 100)
        else:
            status_label.text = "Status: Idle"
            status_label.fill_color = mcrfpy.Color(150, 255, 150)
    except Exception as e:
        print(f"Update error: {e}")

# =============================================================================
# Input Handling
# =============================================================================
def try_move_player(dx, dz):
    """Try to move player in direction"""
    new_x = player.pos[0] + dx
    new_z = player.pos[1] + dz

    if not viewport.is_in_fov(new_x, new_z):
        # Allow moving into discovered cells even if not currently visible
        if (new_x, new_z) not in discovered:
            return False

    if new_x < 0 or new_x >= GRID_WIDTH or new_z < 0 or new_z >= GRID_DEPTH:
        return False

    cell = viewport.at(new_x, new_z)
    if not cell.walkable:
        return False

    player.pos = (new_x, new_z)
    update_fov_colors()
    return True

def on_key(key, state):
    global follow_camera

    if state != mcrfpy.InputState.PRESSED:
        return

    if player.is_moving:
        return  # Don't accept input while moving

    dx, dz = 0, 0
    if key == mcrfpy.Key.UP:
        dz = -1
    elif key == mcrfpy.Key.DOWN:
        dz = 1
    elif key == mcrfpy.Key.LEFT:
        dx = -1
    elif key == mcrfpy.Key.RIGHT:
        dx = 1
    elif key == mcrfpy.Key.F:
        follow_camera = not follow_camera
        status_label.text = f"Camera: {'Follow' if follow_camera else 'Free'}"
        return
    elif key == mcrfpy.Key.ESCAPE:
        mcrfpy.exit()
        return

    if dx != 0 or dz != 0:
        try_move_player(dx, dz)

# Click-to-move handling
def on_click(pos, button, state):
    if button != mcrfpy.MouseButton.LEFT or state != mcrfpy.InputState.PRESSED:
        return

    if player.is_moving:
        return

    # Convert click position to viewport-relative coordinates
    vp_x = pos.x - viewport.x
    vp_y = pos.y - viewport.y

    # Check if click is within viewport
    if vp_x < 0 or vp_x >= viewport.w or vp_y < 0 or vp_y >= viewport.h:
        return

    # Convert to world position
    world_pos = viewport.screen_to_world(vp_x, vp_y)
    if world_pos is None:
        return

    # Convert to grid position
    grid_x = int(world_pos[0] / CELL_SIZE)
    grid_z = int(world_pos[2] / CELL_SIZE)

    # Validate grid position
    if grid_x < 0 or grid_x >= GRID_WIDTH or grid_z < 0 or grid_z >= GRID_DEPTH:
        return

    cell = viewport.at(grid_x, grid_z)
    if not cell.walkable:
        status_label.text = "Status: Can't walk there!"
        status_label.fill_color = mcrfpy.Color(255, 100, 100)
        return

    # Find path
    path = player.path_to(grid_x, grid_z)
    if not path:
        status_label.text = "Status: No path!"
        status_label.fill_color = mcrfpy.Color(255, 100, 100)
        return

    # Follow path (limited to FOV_RADIUS steps)
    limited_path = path[:FOV_RADIUS]
    player.follow_path(limited_path)
    status_label.text = f"Status: Moving ({len(limited_path)} steps)"
    status_label.fill_color = mcrfpy.Color(255, 255, 100)

    # Schedule FOV update after movement completes
    fov_update_timer = None

    def update_fov_after_move(*args):
        # Accept any number of args since timer may pass (runtime) or (timer, runtime)
        nonlocal fov_update_timer
        if not player.is_moving:
            update_fov_colors()
            if fov_update_timer:
                fov_update_timer.stop()

    fov_update_timer = mcrfpy.Timer("fov_update", update_fov_after_move, 100)

scene.on_key = on_key
viewport.on_click = on_click

# =============================================================================
# Start Game
# =============================================================================
timer = mcrfpy.Timer("game_update", game_update, 16)  # ~60 FPS

mcrfpy.current_scene = scene

print()
print("=" * 60)
print("3D Integration Demo Loaded!")
print("=" * 60)
print(f"  Terrain: {GRID_WIDTH}x{GRID_DEPTH} cells")
print(f"  Player starts at: {player_start}")
print(f"  NPC patrolling {len(npc_waypoints)} waypoints")
print()
print("Controls:")
print("  Arrow keys: Move player")
print("  Click: Pathfind to location")
print("  F: Toggle camera follow")
print("  ESC: Quit")
print("=" * 60)
