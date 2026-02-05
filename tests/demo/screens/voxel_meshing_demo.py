# voxel_meshing_demo.py - Visual demo of VoxelGrid mesh rendering
# Shows voxel building rendered in Viewport3D with PS1 effects

import mcrfpy
import sys
import math

# Create demo scene
scene = mcrfpy.Scene("voxel_meshing_demo")

# Dark background frame
bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(15, 15, 25))
scene.children.append(bg)

# Title
title = mcrfpy.Caption(text="VoxelGrid Meshing Demo - Face-Culled 3D Voxels", pos=(20, 10))
title.fill_color = mcrfpy.Color(255, 255, 255)
scene.children.append(title)

# Create the 3D viewport
viewport = mcrfpy.Viewport3D(
    pos=(50, 60),
    size=(600, 500),
    render_resolution=(320, 240),  # PS1 resolution
    fov=60.0,
    camera_pos=(20.0, 15.0, 20.0),
    camera_target=(4.0, 2.0, 4.0),
    bg_color=mcrfpy.Color(50, 70, 100)  # Sky color
)
scene.children.append(viewport)

# Create voxel grid for building
print("Creating voxel building...")
voxels = mcrfpy.VoxelGrid(size=(12, 8, 12), cell_size=1.0)

# Define materials
STONE = voxels.add_material("stone", color=mcrfpy.Color(128, 128, 128))
BRICK = voxels.add_material("brick", color=mcrfpy.Color(165, 82, 42))
WOOD = voxels.add_material("wood", color=mcrfpy.Color(139, 90, 43))
GLASS = voxels.add_material("glass", color=mcrfpy.Color(180, 220, 255, 180), transparent=True)
GRASS = voxels.add_material("grass", color=mcrfpy.Color(60, 150, 60))

print(f"Defined {voxels.material_count} materials")

# Build a simple house structure

# Ground/foundation
voxels.fill_box((0, 0, 0), (11, 0, 11), GRASS)

# Floor
voxels.fill_box((1, 1, 1), (10, 1, 10), STONE)

# Walls
# Front wall (Z=1)
voxels.fill_box((1, 2, 1), (10, 5, 1), BRICK)
# Back wall (Z=10)
voxels.fill_box((1, 2, 10), (10, 5, 10), BRICK)
# Left wall (X=1)
voxels.fill_box((1, 2, 1), (1, 5, 10), BRICK)
# Right wall (X=10)
voxels.fill_box((10, 2, 1), (10, 5, 10), BRICK)

# Door opening (front wall)
voxels.fill_box((4, 2, 1), (6, 4, 1), 0)  # Clear door opening

# Windows
# Front windows (beside door)
voxels.fill_box((2, 3, 1), (3, 4, 1), GLASS)
voxels.fill_box((8, 3, 1), (9, 4, 1), GLASS)
# Side windows
voxels.fill_box((1, 3, 4), (1, 4, 5), GLASS)
voxels.fill_box((1, 3, 7), (1, 4, 8), GLASS)
voxels.fill_box((10, 3, 4), (10, 4, 5), GLASS)
voxels.fill_box((10, 3, 7), (10, 4, 8), GLASS)

# Ceiling
voxels.fill_box((1, 6, 1), (10, 6, 10), WOOD)

# Simple roof (peaked)
voxels.fill_box((0, 7, 0), (11, 7, 11), WOOD)
voxels.fill_box((1, 8, 1), (10, 8, 10), WOOD)
voxels.fill_box((2, 9, 2), (9, 9, 9), WOOD)
voxels.fill_box((3, 10, 3), (8, 10, 8), WOOD)
voxels.fill_box((4, 11, 4), (7, 11, 7), WOOD)

# Build the mesh
voxels.rebuild_mesh()

print(f"Built voxel house:")
print(f"  Non-air voxels: {voxels.count_non_air()}")
print(f"  Vertices: {voxels.vertex_count}")
print(f"  Faces: {voxels.vertex_count // 6}")

# Position the building
voxels.offset = (0.0, 0.0, 0.0)
voxels.rotation = 0.0

# Add to viewport
viewport.add_voxel_layer(voxels, z_index=0)
print(f"Added voxel layer to viewport (count: {viewport.voxel_layer_count()})")

# Create info panel
info_frame = mcrfpy.Frame(pos=(680, 60), size=(300, 250), fill_color=mcrfpy.Color(40, 40, 60, 200))
scene.children.append(info_frame)

info_title = mcrfpy.Caption(text="Building Stats", pos=(690, 70))
info_title.fill_color = mcrfpy.Color(255, 255, 100)
scene.children.append(info_title)

stats_text = f"""Grid: {voxels.width}x{voxels.height}x{voxels.depth}
Total voxels: {voxels.width * voxels.height * voxels.depth}
Non-air: {voxels.count_non_air()}
Materials: {voxels.material_count}
Vertices: {voxels.vertex_count}
Faces: {voxels.vertex_count // 6}

Without culling would be:
  {voxels.count_non_air() * 36} vertices
  ({100 - (voxels.vertex_count / (voxels.count_non_air() * 36) * 100):.0f}% reduction)"""

stats = mcrfpy.Caption(text=stats_text, pos=(690, 100))
stats.fill_color = mcrfpy.Color(200, 200, 200)
scene.children.append(stats)

# Controls info
controls_frame = mcrfpy.Frame(pos=(680, 330), size=(300, 180), fill_color=mcrfpy.Color(40, 40, 60, 200))
scene.children.append(controls_frame)

controls_title = mcrfpy.Caption(text="Controls", pos=(690, 340))
controls_title.fill_color = mcrfpy.Color(255, 255, 100)
scene.children.append(controls_title)

controls_text = """R - Toggle rotation
1-5 - Change camera angle
SPACE - Reset camera
ESC - Exit demo"""

controls = mcrfpy.Caption(text=controls_text, pos=(690, 370))
controls.fill_color = mcrfpy.Color(200, 200, 200)
scene.children.append(controls)

# Animation state
rotation_enabled = False
current_angle = 0.0
camera_angles = [
    (20.0, 15.0, 20.0),   # Default - diagonal view
    (0.0, 15.0, 25.0),    # Front view
    (25.0, 15.0, 0.0),    # Side view
    (5.5, 25.0, 5.5),     # Top-down view
    (5.5, 3.0, 20.0),     # Low angle
]
current_camera = 0

def rotate_building(timer, runtime):
    """Timer callback for building rotation"""
    global current_angle, rotation_enabled
    if rotation_enabled:
        current_angle += 1.0
        if current_angle >= 360.0:
            current_angle = 0.0
        voxels.rotation = current_angle

# Set up rotation timer
timer = mcrfpy.Timer("rotate", rotate_building, 33)  # ~30 FPS

def handle_key(key, action):
    """Keyboard handler"""
    global rotation_enabled, current_camera
    if action != mcrfpy.InputState.PRESSED:
        return

    if key == mcrfpy.Key.R:
        rotation_enabled = not rotation_enabled
        print(f"Rotation: {'ON' if rotation_enabled else 'OFF'}")
    elif key == mcrfpy.Key.NUM_1:
        current_camera = 0
        viewport.camera_pos = camera_angles[0]
        print("Camera: Default diagonal")
    elif key == mcrfpy.Key.NUM_2:
        current_camera = 1
        viewport.camera_pos = camera_angles[1]
        print("Camera: Front view")
    elif key == mcrfpy.Key.NUM_3:
        current_camera = 2
        viewport.camera_pos = camera_angles[2]
        print("Camera: Side view")
    elif key == mcrfpy.Key.NUM_4:
        current_camera = 3
        viewport.camera_pos = camera_angles[3]
        print("Camera: Top-down view")
    elif key == mcrfpy.Key.NUM_5:
        current_camera = 4
        viewport.camera_pos = camera_angles[4]
        print("Camera: Low angle")
    elif key == mcrfpy.Key.SPACE:
        current_camera = 0
        voxels.rotation = 0.0
        viewport.camera_pos = camera_angles[0]
        print("Camera: Reset")
    elif key == mcrfpy.Key.ESCAPE:
        print("Exiting demo...")
        sys.exit(0)

scene.on_key = handle_key

# Activate the scene
mcrfpy.current_scene = scene
print("Voxel Meshing Demo ready! Press R to toggle rotation.")

# Main entry point for --exec mode
if __name__ == "__main__":
    # Demo is set up, print summary
    print("\n=== Voxel Meshing Demo Summary ===")
    print(f"Grid size: {voxels.width}x{voxels.height}x{voxels.depth}")
    print(f"Non-air voxels: {voxels.count_non_air()}")
    print(f"Generated vertices: {voxels.vertex_count}")
    print(f"Rendered faces: {voxels.vertex_count // 6}")
    print("===================================\n")
