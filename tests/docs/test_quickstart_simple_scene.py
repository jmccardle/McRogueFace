#!/usr/bin/env python3
"""Test for quickstart.md 'Simple Test Scene' example.

Original (DEPRECATED - lines 48-74):
    mcrfpy.createScene("test")
    grid = mcrfpy.Grid(20, 15, texture, (10, 10), (800, 600))
    ui = mcrfpy.sceneUI("test")
    mcrfpy.setScene("test")
    mcrfpy.keypressScene(move_around)

Modern equivalent below.
"""
import mcrfpy
from mcrfpy import automation
import sys

# Create scene using modern API
scene = mcrfpy.Scene("test")
scene.activate()
mcrfpy.step(0.01)  # Initialize

# Load texture
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

# Create grid using modern keyword API
grid = mcrfpy.Grid(
    grid_size=(20, 15),
    texture=texture,
    pos=(10, 10),
    size=(800, 600)
)

# Add to scene's children (not sceneUI)
scene.children.append(grid)

# Add keyboard controls using modern API
def move_around(key, state):
    if state == "start":
        print(f"You pressed {key}")

scene.on_key = move_around

# Render and screenshot
mcrfpy.step(0.1)
automation.screenshot("/opt/goblincorps/repos/McRogueFace/tests/docs/screenshots/quickstart_simple_scene.png")

print("PASS - quickstart simple scene")
sys.exit(0)
