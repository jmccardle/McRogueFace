# billboard_building_demo.py - Visual demo of Billboard and Mesh Instances
# Demonstrates camera-facing sprites and static mesh placement

import mcrfpy
import sys
import math

# Create demo scene
scene = mcrfpy.Scene("billboard_building_demo")

# Dark background frame
bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(15, 15, 25))
scene.children.append(bg)

# Title
title = mcrfpy.Caption(text="Billboard & Building Demo - 3D Sprites and Static Meshes", pos=(20, 10))
title.fill_color = mcrfpy.Color(255, 255, 255)
scene.children.append(title)

# Create the 3D viewport
viewport = mcrfpy.Viewport3D(
    pos=(50, 60),
    size=(600, 450),
    render_resolution=(320, 240),  # PS1 resolution
    fov=60.0,
    camera_pos=(16.0, 10.0, 20.0),
    camera_target=(8.0, 0.0, 8.0),
    bg_color=mcrfpy.Color(80, 120, 180)  # Sky blue background
)
scene.children.append(viewport)

# Set up the navigation grid
GRID_SIZE = 16
viewport.set_grid_size(GRID_SIZE, GRID_SIZE)

# Generate terrain
print("Generating terrain...")
hm = mcrfpy.HeightMap((GRID_SIZE, GRID_SIZE))
hm.mid_point_displacement(0.2, seed=456)  # Gentle terrain
hm.normalize(0.0, 0.5)  # Keep it low for placing objects

# Apply heightmap
viewport.apply_heightmap(hm, 2.0)

# Build terrain mesh
vertex_count = viewport.build_terrain(
    layer_name="terrain",
    heightmap=hm,
    y_scale=2.0,
    cell_size=1.0
)
print(f"Terrain built with {vertex_count} vertices")

# Create terrain colors (earthy tones)
r_map = mcrfpy.HeightMap((GRID_SIZE, GRID_SIZE))
g_map = mcrfpy.HeightMap((GRID_SIZE, GRID_SIZE))
b_map = mcrfpy.HeightMap((GRID_SIZE, GRID_SIZE))

for y in range(GRID_SIZE):
    for x in range(GRID_SIZE):
        h = hm[x, y]
        # Earth/grass colors
        r_map[x, y] = 0.25 + h * 0.2
        g_map[x, y] = 0.35 + h * 0.25
        b_map[x, y] = 0.15 + h * 0.1

viewport.apply_terrain_colors("terrain", r_map, g_map, b_map)

# =============================================================================
# PART 1: Building Placement using Mesh Instances
# =============================================================================
print("Placing buildings...")

# Add a layer for buildings
viewport.add_layer("buildings", z_index=1)

# Create a simple building model (cube-like structure)
building_model = mcrfpy.Model3D()

# Place several buildings at different locations with transforms
building_positions = [
    ((2, 0, 2), 0, 1.5),      # Position, rotation, scale
    ((12, 0, 2), 45, 1.2),
    ((4, 0, 12), 90, 1.0),
    ((10, 0, 10), 30, 1.8),
]

for pos, rotation, scale in building_positions:
    idx = viewport.add_mesh("buildings", building_model, pos=pos, rotation=rotation, scale=scale)
    print(f"  Placed building {idx} at {pos}")

    # Mark the footprint as blocking
    gx, gz = int(pos[0]), int(pos[2])
    footprint_size = max(1, int(scale))
    viewport.place_blocking(grid_pos=(gx, gz), footprint=(footprint_size, footprint_size))

print(f"Placed {len(building_positions)} buildings")

# =============================================================================
# PART 2: Billboard Sprites (camera-facing)
# =============================================================================
print("Creating billboards...")

# Create billboards for "trees" - camera_y mode (stays upright)
tree_positions = [
    (3, 0, 5), (5, 0, 3), (6, 0, 8), (9, 0, 5),
    (11, 0, 7), (7, 0, 11), (13, 0, 13), (1, 0, 9)
]

# Note: Without actual textures, billboards will render as simple quads
# In a real game, you'd load a tree sprite texture
for i, pos in enumerate(tree_positions):
    bb = mcrfpy.Billboard(
        pos=pos,
        scale=1.5,
        facing="camera_y",  # Stays upright, only rotates on Y axis
        opacity=1.0
    )
    viewport.add_billboard(bb)

print(f"  Created {len(tree_positions)} tree billboards (camera_y facing)")

# Create some particle-like billboards - full camera facing
particle_positions = [
    (8, 3, 8), (8.5, 3.5, 8.2), (7.5, 3.2, 7.8),  # Floating particles
]

for i, pos in enumerate(particle_positions):
    bb = mcrfpy.Billboard(
        pos=pos,
        scale=0.3,
        facing="camera",  # Full rotation to face camera
        opacity=0.7
    )
    viewport.add_billboard(bb)

print(f"  Created {len(particle_positions)} particle billboards (camera facing)")

# Create a fixed-orientation billboard (signpost)
signpost = mcrfpy.Billboard(
    pos=(5, 1.5, 5),
    scale=1.0,
    facing="fixed",  # Manual orientation
)
signpost.theta = math.pi / 4  # 45 degrees horizontal
signpost.phi = 0.0  # No vertical tilt
viewport.add_billboard(signpost)

print(f"  Created 1 signpost billboard (fixed facing)")
print(f"Total billboards: {viewport.billboard_count()}")

# =============================================================================
# Info Panel
# =============================================================================
info_panel = mcrfpy.Frame(pos=(670, 60), size=(330, 450),
                          fill_color=mcrfpy.Color(30, 30, 40),
                          outline_color=mcrfpy.Color(80, 80, 100),
                          outline=2.0)
scene.children.append(info_panel)

# Panel title
panel_title = mcrfpy.Caption(text="Billboard & Mesh Demo", pos=(690, 70))
panel_title.fill_color = mcrfpy.Color(200, 200, 255)
scene.children.append(panel_title)

# Billboard info
bb_info = [
    ("", ""),
    ("Billboard Modes:", ""),
    ("  camera", "Full rotation to face camera"),
    ("  camera_y", "Y-axis only (stays upright)"),
    ("  fixed", "Manual theta/phi angles"),
    ("", ""),
    (f"Trees:", f"{len(tree_positions)} (camera_y)"),
    (f"Particles:", f"{len(particle_positions)} (camera)"),
    (f"Signpost:", "1 (fixed)"),
    ("", ""),
    ("Mesh Instances:", ""),
    (f"  Buildings:", f"{len(building_positions)}"),
]

y_offset = 100
for label, value in bb_info:
    if label or value:
        text = f"{label} {value}" if value else label
        cap = mcrfpy.Caption(text=text, pos=(690, y_offset))
        cap.fill_color = mcrfpy.Color(150, 150, 170)
        scene.children.append(cap)
    y_offset += 22

# Dynamic camera info
camera_label = mcrfpy.Caption(text="Camera: Following...", pos=(690, y_offset + 20))
camera_label.fill_color = mcrfpy.Color(180, 180, 200)
scene.children.append(camera_label)

# Instructions at bottom
instructions = mcrfpy.Caption(
    text="[Space] Toggle orbit | [1-3] Change billboard mode | [C] Clear buildings | [ESC] Quit",
    pos=(20, 530)
)
instructions.fill_color = mcrfpy.Color(150, 150, 150)
scene.children.append(instructions)

# Status line
status = mcrfpy.Caption(text="Status: Billboard & Building demo loaded", pos=(20, 555))
status.fill_color = mcrfpy.Color(100, 200, 100)
scene.children.append(status)

# Animation state
animation_time = [0.0]
camera_orbit = [True]

# Update function
def update(timer, runtime):
    animation_time[0] += runtime / 1000.0

    # Camera orbit
    if camera_orbit[0]:
        angle = animation_time[0] * 0.3
        radius = 18.0
        center_x = 8.0
        center_z = 8.0
        height = 10.0 + math.sin(animation_time[0] * 0.2) * 2.0

        x = center_x + math.cos(angle) * radius
        z = center_z + math.sin(angle) * radius

        viewport.camera_pos = (x, height, z)
        viewport.camera_target = (center_x, 1.0, center_z)

        camera_label.text = f"Camera: Orbit ({x:.1f}, {height:.1f}, {z:.1f})"

    # Animate particle billboards (bobbing up and down)
    bb_count = viewport.billboard_count()
    if bb_count > len(tree_positions):
        particle_start = len(tree_positions)
        for i in range(particle_start, particle_start + len(particle_positions)):
            if i < bb_count:
                bb = viewport.get_billboard(i)
                pos = bb.pos
                new_y = 3.0 + math.sin(animation_time[0] * 2.0 + i * 0.5) * 0.5
                bb.pos = (pos[0], new_y, pos[2])

# Key handler
def on_key(key, state):
    if state != mcrfpy.InputState.PRESSED:
        return

    if key == mcrfpy.Key.SPACE:
        camera_orbit[0] = not camera_orbit[0]
        status.text = f"Camera orbit: {'ON' if camera_orbit[0] else 'OFF'}"

    elif key == mcrfpy.Key.NUM_1:
        # Change all tree billboards to "camera" mode
        for i in range(len(tree_positions)):
            viewport.get_billboard(i).facing = "camera"
        status.text = "Trees now use 'camera' facing (full rotation)"

    elif key == mcrfpy.Key.NUM_2:
        # Change all tree billboards to "camera_y" mode
        for i in range(len(tree_positions)):
            viewport.get_billboard(i).facing = "camera_y"
        status.text = "Trees now use 'camera_y' facing (upright)"

    elif key == mcrfpy.Key.NUM_3:
        # Change all tree billboards to "fixed" mode
        for i in range(len(tree_positions)):
            bb = viewport.get_billboard(i)
            bb.facing = "fixed"
            bb.theta = i * 0.5  # Different angles
        status.text = "Trees now use 'fixed' facing (manual angles)"

    elif key == mcrfpy.Key.C:
        viewport.clear_meshes("buildings")
        status.text = "Cleared all buildings from layer"

    elif key == mcrfpy.Key.O:
        # Adjust tree opacity
        for i in range(len(tree_positions)):
            bb = viewport.get_billboard(i)
            bb.opacity = 0.5 if bb.opacity > 0.7 else 1.0
        status.text = f"Tree opacity toggled"

    elif key == mcrfpy.Key.V:
        # Toggle tree visibility
        for i in range(len(tree_positions)):
            bb = viewport.get_billboard(i)
            bb.visible = not bb.visible
        status.text = f"Tree visibility toggled"

    elif key == mcrfpy.Key.ESCAPE:
        mcrfpy.exit()

# Set up scene
scene.on_key = on_key

# Create timer for updates
timer = mcrfpy.Timer("billboard_update", update, 16)  # ~60fps

# Activate scene
mcrfpy.current_scene = scene

print()
print("Billboard & Building Demo loaded!")
print()
print("Controls:")
print("  [Space] Toggle camera orbit")
print("  [1] Trees -> 'camera' facing")
print("  [2] Trees -> 'camera_y' facing (default)")
print("  [3] Trees -> 'fixed' facing")
print("  [O] Toggle tree opacity")
print("  [V] Toggle tree visibility")
print("  [C] Clear buildings")
print("  [ESC] Quit")
