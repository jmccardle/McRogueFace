# model_loading_demo.py - Visual demo of Model3D model loading
# Shows both procedural primitives and loaded .glb models

import mcrfpy
import sys
import math
import os

# Create demo scene
scene = mcrfpy.Scene("model_loading_demo")

# Dark background frame
bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(15, 15, 25))
scene.children.append(bg)

# Title
title = mcrfpy.Caption(text="Model3D Demo - Procedural & glTF Models", pos=(20, 10))
title.fill_color = mcrfpy.Color(255, 255, 255)
scene.children.append(title)

# Create the 3D viewport
viewport = mcrfpy.Viewport3D(
    pos=(50, 60),
    size=(600, 450),
#    render_resolution=(320, 240),  # PS1 resolution
    render_resolution=(600,450),
    fov=60.0,
    camera_pos=(0.0, 3.0, 8.0),
    camera_target=(0.0, 1.0, 0.0),
    bg_color=mcrfpy.Color(30, 30, 50)
)
scene.children.append(viewport)

# Set up navigation grid
GRID_SIZE = 32
viewport.set_grid_size(GRID_SIZE, GRID_SIZE)

# Build a simple flat floor
hm = mcrfpy.HeightMap((GRID_SIZE, GRID_SIZE))
hm.normalize(0.0, 0.0)
viewport.apply_heightmap(hm, 0.0)
vertex_count = viewport.build_terrain(
    layer_name="floor",
    heightmap=hm,
    y_scale=0.0,
    cell_size=1.0
)

# Apply floor colors (checkerboard pattern)
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

# Create procedural models
print("Creating procedural models...")
cube_model = mcrfpy.Model3D.cube(1.0)
sphere_model = mcrfpy.Model3D.sphere(0.5, 12, 8)

# Try to load glTF models
loaded_models = {}
models_dir = "../assets/models"
if os.path.exists(models_dir):
    for filename in ["Duck.glb", "Box.glb", "Lantern.glb", "WaterBottle.glb"]:
        path = os.path.join(models_dir, filename)
        if os.path.exists(path):
            try:
                model = mcrfpy.Model3D(path)
                loaded_models[filename] = model
                print(f"Loaded {filename}: {model.vertex_count} verts, {model.triangle_count} tris")
            except Exception as e:
                print(f"Failed to load {filename}: {e}")

# Create entities with different models
entities = []

# Row 1: Procedural primitives
entity_configs = [
    ((12, 16), cube_model, 1.0, mcrfpy.Color(255, 100, 100), "Cube"),
    ((16, 16), sphere_model, 1.0, mcrfpy.Color(100, 255, 100), "Sphere"),
    ((20, 16), None, 1.0, mcrfpy.Color(200, 200, 200), "Placeholder"),
]

# Row 2: Loaded glTF models (if available)
if "Duck.glb" in loaded_models:
    # Duck is huge (~160 units), scale it down significantly
    entity_configs.append(((14, 12), loaded_models["Duck.glb"], 0.006, mcrfpy.Color(255, 200, 50), "Duck"))

if "Box.glb" in loaded_models:
    entity_configs.append(((16, 12), loaded_models["Box.glb"], 1.5, mcrfpy.Color(150, 100, 50), "Box (glb)"))

if "Lantern.glb" in loaded_models:
    # Lantern is ~25 units tall
    entity_configs.append(((18, 12), loaded_models["Lantern.glb"], 0.08, mcrfpy.Color(255, 200, 100), "Lantern"))

if "WaterBottle.glb" in loaded_models:
    # WaterBottle is ~0.26 units tall
    entity_configs.append(((20, 12), loaded_models["WaterBottle.glb"], 4.0, mcrfpy.Color(100, 150, 255), "Bottle"))

for pos, model, scale, color, name in entity_configs:
    e = mcrfpy.Entity3D(pos=pos, scale=scale, color=color)
    if model:
        e.model = model
    viewport.entities.append(e)
    entities.append((e, name, model))

print(f"Created {len(entities)} entities")

# Info panel on the right
info_panel = mcrfpy.Frame(pos=(670, 60), size=(330, 450),
                          fill_color=mcrfpy.Color(30, 30, 40),
                          outline_color=mcrfpy.Color(80, 80, 100),
                          outline=2.0)
scene.children.append(info_panel)

# Panel title
panel_title = mcrfpy.Caption(text="Model Information", pos=(690, 70))
panel_title.fill_color = mcrfpy.Color(200, 200, 255)
scene.children.append(panel_title)

# Model info labels
y_offset = 100
for e, name, model in entities:
    if model:
        info = f"{name}: {model.vertex_count}v, {model.triangle_count}t"
    else:
        info = f"{name}: Placeholder (36v, 12t)"
    label = mcrfpy.Caption(text=info, pos=(690, y_offset))
    label.fill_color = e.color
    scene.children.append(label)
    y_offset += 22

# Separator
y_offset += 10
sep = mcrfpy.Caption(text="--- glTF Support ---", pos=(690, y_offset))
sep.fill_color = mcrfpy.Color(150, 150, 150)
scene.children.append(sep)
y_offset += 22

# glTF info
gltf_info = [
    "Format: glTF 2.0 (.glb, .gltf)",
    "Library: cgltf (C99)",
    f"Loaded models: {len(loaded_models)}",
]
for info in gltf_info:
    label = mcrfpy.Caption(text=info, pos=(690, y_offset))
    label.fill_color = mcrfpy.Color(150, 150, 170)
    scene.children.append(label)
    y_offset += 20

# Instructions at bottom
instructions = mcrfpy.Caption(
    text="[Space] Toggle rotation | [1-3] Camera presets | [ESC] Quit",
    pos=(20, 530)
)
instructions.fill_color = mcrfpy.Color(150, 150, 150)
scene.children.append(instructions)

# Status line
status = mcrfpy.Caption(text="Status: Showing procedural and glTF models", pos=(20, 555))
status.fill_color = mcrfpy.Color(100, 200, 100)
scene.children.append(status)

# Animation state
animation_time = [0.0]
rotate_entities = [True]

# Camera presets
camera_presets = [
    ((0.0, 5.0, 12.0), (0.0, 1.0, 0.0), "Front view"),
    ((12.0, 8.0, 0.0), (0.0, 1.0, 0.0), "Side view"),
    ((0.0, 15.0, 0.1), (0.0, 0.0, 0.0), "Top-down view"),
]
current_preset = [0]

# Update function
def update(timer, runtime):
    animation_time[0] += runtime / 1000.0

    if rotate_entities[0]:
        for i, (e, name, model) in enumerate(entities):
            e.rotation = (animation_time[0] * 30.0 + i * 45.0) % 360.0

# Key handler
def on_key(key, state):
    if state != mcrfpy.InputState.PRESSED:
        return

    if key == mcrfpy.Key.SPACE:
        rotate_entities[0] = not rotate_entities[0]
        status.text = f"Rotation: {'ON' if rotate_entities[0] else 'OFF'}"

    elif key == mcrfpy.Key.NUM_1:
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
timer = mcrfpy.Timer("model_update", update, 16)

# Activate scene
mcrfpy.current_scene = scene

print()
print("Model3D Demo loaded!")
print(f"Procedural models: cube, sphere")
print(f"glTF models loaded: {list(loaded_models.keys())}")
print()
print("Controls:")
print("  [Space] Toggle rotation")
print("  [1-3] Camera presets")
print("  [ESC] Quit")
