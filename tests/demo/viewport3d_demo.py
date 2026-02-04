# viewport3d_demo.py - Visual demo of Viewport3D integration
# Shows the 3D viewport as a UIDrawable alongside 2D elements

import mcrfpy
import sys
import math

# Create demo scene
scene = mcrfpy.Scene("viewport3d_demo")

# Dark background frame
bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(20, 20, 30))
scene.children.append(bg)

# Title
title = mcrfpy.Caption(text="Viewport3D Demo - PS1-Style 3D Rendering", pos=(20, 10))
title.fill_color = mcrfpy.Color(255, 255, 255)
scene.children.append(title)

# Create the 3D viewport - this is the star of the show!
viewport = mcrfpy.Viewport3D(
    pos=(50, 60),
    size=(600, 450),
    render_resolution=(320, 240),  # PS1 resolution for that retro look
    fov=60.0,
    camera_pos=(5.0, 3.0, 5.0),
    camera_target=(0.0, 0.0, 0.0),
    bg_color=mcrfpy.Color(25, 25, 50)  # Dark blue background
)
scene.children.append(viewport)

# Info panel on the right
info_panel = mcrfpy.Frame(pos=(670, 60), size=(330, 450),
                          fill_color=mcrfpy.Color(30, 30, 40),
                          outline_color=mcrfpy.Color(80, 80, 100),
                          outline=2.0)
scene.children.append(info_panel)

# Panel title
panel_title = mcrfpy.Caption(text="Viewport Properties", pos=(690, 70))
panel_title.fill_color = mcrfpy.Color(200, 200, 255)
scene.children.append(panel_title)

# Property labels
props = [
    ("Position:", f"({viewport.x}, {viewport.y})"),
    ("Size:", f"{viewport.w}x{viewport.h}"),
    ("Render Res:", f"{viewport.render_resolution[0]}x{viewport.render_resolution[1]}"),
    ("FOV:", f"{viewport.fov} degrees"),
    ("Camera Pos:", f"({viewport.camera_pos[0]:.1f}, {viewport.camera_pos[1]:.1f}, {viewport.camera_pos[2]:.1f})"),
    ("Camera Target:", f"({viewport.camera_target[0]:.1f}, {viewport.camera_target[1]:.1f}, {viewport.camera_target[2]:.1f})"),
    ("", ""),
    ("PS1 Effects:", ""),
    ("  Vertex Snap:", "ON" if viewport.enable_vertex_snap else "OFF"),
    ("  Affine Map:", "ON" if viewport.enable_affine else "OFF"),
    ("  Dithering:", "ON" if viewport.enable_dither else "OFF"),
    ("  Fog:", "ON" if viewport.enable_fog else "OFF"),
    ("  Fog Range:", f"{viewport.fog_near} - {viewport.fog_far}"),
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
    text="[1-4] Toggle PS1 effects | [WASD] Move camera | [Q/E] Camera height | [ESC] Quit",
    pos=(20, 530)
)
instructions.fill_color = mcrfpy.Color(150, 150, 150)
scene.children.append(instructions)

# Status line
status = mcrfpy.Caption(text="Status: Viewport3D rendering PS1-style 3D cube", pos=(20, 555))
status.fill_color = mcrfpy.Color(100, 200, 100)
scene.children.append(status)

# Animation state
animation_time = [0.0]
camera_orbit = [True]

# Camera orbit animation
def update_camera(timer, runtime):
    animation_time[0] += runtime / 1000.0

    if camera_orbit[0]:
        # Orbit camera around origin
        angle = animation_time[0] * 0.5  # Slow rotation
        radius = 7.0
        height = 4.0 + math.sin(animation_time[0] * 0.3) * 2.0

        x = math.cos(angle) * radius
        z = math.sin(angle) * radius

        viewport.camera_pos = (x, height, z)

# Key handler
def on_key(key, state):
    if state != mcrfpy.InputState.PRESSED:
        return

    key_name = str(key)

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

    # Camera controls
    elif key == mcrfpy.Key.SPACE:
        camera_orbit[0] = not camera_orbit[0]
        status.text = f"Camera orbit: {'ON' if camera_orbit[0] else 'OFF (manual control)'}"

    elif key == mcrfpy.Key.ESCAPE:
        mcrfpy.exit()

    # Manual camera movement (when orbit is off)
    if not camera_orbit[0]:
        pos = list(viewport.camera_pos)
        speed = 0.5

        if key == mcrfpy.Key.W:
            pos[2] -= speed
        elif key == mcrfpy.Key.S:
            pos[2] += speed
        elif key == mcrfpy.Key.A:
            pos[0] -= speed
        elif key == mcrfpy.Key.D:
            pos[0] += speed
        elif key == mcrfpy.Key.Q:
            pos[1] -= speed
        elif key == mcrfpy.Key.E:
            pos[1] += speed

        viewport.camera_pos = tuple(pos)
        status.text = f"Camera: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})"

# Set up scene
scene.on_key = on_key

# Create timer for camera animation
timer = mcrfpy.Timer("camera_update", update_camera, 16)  # ~60fps

# Activate scene
mcrfpy.current_scene = scene

print("Viewport3D Demo loaded!")
print("3D rendering enabled - spinning colored cube should be visible.")
print()
print("Controls:")
print("  [1-4] Toggle PS1 effects")
print("  [Space] Toggle camera orbit")
print("  [WASD/QE] Manual camera control (when orbit off)")
print("  [ESC] Quit")
