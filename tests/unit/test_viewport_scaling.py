#!/usr/bin/env python3
"""Test viewport scaling modes"""

import mcrfpy
from mcrfpy import Window, Frame, Caption, Color, Vector
from mcrfpy import automation
import sys

print("Creating viewport test scene...")
test = mcrfpy.Scene("test")
mcrfpy.current_scene = test

print("Testing viewport scaling modes...")

# Get window singleton
window = Window.get()

# Test initial state
print(f"Initial game resolution: {window.game_resolution}")
print(f"Initial scaling mode: {window.scaling_mode}")
print(f"Window resolution: {window.resolution}")

# Create test scene with visual elements
scene = test.children

# Create a frame that fills the game resolution to show boundaries
game_res = window.game_resolution
boundary = Frame(pos=(0, 0), size=(game_res[0], game_res[1]),
                fill_color=Color(50, 50, 100),
                outline_color=Color(255, 255, 255),
                outline=2)
boundary.name = "boundary"
scene.append(boundary)

# Add corner markers
corner_size = 50
corners = [
    (0, 0, "TL"),  # Top-left
    (game_res[0] - corner_size, 0, "TR"),  # Top-right
    (0, game_res[1] - corner_size, "BL"),  # Bottom-left
    (game_res[0] - corner_size, game_res[1] - corner_size, "BR")  # Bottom-right
]

for x, y, label in corners:
    corner = Frame(pos=(x, y), size=(corner_size, corner_size),
                  fill_color=Color(255, 100, 100),
                  outline_color=Color(255, 255, 255),
                  outline=1)
    scene.append(corner)

    text = Caption(text=label, pos=(x + 5, y + 5))
    text.font_size = 20
    text.fill_color = Color(255, 255, 255)
    scene.append(text)

# Add center crosshair
center_x = game_res[0] // 2
center_y = game_res[1] // 2
h_line = Frame(pos=(center_x - 50, center_y - 1), size=(100, 2),
              fill_color=Color(255, 255, 0))
v_line = Frame(pos=(center_x - 1, center_y - 50), size=(2, 100),
              fill_color=Color(255, 255, 0))
scene.append(h_line)
scene.append(v_line)

# Add mode indicator
mode_text = Caption(text=f"Mode: {window.scaling_mode}", pos=(10, 10))
mode_text.font_size = 24
mode_text.fill_color = Color(255, 255, 255)
mode_text.name = "mode_text"
scene.append(mode_text)

# Render initial frame
mcrfpy.step(0.01)

print("\nTesting scaling modes:")

# Test center mode
window.scaling_mode = "center"
print(f"Set to center mode: {window.scaling_mode}")
mode_text.text = f"Mode: center (1:1 pixels)"
mcrfpy.step(0.01)
automation.screenshot("viewport_center_mode.png")

# Test stretch mode
window.scaling_mode = "stretch"
print(f"Set to stretch mode: {window.scaling_mode}")
mode_text.text = f"Mode: stretch (fill window)"
mcrfpy.step(0.01)
automation.screenshot("viewport_stretch_mode.png")

# Test fit mode
window.scaling_mode = "fit"
print(f"Set to fit mode: {window.scaling_mode}")
mode_text.text = f"Mode: fit (aspect ratio maintained)"
mcrfpy.step(0.01)
automation.screenshot("viewport_fit_mode.png")

# Test window resize (may fail in headless mode)
print("\nTesting window resize with fit mode:")
try:
    window.resolution = (1280, 720)
    print(f"Window resized to: {window.resolution}")
    mcrfpy.step(0.01)
    automation.screenshot("viewport_fit_wide.png")

    try:
        window.resolution = (800, 1000)
        print(f"Window resized to: {window.resolution}")
        mcrfpy.step(0.01)
        automation.screenshot("viewport_fit_tall.png")
    except RuntimeError as e:
        print(f"  Skipping tall window test (headless mode): {e}")
except RuntimeError as e:
    print(f"  Skipping window resize tests (headless mode): {e}")

# Test game resolution change
print("\nTesting game resolution change:")
window.game_resolution = (800, 600)
print(f"Game resolution changed to: {window.game_resolution}")

print("\nTest completed!")
print("Screenshots saved:")
print("  - viewport_center_mode.png")
print("  - viewport_stretch_mode.png")
print("  - viewport_fit_mode.png")
print("  - viewport_fit_wide.png")
print("  - viewport_fit_tall.png")

# Restore original settings
try:
    window.resolution = (1024, 768)
except RuntimeError:
    pass  # Headless mode - can't change resolution
window.game_resolution = (1024, 768)
window.scaling_mode = "fit"

sys.exit(0)
