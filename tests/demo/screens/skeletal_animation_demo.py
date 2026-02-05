# skeletal_animation_demo.py - 3D Skeletal Animation Demo Screen
# Demonstrates Entity3D animation with real animated glTF models

import mcrfpy
import sys
import os

DEMO_NAME = "3D Skeletal Animation"
DEMO_DESCRIPTION = """Entity3D Animation API with real skeletal models"""

# Create demo scene
scene = mcrfpy.Scene("skeletal_animation_demo")

# Dark background frame
bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(15, 15, 25))
scene.children.append(bg)

# Title
title = mcrfpy.Caption(text="Skeletal Animation Demo", pos=(20, 10))
title.fill_color = mcrfpy.Color(255, 255, 100)
scene.children.append(title)

# Create the 3D viewport
viewport = mcrfpy.Viewport3D(
    pos=(50, 50),
    size=(600, 500),
    render_resolution=(600, 500),
    fov=60.0,
    camera_pos=(0.0, 2.0, 5.0),
    camera_target=(0.0, 1.0, 0.0),
    bg_color=mcrfpy.Color(30, 30, 50)
)
scene.children.append(viewport)

# Set up navigation grid
GRID_SIZE = 16
viewport.set_grid_size(GRID_SIZE, GRID_SIZE)

# Build a simple flat floor
hm = mcrfpy.HeightMap((GRID_SIZE, GRID_SIZE))
hm.normalize(0.0, 0.0)
viewport.apply_heightmap(hm, 0.0)
viewport.build_terrain(
    layer_name="floor",
    heightmap=hm,
    y_scale=0.0,
    cell_size=1.0
)

# Apply floor colors (dark gray)
r_map = mcrfpy.HeightMap((GRID_SIZE, GRID_SIZE))
g_map = mcrfpy.HeightMap((GRID_SIZE, GRID_SIZE))
b_map = mcrfpy.HeightMap((GRID_SIZE, GRID_SIZE))
for y in range(GRID_SIZE):
    for x in range(GRID_SIZE):
        checker = ((x + y) % 2) * 0.1 + 0.15
        r_map[x, y] = checker
        g_map[x, y] = checker
        b_map[x, y] = checker + 0.05
viewport.apply_terrain_colors("floor", r_map, g_map, b_map)

# Load animated models
animated_entity = None
model_info = "No animated model"

# Try to load CesiumMan (humanoid with walk animation)
try:
    model = mcrfpy.Model3D("../assets/models/CesiumMan.glb")
    if model.has_skeleton:
        animated_entity = mcrfpy.Entity3D(pos=(8, 8), scale=1.0, color=mcrfpy.Color(200, 180, 150))
        animated_entity.model = model
        viewport.entities.append(animated_entity)

        # Set up animation
        clips = model.animation_clips
        if clips:
            animated_entity.anim_clip = clips[0]
            animated_entity.anim_loop = True
            animated_entity.anim_speed = 1.0

        model_info = f"CesiumMan: {model.bone_count} bones, {model.vertex_count} verts"
        print(f"Loaded {model_info}")
        print(f"Animation clips: {clips}")
except Exception as e:
    print(f"Failed to load CesiumMan: {e}")

# Also try RiggedSimple as a second model
try:
    model2 = mcrfpy.Model3D("../assets/models/RiggedSimple.glb")
    if model2.has_skeleton:
        entity2 = mcrfpy.Entity3D(pos=(10, 8), scale=0.5, color=mcrfpy.Color(100, 200, 255))
        entity2.model = model2
        viewport.entities.append(entity2)

        clips = model2.animation_clips
        if clips:
            entity2.anim_clip = clips[0]
            entity2.anim_loop = True
            entity2.anim_speed = 1.5

        print(f"Loaded RiggedSimple: {model2.bone_count} bones")
except Exception as e:
    print(f"Failed to load RiggedSimple: {e}")

# Info panel on the right
info_panel = mcrfpy.Frame(pos=(670, 50), size=(330, 500),
                          fill_color=mcrfpy.Color(30, 30, 40),
                          outline_color=mcrfpy.Color(80, 80, 100),
                          outline=2.0)
scene.children.append(info_panel)

# Panel title
panel_title = mcrfpy.Caption(text="Animation Properties", pos=(690, 60))
panel_title.fill_color = mcrfpy.Color(200, 200, 255)
scene.children.append(panel_title)

# Status labels (will be updated by timer)
status_labels = []
y_offset = 90

label_texts = [
    "Model: loading...",
    "anim_clip: ",
    "anim_time: 0.00",
    "anim_speed: 1.00",
    "anim_loop: True",
    "anim_paused: False",
    "anim_frame: 0",
]

for text in label_texts:
    label = mcrfpy.Caption(text=text, pos=(690, y_offset))
    label.fill_color = mcrfpy.Color(150, 200, 150)
    scene.children.append(label)
    status_labels.append(label)
    y_offset += 25

# Set initial model info
status_labels[0].text = f"Model: {model_info}"

# Controls section
y_offset += 20
controls_title = mcrfpy.Caption(text="Controls:", pos=(690, y_offset))
controls_title.fill_color = mcrfpy.Color(255, 255, 200)
scene.children.append(controls_title)
y_offset += 25

controls = [
    "[SPACE] Toggle pause",
    "[L] Toggle loop",
    "[+/-] Adjust speed",
    "[R] Reset time",
    "[1-3] Camera presets",
]

for ctrl in controls:
    cap = mcrfpy.Caption(text=ctrl, pos=(690, y_offset))
    cap.fill_color = mcrfpy.Color(180, 180, 150)
    scene.children.append(cap)
    y_offset += 20

# Auto-animate section
y_offset += 20
auto_title = mcrfpy.Caption(text="Auto-Animate:", pos=(690, y_offset))
auto_title.fill_color = mcrfpy.Color(255, 200, 200)
scene.children.append(auto_title)
y_offset += 25

auto_labels = []
auto_texts = [
    "auto_animate: True",
    "walk_clip: 'walk'",
    "idle_clip: 'idle'",
]

for text in auto_texts:
    cap = mcrfpy.Caption(text=text, pos=(690, y_offset))
    cap.fill_color = mcrfpy.Color(180, 160, 160)
    scene.children.append(cap)
    auto_labels.append(cap)
    y_offset += 20

# Instructions at bottom
status = mcrfpy.Caption(text="Status: Animation playing", pos=(20, 570))
status.fill_color = mcrfpy.Color(100, 200, 100)
scene.children.append(status)

# Camera presets
camera_presets = [
    ((0.0, 2.0, 5.0), (0.0, 1.0, 0.0), "Front view"),
    ((5.0, 3.0, 0.0), (0.0, 1.0, 0.0), "Side view"),
    ((0.0, 6.0, 0.1), (0.0, 0.0, 0.0), "Top-down view"),
]

# Update function - updates display and entity rotation
def update(timer, runtime):
    if animated_entity:
        # Update status display
        status_labels[1].text = f"anim_clip: '{animated_entity.anim_clip}'"
        status_labels[2].text = f"anim_time: {animated_entity.anim_time:.2f}"
        status_labels[3].text = f"anim_speed: {animated_entity.anim_speed:.2f}"
        status_labels[4].text = f"anim_loop: {animated_entity.anim_loop}"
        status_labels[5].text = f"anim_paused: {animated_entity.anim_paused}"
        status_labels[6].text = f"anim_frame: {animated_entity.anim_frame}"

        auto_labels[0].text = f"auto_animate: {animated_entity.auto_animate}"
        auto_labels[1].text = f"walk_clip: '{animated_entity.walk_clip}'"
        auto_labels[2].text = f"idle_clip: '{animated_entity.idle_clip}'"

# Key handler
def on_key(key, state):
    if state != mcrfpy.InputState.PRESSED:
        return

    if animated_entity:
        if key == mcrfpy.Key.SPACE:
            animated_entity.anim_paused = not animated_entity.anim_paused
            status.text = f"Status: {'Paused' if animated_entity.anim_paused else 'Playing'}"

        elif key == mcrfpy.Key.L:
            animated_entity.anim_loop = not animated_entity.anim_loop
            status.text = f"Status: Loop {'ON' if animated_entity.anim_loop else 'OFF'}"

        elif key == mcrfpy.Key.EQUAL or key == mcrfpy.Key.ADD:
            animated_entity.anim_speed = min(animated_entity.anim_speed + 0.25, 4.0)
            status.text = f"Status: Speed {animated_entity.anim_speed:.2f}x"

        elif key == mcrfpy.Key.HYPHEN or key == mcrfpy.Key.SUBTRACT:
            animated_entity.anim_speed = max(animated_entity.anim_speed - 0.25, 0.0)
            status.text = f"Status: Speed {animated_entity.anim_speed:.2f}x"

        elif key == mcrfpy.Key.R:
            animated_entity.anim_time = 0.0
            status.text = "Status: Animation reset"

    # Camera presets
    if key == mcrfpy.Key.NUM_1:
        pos, target, name = camera_presets[0]
        viewport.camera_pos = pos
        viewport.camera_target = target
        status.text = f"Camera: {name}"

    elif key == mcrfpy.Key.NUM_2:
        pos, target, name = camera_presets[1]
        viewport.camera_pos = pos
        viewport.camera_target = target
        status.text = f"Camera: {name}"

    elif key == mcrfpy.Key.NUM_3:
        pos, target, name = camera_presets[2]
        viewport.camera_pos = pos
        viewport.camera_target = target
        status.text = f"Camera: {name}"

    elif key == mcrfpy.Key.ESCAPE:
        mcrfpy.exit()

# Set up scene
scene.on_key = on_key

# Create timer for updates
timer = mcrfpy.Timer("anim_update", update, 16)

# Activate scene
mcrfpy.current_scene = scene

print()
print("Skeletal Animation Demo loaded!")
print("Controls:")
print("  [Space] Toggle pause")
print("  [L] Toggle loop")
print("  [+/-] Adjust speed")
print("  [R] Reset time")
print("  [1-3] Camera presets")
print("  [ESC] Quit")
