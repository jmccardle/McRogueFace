# terrain_demo.py - Visual demo of terrain system
# Shows procedurally generated 3D terrain using HeightMap + Viewport3D

import mcrfpy
import sys
import math

# Create demo scene
scene = mcrfpy.Scene("terrain_demo")

# Dark background frame
bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(15, 15, 25))
scene.children.append(bg)

# Title
title = mcrfpy.Caption(text="Terrain System Demo - HeightMap to 3D Mesh", pos=(20, 10))
title.fill_color = mcrfpy.Color(255, 255, 255)
scene.children.append(title)

# Create the 3D viewport
viewport = mcrfpy.Viewport3D(
    pos=(50, 60),
    size=(600, 450),
    render_resolution=(320, 240),  # PS1 resolution
    fov=60.0,
    camera_pos=(30.0, 20.0, 30.0),
    camera_target=(20.0, 0.0, 20.0),
    bg_color=mcrfpy.Color(100, 150, 200)  # Sky blue background
)
scene.children.append(viewport)

# Generate terrain using HeightMap
print("Generating terrain heightmap...")
hm = mcrfpy.HeightMap((40, 40))

# Use midpoint displacement for natural-looking terrain
hm.mid_point_displacement(0.5, seed=42)
hm.normalize(0.0, 1.0)

# Optional: Add some erosion for more realistic terrain
hm.rain_erosion(drops=1000, erosion=0.08, sedimentation=0.04, seed=42)
hm.normalize(0.0, 1.0)

# Build terrain mesh from heightmap
print("Building terrain mesh...")
vertex_count = viewport.build_terrain(
    layer_name="terrain",
    heightmap=hm,
    y_scale=8.0,       # Vertical exaggeration
    cell_size=1.0      # World-space grid cell size
)
print(f"Terrain built with {vertex_count} vertices")

# Create color maps for terrain (decoupled from height)
# This demonstrates using separate HeightMaps for R, G, B channels
print("Creating terrain color maps...")
r_map = mcrfpy.HeightMap((40, 40))
g_map = mcrfpy.HeightMap((40, 40))
b_map = mcrfpy.HeightMap((40, 40))

# Generate a "moisture" map using different noise
moisture = mcrfpy.HeightMap((40, 40))
moisture.mid_point_displacement(0.6, seed=999)
moisture.normalize(0.0, 1.0)

# Color based on height + moisture combination:
# Low + wet = water blue, Low + dry = sand yellow
# High + wet = grass green, High + dry = rock brown/snow white
for y in range(40):
    for x in range(40):
        h = hm[x, y]  # Height (0-1)
        m = moisture[x, y]  # Moisture (0-1)

        if h < 0.3:  # Low elevation
            if m > 0.5:  # Wet = water
                r_map[x, y] = 0.2
                g_map[x, y] = 0.4
                b_map[x, y] = 0.8
            else:  # Dry = sand
                r_map[x, y] = 0.9
                g_map[x, y] = 0.8
                b_map[x, y] = 0.5
        elif h < 0.6:  # Mid elevation
            if m > 0.4:  # Wet = grass
                r_map[x, y] = 0.2 + h * 0.3
                g_map[x, y] = 0.5 + m * 0.3
                b_map[x, y] = 0.1
            else:  # Dry = dirt
                r_map[x, y] = 0.5
                g_map[x, y] = 0.35
                b_map[x, y] = 0.2
        else:  # High elevation
            if h > 0.85:  # Snow caps
                r_map[x, y] = 0.95
                g_map[x, y] = 0.95
                b_map[x, y] = 1.0
            else:  # Rock
                r_map[x, y] = 0.5
                g_map[x, y] = 0.45
                b_map[x, y] = 0.4

# Apply colors to terrain
viewport.apply_terrain_colors("terrain", r_map, g_map, b_map)
print("Terrain colors applied")

# Info panel on the right
info_panel = mcrfpy.Frame(pos=(670, 60), size=(330, 450),
                          fill_color=mcrfpy.Color(30, 30, 40),
                          outline_color=mcrfpy.Color(80, 80, 100),
                          outline=2.0)
scene.children.append(info_panel)

# Panel title
panel_title = mcrfpy.Caption(text="Terrain Properties", pos=(690, 70))
panel_title.fill_color = mcrfpy.Color(200, 200, 255)
scene.children.append(panel_title)

# Property labels
props = [
    ("HeightMap Size:", f"{hm.size[0]}x{hm.size[1]}"),
    ("Vertex Count:", f"{vertex_count}"),
    ("Y Scale:", "8.0"),
    ("Cell Size:", "1.0"),
    ("", ""),
    ("Generation:", ""),
    ("  Algorithm:", "Midpoint Displacement"),
    ("  Roughness:", "0.5"),
    ("  Erosion:", "1000 drops"),
    ("", ""),
    ("Layer Count:", f"{viewport.layer_count()}"),
]

y_offset = 100
for label, value in props:
    if label:
        cap = mcrfpy.Caption(text=f"{label} {value}", pos=(690, y_offset))
        cap.fill_color = mcrfpy.Color(180, 180, 200)
        scene.children.append(cap)
    y_offset += 22

# Instructions at bottom
instructions = mcrfpy.Caption(
    text="[Space] Orbit | [C] Colors | [1-4] PS1 effects | [+/-] Height | [ESC] Quit",
    pos=(20, 530)
)
instructions.fill_color = mcrfpy.Color(150, 150, 150)
scene.children.append(instructions)

# Status line
status = mcrfpy.Caption(text="Status: Terrain rendering with PS1 effects", pos=(20, 555))
status.fill_color = mcrfpy.Color(100, 200, 100)
scene.children.append(status)

# Animation state
animation_time = [0.0]
camera_orbit = [True]
terrain_height = [8.0]
colors_enabled = [True]

# White color map for "no colors" mode
white_r = mcrfpy.HeightMap((40, 40))
white_g = mcrfpy.HeightMap((40, 40))
white_b = mcrfpy.HeightMap((40, 40))
white_r.fill(1.0)
white_g.fill(1.0)
white_b.fill(1.0)

# Camera orbit animation
def update_camera(timer, runtime):
    animation_time[0] += runtime / 1000.0

    if camera_orbit[0]:
        # Orbit camera around terrain center
        angle = animation_time[0] * 0.3  # Slow rotation
        radius = 35.0
        center_x = 20.0
        center_z = 20.0
        height = 15.0 + math.sin(animation_time[0] * 0.2) * 5.0

        x = center_x + math.cos(angle) * radius
        z = center_z + math.sin(angle) * radius

        viewport.camera_pos = (x, height, z)
        viewport.camera_target = (center_x, 2.0, center_z)

# Key handler
def on_key(key, state):
    if state != mcrfpy.InputState.PRESSED:
        return

    # Toggle PS1 effects with number keys
    if key == mcrfpy.Key.NUM_1:
        viewport.enable_vertex_snap = not viewport.enable_vertex_snap
        status.text = f"Vertex Snap: {'ON' if viewport.enable_vertex_snap else 'OFF'}"
    elif key == mcrfpy.Key.NUM_2:
        viewport.enable_affine = not viewport.enable_affine
        status.text = f"Affine Mapping: {'ON' if viewport.enable_affine else 'OFF'}"
    elif key == mcrfpy.Key.NUM_3:
        viewport.enable_dither = not viewport.enable_dither
        status.text = f"Dithering: {'ON' if viewport.enable_dither else 'OFF'}"
    elif key == mcrfpy.Key.NUM_4:
        viewport.enable_fog = not viewport.enable_fog
        status.text = f"Fog: {'ON' if viewport.enable_fog else 'OFF'}"

    # Toggle terrain colors
    elif key == mcrfpy.Key.C:
        colors_enabled[0] = not colors_enabled[0]
        if colors_enabled[0]:
            viewport.apply_terrain_colors("terrain", r_map, g_map, b_map)
            status.text = "Terrain colors: ON (height + moisture)"
        else:
            viewport.apply_terrain_colors("terrain", white_r, white_g, white_b)
            status.text = "Terrain colors: OFF (white)"

    # Camera controls
    elif key == mcrfpy.Key.SPACE:
        camera_orbit[0] = not camera_orbit[0]
        status.text = f"Camera orbit: {'ON' if camera_orbit[0] else 'OFF (WASD/QE to move)'}"

    # Height adjustment
    elif key == mcrfpy.Key.EQUAL:  # + key
        terrain_height[0] += 1.0
        rebuild_terrain()
    elif key == mcrfpy.Key.HYPHEN:  # - key
        terrain_height[0] = max(1.0, terrain_height[0] - 1.0)
        rebuild_terrain()

    elif key == mcrfpy.Key.ESCAPE:
        mcrfpy.exit()

    # Manual camera movement (when orbit is off)
    if not camera_orbit[0]:
        pos = list(viewport.camera_pos)
        target = list(viewport.camera_target)
        speed = 2.0

        if key == mcrfpy.Key.W:
            # Move forward (toward target)
            dx = target[0] - pos[0]
            dz = target[2] - pos[2]
            length = math.sqrt(dx*dx + dz*dz)
            if length > 0.01:
                pos[0] += (dx / length) * speed
                pos[2] += (dz / length) * speed
                target[0] += (dx / length) * speed
                target[2] += (dz / length) * speed
        elif key == mcrfpy.Key.S:
            # Move backward
            dx = target[0] - pos[0]
            dz = target[2] - pos[2]
            length = math.sqrt(dx*dx + dz*dz)
            if length > 0.01:
                pos[0] -= (dx / length) * speed
                pos[2] -= (dz / length) * speed
                target[0] -= (dx / length) * speed
                target[2] -= (dz / length) * speed
        elif key == mcrfpy.Key.A:
            # Strafe left
            dx = target[0] - pos[0]
            dz = target[2] - pos[2]
            # Perpendicular direction
            pos[0] -= dz / math.sqrt(dx*dx + dz*dz) * speed
            pos[2] += dx / math.sqrt(dx*dx + dz*dz) * speed
            target[0] -= dz / math.sqrt(dx*dx + dz*dz) * speed
            target[2] += dx / math.sqrt(dx*dx + dz*dz) * speed
        elif key == mcrfpy.Key.D:
            # Strafe right
            dx = target[0] - pos[0]
            dz = target[2] - pos[2]
            pos[0] += dz / math.sqrt(dx*dx + dz*dz) * speed
            pos[2] -= dx / math.sqrt(dx*dx + dz*dz) * speed
            target[0] += dz / math.sqrt(dx*dx + dz*dz) * speed
            target[2] -= dx / math.sqrt(dx*dx + dz*dz) * speed
        elif key == mcrfpy.Key.Q:
            # Move down
            pos[1] -= speed
        elif key == mcrfpy.Key.E:
            # Move up
            pos[1] += speed

        viewport.camera_pos = tuple(pos)
        viewport.camera_target = tuple(target)
        status.text = f"Camera: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})"

def rebuild_terrain():
    """Rebuild terrain with new height scale"""
    global vertex_count
    vertex_count = viewport.build_terrain(
        layer_name="terrain",
        heightmap=hm,
        y_scale=terrain_height[0],
        cell_size=1.0
    )
    # Reapply colors after rebuild
    if colors_enabled[0]:
        viewport.apply_terrain_colors("terrain", r_map, g_map, b_map)
    else:
        viewport.apply_terrain_colors("terrain", white_r, white_g, white_b)
    status.text = f"Terrain rebuilt: height scale = {terrain_height[0]}"

# Set up scene
scene.on_key = on_key

# Create timer for camera animation
timer = mcrfpy.Timer("camera_update", update_camera, 16)  # ~60fps

# Activate scene
mcrfpy.current_scene = scene

print()
print("Terrain Demo loaded!")
print("A 40x40 heightmap has been converted to 3D terrain mesh.")
print("Terrain colored using separate R/G/B HeightMaps based on height + moisture.")
print()
print("Controls:")
print("  [C] Toggle terrain colors")
print("  [1-4] Toggle PS1 effects")
print("  [Space] Toggle camera orbit")
print("  [+/-] Adjust terrain height scale")
print("  [ESC] Quit")
