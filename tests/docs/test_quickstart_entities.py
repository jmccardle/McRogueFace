#!/usr/bin/env python3
"""Test for quickstart.md 'Game Entity' example.

Original (DEPRECATED - lines 133-168):
    mcrfpy.createScene("game")
    grid = mcrfpy.Grid(20, 15, texture, (10, 10), (640, 480))
    ui = mcrfpy.sceneUI("game")
    player = mcrfpy.Entity((10, 7), texture, 85)
    mcrfpy.keypressScene(handle_keys)
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

# Load texture
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

# Create grid using modern keyword API
grid = mcrfpy.Grid(
    grid_size=(20, 15),
    texture=texture,
    pos=(10, 10),
    size=(640, 480)
)
scene.children.append(grid)

# Add player entity
player = mcrfpy.Entity(grid_pos=(10, 7), texture=texture, sprite_index=85)
grid.entities.append(player)

# Add NPC entity
npc = mcrfpy.Entity(grid_pos=(5, 5), texture=texture, sprite_index=109)
grid.entities.append(npc)

# Add treasure chest
treasure = mcrfpy.Entity(grid_pos=(15, 10), texture=texture, sprite_index=89)
grid.entities.append(treasure)

# Movement handler using modern API
def handle_keys(key, state):
    if state == "start":
        x, y = player.pos[0], player.pos[1]
        if key == "W":
            player.pos = (x, y - 1)
        elif key == "S":
            player.pos = (x, y + 1)
        elif key == "A":
            player.pos = (x - 1, y)
        elif key == "D":
            player.pos = (x + 1, y)

scene.on_key = handle_keys

# Center grid on player
grid.center = (10, 7)

# Render and screenshot
mcrfpy.step(0.1)
automation.screenshot("/opt/goblincorps/repos/McRogueFace/tests/docs/screenshots/quickstart_entities.png")

print("PASS - quickstart entities")
sys.exit(0)
