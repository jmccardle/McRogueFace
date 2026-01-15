#!/usr/bin/env python3
"""Test for quickstart.md 'Custom Sprite Sheet' example.

Original (DEPRECATED - lines 176-201):
    mcrfpy.createScene("game")
    grid = mcrfpy.Grid(20, 15, my_texture, (10, 10), (640, 480))
    grid.at(5, 5).sprite = 10
    ui = mcrfpy.sceneUI("game")
    mcrfpy.setScene("game")

Modern equivalent below.
"""
import mcrfpy
from mcrfpy import automation
import sys

# Create scene using modern API
scene = mcrfpy.Scene("game")
scene.activate()
mcrfpy.step(0.01)

# Load sprite sheet (using existing texture for test)
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

# Create grid using modern keyword API
grid = mcrfpy.Grid(
    grid_size=(20, 15),
    texture=texture,
    pos=(10, 10),
    size=(640, 480)
)

# Set specific tiles using modern API
# grid.at() returns a GridPoint with tilesprite property
grid.at((5, 5)).tilesprite = 10  # Note: tuple for position
grid.at((6, 5)).tilesprite = 11

# Set walkability
grid.at((6, 5)).walkable = False

# Add grid to scene
scene.children.append(grid)

# Render and screenshot
mcrfpy.step(0.1)
automation.screenshot("/opt/goblincorps/repos/McRogueFace/tests/docs/screenshots/quickstart_sprites.png")

print("PASS - quickstart sprites")
sys.exit(0)
