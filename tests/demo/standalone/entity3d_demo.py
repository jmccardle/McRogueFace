# entity3d_demo.py - Visual demo of Entity3D 3D game entities
# Shows entities moving on a terrain grid with pathfinding and FOV

import mcrfpy
import sys
import math

# Create demo scene
scene = mcrfpy.Scene("entity3d_demo")

# Dark background frame
bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(15, 15, 25))
scene.children.append(bg)

# Title
title = mcrfpy.Caption(text="Entity3D Demo - 3D Entities on Navigation Grid", pos=(20, 10))
title.fill_color = mcrfpy.Color(255, 255, 255)
scene.children.append(title)

# Create the 3D viewport
viewport = mcrfpy.Viewport3D(
    pos=(50, 60),
    size=(600, 450),
    render_resolution=(320, 240),  # PS1 resolution
    fov=60.0,
    camera_pos=(16.0, 12.0, 24.0),
    camera_target=(8.0, 0.0, 8.0),
    bg_color=mcrfpy.Color(50, 70, 100)  # Twilight background
)
scene.children.append(viewport)

# Set up the navigation grid (16x16 for this demo)
GRID_SIZE = 16
viewport.set_grid_size(GRID_SIZE, GRID_SIZE)

# Generate simple terrain using HeightMap
print("Generating terrain...")
hm = mcrfpy.HeightMap((GRID_SIZE, GRID_SIZE))

# Create a gentle rolling terrain
hm.mid_point_displacement(0.3, seed=123)  # Low roughness for gentle hills
hm.normalize(0.0, 1.0)

# Apply heightmap to navigation grid
viewport.apply_heightmap(hm, 3.0)  # y_scale = 3.0 for moderate elevation changes

# Build terrain mesh
vertex_count = viewport.build_terrain(
    layer_name="terrain",
    heightmap=hm,
    y_scale=3.0,
    cell_size=1.0
)
print(f"Terrain built with {vertex_count} vertices")

# Create terrain colors (grass-like green with some variation)
r_map = mcrfpy.HeightMap((GRID_SIZE, GRID_SIZE))
g_map = mcrfpy.HeightMap((GRID_SIZE, GRID_SIZE))
b_map = mcrfpy.HeightMap((GRID_SIZE, GRID_SIZE))

for y in range(GRID_SIZE):
    for x in range(GRID_SIZE):
        h = hm[x, y]
        # Green grass with height-based variation
        r_map[x, y] = 0.2 + h * 0.2
        g_map[x, y] = 0.4 + h * 0.3  # More green on higher ground
        b_map[x, y] = 0.15 + h * 0.1

viewport.apply_terrain_colors("terrain", r_map, g_map, b_map)

# Create entities
print("Creating entities...")

# Player entity (bright yellow/orange)
player = mcrfpy.Entity3D(
    pos=(8, 8),
    rotation=0.0,
    scale=0.8,
    color=mcrfpy.Color(255, 200, 50)
)
viewport.entities.append(player)

# NPC entities (different colors)
npc_colors = [
    mcrfpy.Color(50, 150, 255),   # Blue
    mcrfpy.Color(255, 80, 80),    # Red
    mcrfpy.Color(80, 255, 80),    # Green
    mcrfpy.Color(200, 80, 200),   # Purple
]

npcs = []
npc_positions = [(2, 2), (14, 2), (2, 14), (14, 14)]
for i, (x, z) in enumerate(npc_positions):
    npc = mcrfpy.Entity3D(
        pos=(x, z),
        rotation=45.0 * i,
        scale=0.6,
        color=npc_colors[i]
    )
    viewport.entities.append(npc)
    npcs.append(npc)

print(f"Created {len(viewport.entities)} entities")

# Info panel on the right
info_panel = mcrfpy.Frame(pos=(670, 60), size=(330, 450),
                          fill_color=mcrfpy.Color(30, 30, 40),
                          outline_color=mcrfpy.Color(80, 80, 100),
                          outline=2.0)
scene.children.append(info_panel)

# Panel title
panel_title = mcrfpy.Caption(text="Entity3D Properties", pos=(690, 70))
panel_title.fill_color = mcrfpy.Color(200, 200, 255)
scene.children.append(panel_title)

# Dynamic property displays
pos_label = mcrfpy.Caption(text="Player Pos: (8, 8)", pos=(690, 100))
pos_label.fill_color = mcrfpy.Color(180, 180, 200)
scene.children.append(pos_label)

world_pos_label = mcrfpy.Caption(text="World Pos: (8.5, ?, 8.5)", pos=(690, 125))
world_pos_label.fill_color = mcrfpy.Color(180, 180, 200)
scene.children.append(world_pos_label)

entity_count_label = mcrfpy.Caption(text=f"Entities: {len(viewport.entities)}", pos=(690, 150))
entity_count_label.fill_color = mcrfpy.Color(180, 180, 200)
scene.children.append(entity_count_label)

# Static properties
props = [
    ("", ""),
    ("Grid Size:", f"{GRID_SIZE}x{GRID_SIZE}"),
    ("Cell Size:", "1.0"),
    ("Y Scale:", "3.0"),
    ("", ""),
    ("Entity Features:", ""),
    ("  - Grid position (x, z)", ""),
    ("  - Smooth movement", ""),
    ("  - Height from terrain", ""),
    ("  - Per-entity color", ""),
]

y_offset = 180
for label, value in props:
    if label:
        cap = mcrfpy.Caption(text=f"{label} {value}", pos=(690, y_offset))
        cap.fill_color = mcrfpy.Color(150, 150, 170)
        scene.children.append(cap)
    y_offset += 22

# Instructions at bottom
instructions = mcrfpy.Caption(
    text="[WASD] Move player | [Q/E] Rotate | [Space] Orbit | [N] NPC wander | [ESC] Quit",
    pos=(20, 530)
)
instructions.fill_color = mcrfpy.Color(150, 150, 150)
scene.children.append(instructions)

# Status line
status = mcrfpy.Caption(text="Status: Use WASD to move the yellow player entity", pos=(20, 555))
status.fill_color = mcrfpy.Color(100, 200, 100)
scene.children.append(status)

# Animation state
animation_time = [0.0]
camera_orbit = [False]
npc_wander = [False]

# Update function - called each frame
def update(timer, runtime):
    animation_time[0] += runtime / 1000.0

    # Update position labels
    px, pz = player.pos
    pos_label.text = f"Player Pos: ({px}, {pz})"

    wp = player.world_pos
    world_pos_label.text = f"World Pos: ({wp[0]:.1f}, {wp[1]:.1f}, {wp[2]:.1f})"

    # Camera orbit
    if camera_orbit[0]:
        angle = animation_time[0] * 0.5
        radius = 20.0
        center_x = 8.0
        center_z = 8.0
        height = 12.0 + math.sin(animation_time[0] * 0.3) * 3.0

        x = center_x + math.cos(angle) * radius
        z = center_z + math.sin(angle) * radius

        viewport.camera_pos = (x, height, z)
        viewport.camera_target = (center_x, 2.0, center_z)
    else:
        # Follow player (smoothly)
        px, pz = player.pos
        target_x = px + 0.5  # Center of cell
        target_z = pz + 0.5

        # Look at player from behind and above
        cam_x = target_x
        cam_z = target_z + 12.0
        cam_y = 10.0

        viewport.camera_pos = (cam_x, cam_y, cam_z)
        viewport.camera_target = (target_x, 1.0, target_z)

    # NPC wandering
    if npc_wander[0]:
        for i, npc in enumerate(npcs):
            # Each NPC rotates slowly
            npc.rotation = (npc.rotation + 1.0 + i * 0.5) % 360.0

# Key handler
def on_key(key, state):
    if state != mcrfpy.InputState.PRESSED:
        return

    px, pz = player.pos

    # Player movement with WASD
    if key == mcrfpy.Key.W:
        new_z = max(0, pz - 1)
        player.teleport(px, new_z)
        player.rotation = 0.0
        status.text = f"Moved north to ({px}, {new_z})"
    elif key == mcrfpy.Key.S:
        new_z = min(GRID_SIZE - 1, pz + 1)
        player.teleport(px, new_z)
        player.rotation = 180.0
        status.text = f"Moved south to ({px}, {new_z})"
    elif key == mcrfpy.Key.A:
        new_x = max(0, px - 1)
        player.teleport(new_x, pz)
        player.rotation = 270.0
        status.text = f"Moved west to ({new_x}, {pz})"
    elif key == mcrfpy.Key.D:
        new_x = min(GRID_SIZE - 1, px + 1)
        player.teleport(new_x, pz)
        player.rotation = 90.0
        status.text = f"Moved east to ({new_x}, {pz})"

    # Rotation with Q/E
    elif key == mcrfpy.Key.Q:
        player.rotation = (player.rotation - 15.0) % 360.0
        status.text = f"Rotated to {player.rotation:.1f} degrees"
    elif key == mcrfpy.Key.E:
        player.rotation = (player.rotation + 15.0) % 360.0
        status.text = f"Rotated to {player.rotation:.1f} degrees"

    # Toggle camera orbit
    elif key == mcrfpy.Key.SPACE:
        camera_orbit[0] = not camera_orbit[0]
        status.text = f"Camera orbit: {'ON' if camera_orbit[0] else 'OFF (following player)'}"

    # Toggle NPC wandering
    elif key == mcrfpy.Key.N:
        npc_wander[0] = not npc_wander[0]
        status.text = f"NPC wandering: {'ON' if npc_wander[0] else 'OFF'}"

    # Entity visibility toggle
    elif key == mcrfpy.Key.V:
        for npc in npcs:
            npc.visible = not npc.visible
        status.text = f"NPCs visible: {npcs[0].visible}"

    # Scale adjustment
    elif key == mcrfpy.Key.EQUAL:  # +
        player.scale = min(2.0, player.scale + 0.1)
        status.text = f"Player scale: {player.scale:.1f}"
    elif key == mcrfpy.Key.HYPHEN:  # -
        player.scale = max(0.3, player.scale - 0.1)
        status.text = f"Player scale: {player.scale:.1f}"

    elif key == mcrfpy.Key.ESCAPE:
        mcrfpy.exit()

# Set up scene
scene.on_key = on_key

# Create timer for updates
timer = mcrfpy.Timer("entity_update", update, 16)  # ~60fps

# Activate scene
mcrfpy.current_scene = scene

print()
print("Entity3D Demo loaded!")
print(f"Created {len(viewport.entities)} entities on a {GRID_SIZE}x{GRID_SIZE} grid.")
print()
print("Controls:")
print("  [WASD] Move player")
print("  [Q/E] Rotate player")
print("  [Space] Toggle camera orbit")
print("  [N] Toggle NPC rotation")
print("  [V] Toggle NPC visibility")
print("  [+/-] Scale player")
print("  [ESC] Quit")
