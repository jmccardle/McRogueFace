# viewport3d_screenshot.py - Quick screenshot of Viewport3D demo
import mcrfpy
from mcrfpy import automation
import sys

print("Script starting...", flush=True)

# Create demo scene
scene = mcrfpy.Scene('viewport3d_demo')
print("Scene created")

# Dark background frame
bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(20, 20, 30))
scene.children.append(bg)

# Title
title = mcrfpy.Caption(text='Viewport3D Demo - PS1-Style 3D Rendering', pos=(20, 10))
title.fill_color = mcrfpy.Color(255, 255, 255)
scene.children.append(title)

# Create the 3D viewport - the main feature!
print("Creating Viewport3D...")
viewport = mcrfpy.Viewport3D(
    pos=(50, 60),
    size=(600, 450),
    render_resolution=(320, 240),
    fov=60.0,
    camera_pos=(5.0, 3.0, 5.0),
    camera_target=(0.0, 0.0, 0.0),
    bg_color=mcrfpy.Color(25, 25, 50)
)
print(f"Viewport3D created: {viewport}")
scene.children.append(viewport)
print("Viewport3D added to scene")

# Info panel on the right
info_panel = mcrfpy.Frame(pos=(670, 60), size=(330, 450),
                          fill_color=mcrfpy.Color(30, 30, 40),
                          outline_color=mcrfpy.Color(80, 80, 100),
                          outline=2.0)
scene.children.append(info_panel)

# Panel title
panel_title = mcrfpy.Caption(text='Viewport Properties', pos=(690, 70))
panel_title.fill_color = mcrfpy.Color(200, 200, 255)
scene.children.append(panel_title)

# Property labels
props = [
    ('Position:', f'({viewport.x}, {viewport.y})'),
    ('Size:', f'{viewport.w}x{viewport.h}'),
    ('Render Res:', f'{viewport.render_resolution[0]}x{viewport.render_resolution[1]}'),
    ('FOV:', f'{viewport.fov} degrees'),
    ('Camera Pos:', f'({viewport.camera_pos[0]:.1f}, {viewport.camera_pos[1]:.1f}, {viewport.camera_pos[2]:.1f})'),
    ('Camera Target:', f'({viewport.camera_target[0]:.1f}, {viewport.camera_target[1]:.1f}, {viewport.camera_target[2]:.1f})'),
    ('', ''),
    ('PS1 Effects:', ''),
    ('  Vertex Snap:', 'ON' if viewport.enable_vertex_snap else 'OFF'),
    ('  Affine Map:', 'ON' if viewport.enable_affine else 'OFF'),
    ('  Dithering:', 'ON' if viewport.enable_dither else 'OFF'),
    ('  Fog:', 'ON' if viewport.enable_fog else 'OFF'),
    ('  Fog Range:', f'{viewport.fog_near} - {viewport.fog_far}'),
]

y_offset = 100
for label, value in props:
    if label:
        cap = mcrfpy.Caption(text=f'{label} {value}', pos=(690, y_offset))
        cap.fill_color = mcrfpy.Color(180, 180, 200)
        scene.children.append(cap)
    y_offset += 22

# Instructions at bottom
instructions = mcrfpy.Caption(
    text='[1-4] Toggle PS1 effects | [WASD] Move camera | [Q/E] Camera height | [ESC] Quit',
    pos=(20, 530)
)
instructions.fill_color = mcrfpy.Color(150, 150, 150)
scene.children.append(instructions)

# Status line
status = mcrfpy.Caption(text='Status: Viewport3D ready (placeholder mode - GL shaders pending)', pos=(20, 555))
status.fill_color = mcrfpy.Color(100, 200, 100)
scene.children.append(status)

scene.activate()

def take_screenshot(timer, runtime):
    print(f'Timer callback fired at runtime: {runtime}')
    automation.screenshot('viewport3d_demo.png')
    print('Screenshot saved to viewport3d_demo.png')
    sys.exit(0)

print('Setting up screenshot timer...')
mcrfpy.Timer('screenshot', take_screenshot, 500, once=True)
print('Timer set, entering game loop...')
