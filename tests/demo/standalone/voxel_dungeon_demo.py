# voxel_dungeon_demo.py - Procedural dungeon demonstrating bulk voxel operations
# Milestone 11: Bulk Operations and Building Primitives

import mcrfpy
import sys
import math
import random

# Create demo scene
scene = mcrfpy.Scene("voxel_dungeon_demo")

# Dark background
bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(20, 20, 30))
scene.children.append(bg)

# Title
title = mcrfpy.Caption(text="Voxel Dungeon Demo - Bulk Operations (Milestone 11)", pos=(20, 10))
title.fill_color = mcrfpy.Color(255, 255, 255)
scene.children.append(title)

# Create the 3D viewport
viewport = mcrfpy.Viewport3D(
    pos=(50, 60),
    size=(620, 520),
    render_resolution=(400, 320),
    fov=60.0,
    camera_pos=(40.0, 30.0, 40.0),
    camera_target=(16.0, 4.0, 16.0),
    bg_color=mcrfpy.Color(30, 30, 40)  # Dark atmosphere
)
scene.children.append(viewport)

# Global voxel grid reference
voxels = None
seed = 42

def generate_dungeon(dungeon_seed=42):
    """Generate a procedural dungeon showcasing all bulk operations"""
    global voxels, seed
    seed = dungeon_seed
    random.seed(seed)

    # Create voxel grid for dungeon
    print(f"Generating dungeon (seed={seed})...")
    voxels = mcrfpy.VoxelGrid(size=(32, 12, 32), cell_size=1.0)

    # Define materials
    STONE_WALL = voxels.add_material("stone_wall", color=mcrfpy.Color(80, 80, 90))
    STONE_FLOOR = voxels.add_material("stone_floor", color=mcrfpy.Color(100, 95, 90))
    MOSS = voxels.add_material("moss", color=mcrfpy.Color(40, 80, 40))
    WATER = voxels.add_material("water", color=mcrfpy.Color(40, 80, 160, 180), transparent=True)
    PILLAR = voxels.add_material("pillar", color=mcrfpy.Color(120, 110, 100))
    GOLD = voxels.add_material("gold", color=mcrfpy.Color(255, 215, 0))

    print(f"Defined {voxels.material_count} materials")

    # 1. Main room using fill_box_hollow
    print("Building main room with fill_box_hollow...")
    voxels.fill_box_hollow((2, 0, 2), (29, 10, 29), STONE_WALL, thickness=1)

    # 2. Floor with slight variation using fill_box
    voxels.fill_box((3, 0, 3), (28, 0, 28), STONE_FLOOR)

    # 3. Spherical alcoves carved into walls using fill_sphere
    print("Carving alcoves with fill_sphere...")
    alcove_positions = [
        (2, 5, 16),   # West wall
        (29, 5, 16),  # East wall
        (16, 5, 2),   # North wall
        (16, 5, 29),  # South wall
    ]
    for pos in alcove_positions:
        voxels.fill_sphere(pos, 3, 0)  # Carve out (air)

    # 4. Small decorative spheres (gold orbs in alcoves)
    print("Adding gold orbs in alcoves...")
    for i, pos in enumerate(alcove_positions):
        # Offset inward so orb is visible
        ox, oy, oz = pos
        if ox < 10:
            ox += 2
        elif ox > 20:
            ox -= 2
        if oz < 10:
            oz += 2
        elif oz > 20:
            oz -= 2
        voxels.fill_sphere((ox, oy - 1, oz), 1, GOLD)

    # 5. Support pillars using fill_cylinder
    print("Building pillars with fill_cylinder...")
    pillar_positions = [
        (8, 1, 8), (8, 1, 24),
        (24, 1, 8), (24, 1, 24),
        (16, 1, 8), (16, 1, 24),
        (8, 1, 16), (24, 1, 16),
    ]
    for px, py, pz in pillar_positions:
        voxels.fill_cylinder((px, py, pz), 1, 9, PILLAR)

    # 6. Moss patches using fill_noise
    print("Adding moss patches with fill_noise...")
    voxels.fill_noise((3, 1, 3), (28, 1, 28), MOSS, threshold=0.65, scale=0.15, seed=seed)

    # 7. Central water pool
    print("Creating water pool...")
    voxels.fill_box((12, 0, 12), (20, 0, 20), 0)  # Carve depression
    voxels.fill_box((12, 0, 12), (20, 0, 20), WATER)

    # 8. Copy a pillar as prefab and paste variations
    print("Creating prefab from pillar and pasting copies...")
    pillar_prefab = voxels.copy_region((8, 1, 8), (9, 9, 9))
    print(f"  Pillar prefab: {pillar_prefab.size}")

    # Paste smaller pillars at corners (offset from main room)
    corner_positions = [(4, 1, 4), (4, 1, 27), (27, 1, 4), (27, 1, 27)]
    for cx, cy, cz in corner_positions:
        voxels.paste_region(pillar_prefab, (cx, cy, cz), skip_air=True)

    # Build mesh
    voxels.rebuild_mesh()

    print(f"\nDungeon generated:")
    print(f"  Non-air voxels: {voxels.count_non_air()}")
    print(f"  Vertices: {voxels.vertex_count}")
    print(f"  Faces: {voxels.vertex_count // 6}")

    # Add to viewport
    # First remove old layer if exists
    if viewport.voxel_layer_count() > 0:
        pass  # Can't easily remove, so we regenerate the whole viewport
    viewport.add_voxel_layer(voxels, z_index=0)

    return voxels

# Generate initial dungeon
generate_dungeon(42)

# Create info panel
info_frame = mcrfpy.Frame(pos=(690, 60), size=(300, 280), fill_color=mcrfpy.Color(40, 40, 60, 220))
scene.children.append(info_frame)

info_title = mcrfpy.Caption(text="Dungeon Stats", pos=(700, 70))
info_title.fill_color = mcrfpy.Color(255, 255, 100)
scene.children.append(info_title)

def update_stats():
    global stats_caption
    stats_text = f"""Grid: {voxels.width}x{voxels.height}x{voxels.depth}
Total cells: {voxels.width * voxels.height * voxels.depth}
Non-air: {voxels.count_non_air()}
Materials: {voxels.material_count}

Mesh Stats:
  Vertices: {voxels.vertex_count}
  Faces: {voxels.vertex_count // 6}

Seed: {seed}

Operations Used:
  - fill_box_hollow (walls)
  - fill_sphere (alcoves)
  - fill_cylinder (pillars)
  - fill_noise (moss)
  - copy/paste (prefabs)"""
    stats_caption.text = stats_text

stats_caption = mcrfpy.Caption(text="", pos=(700, 100))
stats_caption.fill_color = mcrfpy.Color(200, 200, 200)
scene.children.append(stats_caption)
update_stats()

# Controls panel
controls_frame = mcrfpy.Frame(pos=(690, 360), size=(300, 180), fill_color=mcrfpy.Color(40, 40, 60, 220))
scene.children.append(controls_frame)

controls_title = mcrfpy.Caption(text="Controls", pos=(700, 370))
controls_title.fill_color = mcrfpy.Color(255, 255, 100)
scene.children.append(controls_title)

controls_text = """R - Regenerate dungeon (new seed)
1-4 - Camera presets
+/- - Zoom in/out
SPACE - Reset camera
ESC - Exit demo"""

controls = mcrfpy.Caption(text=controls_text, pos=(700, 400))
controls.fill_color = mcrfpy.Color(200, 200, 200)
scene.children.append(controls)

# Camera animation state
rotation_enabled = False
camera_distance = 50.0
camera_angle = 45.0  # degrees
camera_height = 30.0

camera_presets = [
    (40.0, 30.0, 40.0, 16.0, 4.0, 16.0),   # Default diagonal
    (16.0, 30.0, 50.0, 16.0, 4.0, 16.0),   # Front view
    (50.0, 30.0, 16.0, 16.0, 4.0, 16.0),   # Side view
    (16.0, 50.0, 16.0, 16.0, 4.0, 16.0),   # Top-down
]

def rotate_camera(timer_name, runtime):
    """Timer callback for camera rotation"""
    global camera_angle, rotation_enabled
    if rotation_enabled:
        camera_angle += 0.5
        if camera_angle >= 360.0:
            camera_angle = 0.0
        rad = camera_angle * math.pi / 180.0
        x = 16.0 + camera_distance * math.cos(rad)
        z = 16.0 + camera_distance * math.sin(rad)
        viewport.camera_pos = (x, camera_height, z)

# Set up rotation timer
timer = mcrfpy.Timer("rotate_cam", rotate_camera, 33)

def handle_key(key, action):
    """Keyboard handler"""
    global rotation_enabled, seed, camera_distance, camera_height
    if action != mcrfpy.InputState.PRESSED:
        return

    if key == mcrfpy.Key.R:
        seed = random.randint(1, 99999)
        generate_dungeon(seed)
        update_stats()
        print(f"Regenerated dungeon with seed {seed}")
    elif key == mcrfpy.Key.NUM_1:
        viewport.camera_pos = camera_presets[0][:3]
        viewport.camera_target = camera_presets[0][3:]
        rotation_enabled = False
    elif key == mcrfpy.Key.NUM_2:
        viewport.camera_pos = camera_presets[1][:3]
        viewport.camera_target = camera_presets[1][3:]
        rotation_enabled = False
    elif key == mcrfpy.Key.NUM_3:
        viewport.camera_pos = camera_presets[2][:3]
        viewport.camera_target = camera_presets[2][3:]
        rotation_enabled = False
    elif key == mcrfpy.Key.NUM_4:
        viewport.camera_pos = camera_presets[3][:3]
        viewport.camera_target = camera_presets[3][3:]
        rotation_enabled = False
    elif key == mcrfpy.Key.SPACE:
        rotation_enabled = not rotation_enabled
        print(f"Camera rotation: {'ON' if rotation_enabled else 'OFF'}")
    elif key == mcrfpy.Key.EQUALS or key == mcrfpy.Key.ADD:
        camera_distance = max(20.0, camera_distance - 5.0)
        camera_height = max(15.0, camera_height - 2.0)
    elif key == mcrfpy.Key.DASH or key == mcrfpy.Key.SUBTRACT:
        camera_distance = min(80.0, camera_distance + 5.0)
        camera_height = min(50.0, camera_height + 2.0)
    elif key == mcrfpy.Key.ESCAPE:
        print("Exiting demo...")
        sys.exit(0)

scene.on_key = handle_key

# Activate the scene
mcrfpy.current_scene = scene
print("\nVoxel Dungeon Demo ready!")
print("Press SPACE to toggle camera rotation, R to regenerate")

# Main entry point for --exec mode
if __name__ == "__main__":
    print("\n=== Voxel Dungeon Demo Summary ===")
    print(f"Grid size: {voxels.width}x{voxels.height}x{voxels.depth}")
    print(f"Non-air voxels: {voxels.count_non_air()}")
    print(f"Generated vertices: {voxels.vertex_count}")
    print(f"Rendered faces: {voxels.vertex_count // 6}")
    print("===================================\n")
