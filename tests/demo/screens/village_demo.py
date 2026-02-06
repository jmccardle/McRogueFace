# village_demo.py - 3D Village Integration Demo
# Capstone demo combining: heightmap terrain + voxel buildings + animated entities
# + click-to-move pathfinding + FOV + camera follow + roof toggle
#
# Demonstrates all 3D milestones (9-14) working together in one scene.

import mcrfpy
import sys
import math

# ===========================================================================
# Constants
# ===========================================================================
GRID_W, GRID_D = 48, 36
Y_SCALE = 6.0
CELL_SIZE = 1.0

# Building definitions: (name, voxel_size, grid_pos, rotation, palette)
BUILDINGS = [
    {
        "name": "Stone House",
        "size": (8, 5, 8),
        "grid_pos": (10, 10),   # (x, z) on nav grid
        "rotation": 0.0,
        "wall_color": (120, 120, 130),
        "floor_color": (100, 80, 60),
        "roof_color": (140, 60, 40),
        "door_wall": "south",   # which wall gets a doorway
    },
    {
        "name": "Wooden Lodge",
        "size": (10, 6, 8),
        "grid_pos": (30, 8),
        "rotation": 0.0,
        "wall_color": (130, 90, 50),
        "floor_color": (90, 70, 45),
        "roof_color": (80, 55, 30),
        "door_wall": "south",
    },
    {
        "name": "Guard Tower",
        "size": (7, 10, 7),
        "grid_pos": (22, 26),
        "rotation": 0.0,
        "wall_color": (90, 90, 100),
        "floor_color": (70, 65, 60),
        "roof_color": (60, 60, 70),
        "door_wall": "south",
    },
]

# ===========================================================================
# Scene setup
# ===========================================================================
scene = mcrfpy.Scene("village_demo")

bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(15, 15, 25))
scene.children.append(bg)

title = mcrfpy.Caption(text="3D Village Demo", pos=(20, 8))
title.fill_color = mcrfpy.Color(255, 255, 100)
scene.children.append(title)

subtitle = mcrfpy.Caption(text="Terrain + Voxel Buildings + Pathfinding + FOV + Animation", pos=(20, 28))
subtitle.fill_color = mcrfpy.Color(180, 180, 200)
scene.children.append(subtitle)

# ===========================================================================
# Viewport3D
# ===========================================================================
viewport = mcrfpy.Viewport3D(
    pos=(10, 50),
    size=(700, 500),
    render_resolution=(350, 250),
    fov=60.0,
    camera_pos=(24.0, 20.0, 45.0),
    camera_target=(24.0, 0.0, 18.0),
    bg_color=mcrfpy.Color(120, 170, 220)
)
scene.children.append(viewport)
viewport.set_grid_size(GRID_W, GRID_D)
viewport.cell_size = CELL_SIZE

# ===========================================================================
# Phase B1: Terrain generation
# ===========================================================================
print("Generating terrain...")
hm = mcrfpy.HeightMap((GRID_W, GRID_D))
hm.mid_point_displacement(0.45, seed=12345)
hm.normalize(0.0, 1.0)
hm.rain_erosion(drops=2000, erosion=0.06, sedimentation=0.03, seed=54321)
hm.normalize(0.0, 1.0)

# Add hills at strategic locations (away from buildings)
# hm.add_hill() - check if it exists; if not, manually raise areas
# For now, manually raise a few areas
for x in range(3, 8):
    for z in range(25, 32):
        cx, cz = 5.5, 28.5
        dist = math.sqrt((x - cx)**2 + (z - cz)**2)
        if dist < 4.0:
            bump = 0.3 * (1.0 - dist / 4.0)
            hm[x, z] = min(1.0, hm[x, z] + bump)

for x in range(38, 46):
    for z in range(20, 28):
        cx, cz = 42.0, 24.0
        dist = math.sqrt((x - cx)**2 + (z - cz)**2)
        if dist < 5.0:
            bump = 0.25 * (1.0 - dist / 5.0)
            hm[x, z] = min(1.0, hm[x, z] + bump)

# Flatten building zones (set to a constant moderate height)
FLAT_HEIGHT = 0.35
for bldg in BUILDINGS:
    bx, bz = bldg["grid_pos"]
    bw = bldg["size"][0]
    bd = bldg["size"][2]
    # Flatten a zone slightly larger than the building footprint
    for x in range(max(0, bx - 1), min(GRID_W, bx + bw + 1)):
        for z in range(max(0, bz - 1), min(GRID_D, bz + bd + 1)):
            hm[x, z] = FLAT_HEIGHT

hm.normalize(0.0, 1.0)  # Re-normalize after modifications

# Build terrain mesh
vertex_count = viewport.build_terrain(
    layer_name="terrain",
    heightmap=hm,
    y_scale=Y_SCALE,
    cell_size=CELL_SIZE
)
print(f"Terrain: {vertex_count} vertices")

# Apply heightmap to navigation grid
viewport.apply_heightmap(hm, Y_SCALE)

# Color the terrain based on height + moisture
moisture = mcrfpy.HeightMap((GRID_W, GRID_D))
moisture.mid_point_displacement(0.6, seed=7777)
moisture.normalize(0.0, 1.0)

r_map = mcrfpy.HeightMap((GRID_W, GRID_D))
g_map = mcrfpy.HeightMap((GRID_W, GRID_D))
b_map = mcrfpy.HeightMap((GRID_W, GRID_D))

for z in range(GRID_D):
    for x in range(GRID_W):
        h = hm[x, z]
        m = moisture[x, z]

        if h < 0.15:  # Water
            r_map[x, z] = 0.15
            g_map[x, z] = 0.3
            b_map[x, z] = 0.65
        elif h < 0.25:  # Sand / shore
            r_map[x, z] = 0.75
            g_map[x, z] = 0.7
            b_map[x, z] = 0.45
        elif h < 0.6:  # Grass / dirt
            if m > 0.45:
                # Lush grass
                r_map[x, z] = 0.2 + h * 0.15
                g_map[x, z] = 0.45 + m * 0.2
                b_map[x, z] = 0.1
            else:
                # Dry grass / dirt
                r_map[x, z] = 0.45
                g_map[x, z] = 0.38
                b_map[x, z] = 0.18
        elif h < 0.8:  # Rock
            r_map[x, z] = 0.42
            g_map[x, z] = 0.4
            b_map[x, z] = 0.38
        else:  # Snow / high peaks
            r_map[x, z] = 0.9
            g_map[x, z] = 0.9
            b_map[x, z] = 0.95

viewport.apply_terrain_colors("terrain", r_map, g_map, b_map)

# Mark water as unwalkable
viewport.apply_threshold(hm, 0.0, 0.15, False)

# Mark steep areas as costly
viewport.set_slope_cost(0.3, 3.0)

print("Terrain colored and nav grid configured")

# ===========================================================================
# Phase B2: Voxel Buildings
# ===========================================================================
print("Building voxel structures...")

building_data = []  # Store (body, roof, footprint) for each building

for bldg in BUILDINGS:
    bw, bh, bd = bldg["size"]
    gx, gz = bldg["grid_pos"]

    # Get terrain height at building center
    terrain_y = hm[gx + bw // 2, gz + bd // 2] * Y_SCALE

    # --- Body VoxelGrid (floor + walls with doorway) ---
    body = mcrfpy.VoxelGrid((bw, bh, bd), cell_size=CELL_SIZE)
    floor_mat = body.add_material("floor", bldg["floor_color"])
    wall_mat = body.add_material("wall", bldg["wall_color"], transparent=False)
    window_mat = body.add_material("window", (180, 210, 240), transparent=True)

    # Floor
    body.fill_box((0, 0, 0), (bw - 1, 0, bd - 1), floor_mat)

    # Walls (hollow box from y=1 to y=bh-2, leaving top for roof)
    body.fill_box_hollow((0, 1, 0), (bw - 1, bh - 2, bd - 1), wall_mat)

    # Doorway (south wall = z=0 face, centered)
    door_cx = bw // 2
    if bldg["door_wall"] == "south":
        body.fill_box((door_cx - 1, 1, 0), (door_cx, 2, 0), 0)  # 2-wide, 2-tall door
    elif bldg["door_wall"] == "north":
        body.fill_box((door_cx - 1, 1, bd - 1), (door_cx, 2, bd - 1), 0)

    # Windows (east wall, if building is large enough)
    if bw >= 7:
        win_cx = bw - 1
        win_cz = bd // 2
        body.fill_box((win_cx, 2, win_cz - 1), (win_cx, 3, win_cz), window_mat)

    # Windows (west wall)
    if bw >= 7:
        win_cz2 = bd // 2
        body.fill_box((0, 2, win_cz2 - 1), (0, 3, win_cz2), window_mat)

    # Position the body in world space
    body.offset = (float(gx), terrain_y, float(gz))
    body.rotation = bldg["rotation"]
    body.greedy_meshing = True

    # --- Roof VoxelGrid (single slab at top) ---
    roof = mcrfpy.VoxelGrid((bw + 2, 1, bd + 2), cell_size=CELL_SIZE)
    roof_mat = roof.add_material("roof", bldg["roof_color"])
    roof.fill_box((0, 0, 0), (bw + 1, 0, bd + 1), roof_mat)
    roof.offset = (float(gx - 1), terrain_y + (bh - 1) * CELL_SIZE, float(gz - 1))
    roof.rotation = bldg["rotation"]
    roof.greedy_meshing = True

    # Add to viewport
    viewport.add_voxel_layer(body, z_index=1)
    viewport.add_voxel_layer(roof, z_index=2)

    # Project body to nav grid (walls block movement)
    viewport.project_voxel_to_nav(body, headroom=2)

    building_data.append({
        "name": bldg["name"],
        "body": body,
        "roof": roof,
        "footprint": (gx, gz, bw, bd),
        "terrain_y": terrain_y,
    })
    print(f"  {bldg['name']}: {bw}x{bh}x{bd} at ({gx},{gz}), y={terrain_y:.1f}")

print(f"Built {len(building_data)} buildings")

# ===========================================================================
# Phase B3: Player Entity
# ===========================================================================
print("Setting up player...")

# Start player near the first building's door
start_x, start_z = BUILDINGS[0]["grid_pos"][0] + BUILDINGS[0]["size"][0] // 2, BUILDINGS[0]["grid_pos"][1] - 2

player = mcrfpy.Entity3D(
    pos=(start_x, start_z),
    scale=1.0,
    color=mcrfpy.Color(100, 200, 255)
)

# Try to load animated model
try:
    player_model = mcrfpy.Model3D("../assets/models/CesiumMan.glb")
    if player_model.has_skeleton:
        player.model = player_model
        clips = player_model.animation_clips
        if clips:
            player.anim_clip = clips[0]
            player.anim_loop = True
            player.anim_speed = 1.0
            player.auto_animate = True
            # CesiumMan has a single clip - use it for both walk and idle
            player.walk_clip = clips[0]
            player.idle_clip = clips[0]
            print(f"  Player model loaded with {len(clips)} clip(s): {clips}")
    else:
        print("  Player model loaded (no skeleton)")
except Exception as e:
    print(f"  Could not load player model: {e}")

viewport.entities.append(player)

# ===========================================================================
# Phase B3 continued: NPCs
# ===========================================================================
print("Setting up NPCs...")

class NPCController:
    """Simple patrol NPC that walks between waypoints"""
    def __init__(self, entity, waypoints, name="NPC"):
        self.entity = entity
        self.waypoints = waypoints
        self.current_wp = 0
        self.name = name
        self.waiting = False

    def update(self):
        if self.entity.is_moving:
            return

        # Move to next waypoint
        self.current_wp = (self.current_wp + 1) % len(self.waypoints)
        wx, wz = self.waypoints[self.current_wp]

        path = self.entity.path_to(wx, wz)
        if path and len(path) > 0:
            self.entity.follow_path(path)

npcs = []

# NPC 1: Guard patrolling between buildings
npc1 = mcrfpy.Entity3D(
    pos=(15, 14),
    scale=0.9,
    color=mcrfpy.Color(255, 150, 80)
)
try:
    npc1_model = mcrfpy.Model3D("../assets/models/CesiumMan.glb")
    if npc1_model.has_skeleton:
        npc1.model = npc1_model
        clips = npc1_model.animation_clips
        if clips:
            npc1.anim_clip = clips[0]
            npc1.anim_loop = True
            npc1.auto_animate = True
            npc1.walk_clip = clips[0]
            npc1.idle_clip = clips[0]
except Exception:
    pass
viewport.entities.append(npc1)
npc1_ctrl = NPCController(npc1, [
    (15, 14), (28, 12), (35, 15), (28, 22), (15, 20)
], name="Guard")
npcs.append(npc1_ctrl)

# NPC 2: Villager near the lodge
npc2 = mcrfpy.Entity3D(
    pos=(32, 18),
    scale=0.85,
    color=mcrfpy.Color(180, 255, 150)
)
try:
    npc2_model = mcrfpy.Model3D("../assets/models/CesiumMan.glb")
    if npc2_model.has_skeleton:
        npc2.model = npc2_model
        clips = npc2_model.animation_clips
        if clips:
            npc2.anim_clip = clips[0]
            npc2.anim_loop = True
            npc2.auto_animate = True
            npc2.walk_clip = clips[0]
            npc2.idle_clip = clips[0]
except Exception:
    pass
viewport.entities.append(npc2)
npc2_ctrl = NPCController(npc2, [
    (32, 18), (35, 12), (38, 18), (35, 24)
], name="Villager")
npcs.append(npc2_ctrl)

print(f"  {len(npcs)} NPCs created")

# ===========================================================================
# Phase B5: Roof toggle tracking
# ===========================================================================
player_inside = [None]  # Which building the player is inside (or None)

def check_building_interior(px, pz):
    """Check if player position is inside any building footprint"""
    for bd in building_data:
        gx, gz, bw, bdepth = bd["footprint"]
        if gx <= px < gx + bw and gz <= pz < gz + bdepth:
            return bd
    return None

def update_roof_visibility(building_match):
    """Toggle roof visibility based on player position"""
    old = player_inside[0]
    if building_match is old:
        return  # No change

    # Restore old building's roof
    if old is not None:
        old["roof"].visible = True

    # Hide new building's roof
    if building_match is not None:
        building_match["roof"].visible = False

    player_inside[0] = building_match

# ===========================================================================
# Phase B6: Camera + FOV
# ===========================================================================
# Initial FOV
fov_radius = 12
fov_visible = []

# FOV state: discovered cells persist
discovered = set()

def update_fov():
    """Recompute FOV from player position"""
    global fov_visible
    px, pz = player.pos
    px, pz = int(px), int(pz)
    fov_visible = viewport.compute_fov((px, pz), fov_radius)

    # Mark cells as discovered
    for cell_pos in fov_visible:
        discovered.add((cell_pos[0], cell_pos[1]))

# Initial FOV computation
update_fov()

# Set up camera follow
viewport.follow(player, distance=14.0, height=10.0, smoothing=0.08)

# ===========================================================================
# Phase B4: Click-to-move handler
# ===========================================================================
def on_viewport_click(pos, button, action):
    """Handle click on viewport for movement"""
    if action != mcrfpy.InputState.PRESSED:
        return
    if button != mcrfpy.MouseButton.LEFT:
        return

    # pos is absolute screen coords; convert to viewport-relative
    # screen_to_world expects display pixel coords, NOT render resolution
    local_x = pos.x - viewport.x
    local_y = pos.y - viewport.y

    result = viewport.screen_to_world(local_x, local_y)

    # Update debug label
    if result is not None:
        debug_label.text = (
            f"mouse=({pos.x:.0f},{pos.y:.0f}) "
            f"local=({local_x:.0f},{local_y:.0f}) "
            f"world=({result[0]:.1f},{result[1]:.1f},{result[2]:.1f}) "
            f"grid=({int(result[0])},{int(result[2])})"
        )
    else:
        debug_label.text = (
            f"mouse=({pos.x:.0f},{pos.y:.0f}) "
            f"local=({local_x:.0f},{local_y:.0f}) "
            f"world=None"
        )
        return

    # Convert world position to grid coordinates
    target_gx = int(result[0])
    target_gz = int(result[2])

    # Clamp to grid bounds
    target_gx = max(0, min(GRID_W - 1, target_gx))
    target_gz = max(0, min(GRID_D - 1, target_gz))

    # Check if target is walkable
    cell = viewport.at(target_gx, target_gz)
    if not cell.walkable:
        status_text.text = f"Can't walk to ({target_gx}, {target_gz}) - blocked! h={cell.height:.1f}"
        return

    # Pathfind and move
    px, pz = player.pos
    path = player.path_to(target_gx, target_gz)
    if path and len(path) > 0:
        player.follow_path(path)
        status_text.text = f"({int(px)},{int(pz)})->({target_gx},{target_gz}), {len(path)} steps"
    else:
        status_text.text = f"No path from ({int(px)},{int(pz)}) to ({target_gx},{target_gz})"

viewport.on_click = on_viewport_click

# ===========================================================================
# Keyboard handler (arrow keys for step movement)
# ===========================================================================
def on_key(key, state):
    if state != mcrfpy.InputState.PRESSED:
        return

    px, pz = player.pos
    px, pz = int(px), int(pz)
    moved = False

    if key == mcrfpy.Key.UP or key == mcrfpy.Key.W:
        target = (px, pz - 1)
        moved = True
    elif key == mcrfpy.Key.DOWN or key == mcrfpy.Key.S:
        target = (px, pz + 1)
        moved = True
    elif key == mcrfpy.Key.LEFT or key == mcrfpy.Key.A:
        target = (px - 1, pz)
        moved = True
    elif key == mcrfpy.Key.RIGHT or key == mcrfpy.Key.D:
        target = (px + 1, pz)
        moved = True
    elif key == mcrfpy.Key.ESCAPE:
        mcrfpy.exit()
        return
    elif key == mcrfpy.Key.F:
        # Toggle FOV visualization
        update_fov()
        status_text.text = f"FOV recomputed: {len(fov_visible)} visible cells"
        return

    if moved:
        tx, tz = target
        if 0 <= tx < GRID_W and 0 <= tz < GRID_D:
            cell = viewport.at(tx, tz)
            if cell.walkable:
                path = player.path_to(tx, tz)
                if path:
                    player.follow_path(path)

scene.on_key = on_key

# ===========================================================================
# Phase B7: UI Overlay
# ===========================================================================
# Info panel
info_panel = mcrfpy.Frame(
    pos=(720, 50), size=(290, 320),
    fill_color=mcrfpy.Color(25, 25, 35, 220),
    outline_color=mcrfpy.Color(80, 80, 100),
    outline=2.0
)
scene.children.append(info_panel)

info_title = mcrfpy.Caption(text="Village Info", pos=(10, 8))
info_title.fill_color = mcrfpy.Color(255, 255, 100)
info_panel.children.append(info_title)

pos_label = mcrfpy.Caption(text="Player: (?, ?)", pos=(10, 35))
pos_label.fill_color = mcrfpy.Color(180, 220, 255)
info_panel.children.append(pos_label)

building_label = mcrfpy.Caption(text="Location: Outside", pos=(10, 55))
building_label.fill_color = mcrfpy.Color(200, 200, 150)
info_panel.children.append(building_label)

entity_label = mcrfpy.Caption(text=f"Entities: {len(npcs) + 1}", pos=(10, 75))
entity_label.fill_color = mcrfpy.Color(180, 200, 180)
info_panel.children.append(entity_label)

fov_label = mcrfpy.Caption(text="FOV: ? cells", pos=(10, 95))
fov_label.fill_color = mcrfpy.Color(200, 180, 255)
info_panel.children.append(fov_label)

terrain_label = mcrfpy.Caption(text=f"Terrain: {GRID_W}x{GRID_D}, {vertex_count} verts", pos=(10, 115))
terrain_label.fill_color = mcrfpy.Color(150, 180, 150)
info_panel.children.append(terrain_label)

buildings_label = mcrfpy.Caption(text=f"Buildings: {len(building_data)}", pos=(10, 135))
buildings_label.fill_color = mcrfpy.Color(180, 150, 150)
info_panel.children.append(buildings_label)

# Building list
for i, bd in enumerate(building_data):
    bl = mcrfpy.Caption(text=f"  {bd['name']}", pos=(10, 155 + i * 18))
    bl.fill_color = mcrfpy.Color(150, 150, 170)
    info_panel.children.append(bl)

# Controls panel
controls_panel = mcrfpy.Frame(
    pos=(720, 380), size=(290, 170),
    fill_color=mcrfpy.Color(25, 25, 35, 220),
    outline_color=mcrfpy.Color(80, 80, 100),
    outline=2.0
)
scene.children.append(controls_panel)

ctrl_title = mcrfpy.Caption(text="Controls", pos=(10, 8))
ctrl_title.fill_color = mcrfpy.Color(255, 255, 100)
controls_panel.children.append(ctrl_title)

controls = [
    "Click viewport: Move player",
    "WASD/Arrows: Step movement",
    "F: Recompute FOV",
    "ESC: Quit",
    "",
    "Roofs hide when you enter",
    "a building!",
]
for i, line in enumerate(controls):
    cl = mcrfpy.Caption(text=line, pos=(10, 32 + i * 18))
    cl.fill_color = mcrfpy.Color(160, 160, 180)
    controls_panel.children.append(cl)

# Status bar
status_frame = mcrfpy.Frame(
    pos=(10, 560), size=(700, 30),
    fill_color=mcrfpy.Color(20, 20, 30, 220),
    outline_color=mcrfpy.Color(60, 60, 80),
    outline=1.0
)
scene.children.append(status_frame)

status_text = mcrfpy.Caption(text="Click the terrain to move. Enter buildings to see roofs toggle.", pos=(10, 6))
status_text.fill_color = mcrfpy.Color(150, 200, 150)
status_frame.children.append(status_text)

# Debug label for click coordinates
debug_frame = mcrfpy.Frame(
    pos=(10, 595), size=(700, 25),
    fill_color=mcrfpy.Color(30, 15, 15, 200),
    outline_color=mcrfpy.Color(80, 40, 40),
    outline=1.0
)
scene.children.append(debug_frame)

debug_label = mcrfpy.Caption(text="Click debug: (click viewport to see coordinates)", pos=(10, 4))
debug_label.fill_color = mcrfpy.Color(255, 180, 120)
debug_frame.children.append(debug_label)

# ===========================================================================
# Phase B8: Billboards (trees)
# ===========================================================================
# Note: Billboards require a texture. Check if kenney spritesheet works.
# For now, skip billboards if no suitable texture is available.
# Trees can be added once billboard texture support is confirmed.

# ===========================================================================
# Game update loop
# ===========================================================================
frame_count = [0]

def game_update(timer, runtime):
    frame_count[0] += 1

    # Update NPC patrol
    for npc_ctrl in npcs:
        npc_ctrl.update()

    # Update player info
    px, pz = player.pos
    pos_label.text = f"Player: ({int(px)}, {int(pz)})"

    # Check building interior
    building_match = check_building_interior(int(px), int(pz))
    update_roof_visibility(building_match)

    if building_match is not None:
        building_label.text = f"Location: {building_match['name']}"
    else:
        building_label.text = "Location: Outside"

    # Update FOV periodically (every 30 frames to save CPU)
    if frame_count[0] % 30 == 0:
        update_fov()
        fov_label.text = f"FOV: {len(fov_visible)} cells, {len(discovered)} discovered"

# Timer: ~60fps game update
game_timer = mcrfpy.Timer("village_update", game_update, 16)

# ===========================================================================
# Activate scene
# ===========================================================================
mcrfpy.current_scene = scene

print()
print("=== 3D Village Demo ===")
print(f"Terrain: {GRID_W}x{GRID_D} heightmap, {vertex_count} terrain vertices")
print(f"Buildings: {len(building_data)} voxel structures with toggleable roofs")
print(f"Entities: 1 player + {len(npcs)} NPCs with pathfinding")
print("Click terrain to move, enter buildings to see roof toggle!")
print()
