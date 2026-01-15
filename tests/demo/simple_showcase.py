#!/usr/bin/env python3
"""
Simple Tutorial Screenshot Generator

This creates ONE screenshot - the part01 tutorial showcase.
Run with: xvfb-run -a ./build/mcrogueface --headless --exec tests/demo/simple_showcase.py

NOTE: In headless mode, automation.screenshot() is SYNCHRONOUS - it renders
and captures immediately. No timer dance needed!
"""
import mcrfpy
from mcrfpy import automation
import sys
import os

# Output
OUTPUT_PATH = "/opt/goblincorps/repos/mcrogueface.github.io/images/tutorials/part_01_grid_movement.png"

# Tile sprites from the labeled tileset
PLAYER_KNIGHT = 84
FLOOR_STONE = 42
WALL_STONE = 30
TORCH = 72
BARREL = 73
SKULL = 74

def main():
    """Create the part01 showcase screenshot."""
    # Ensure output dir exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Create scene
    scene = mcrfpy.Scene("showcase")

    # Load texture
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

    # Create grid - bigger zoom for visibility
    grid = mcrfpy.Grid(
        pos=(50, 80),
        size=(700, 480),
        grid_size=(12, 9),
        texture=texture,
        zoom=3.5
    )
    grid.fill_color = mcrfpy.Color(20, 20, 30)
    scene.children.append(grid)

    # Fill with floor
    for y in range(9):
        for x in range(12):
            grid.at(x, y).tilesprite = FLOOR_STONE

    # Add wall border
    for x in range(12):
        grid.at(x, 0).tilesprite = WALL_STONE
        grid.at(x, 0).walkable = False
        grid.at(x, 8).tilesprite = WALL_STONE
        grid.at(x, 8).walkable = False
    for y in range(9):
        grid.at(0, y).tilesprite = WALL_STONE
        grid.at(0, y).walkable = False
        grid.at(11, y).tilesprite = WALL_STONE
        grid.at(11, y).walkable = False

    # Add player entity - a knight!
    player = mcrfpy.Entity(
        grid_pos=(6, 4),
        texture=texture,
        sprite_index=PLAYER_KNIGHT
    )
    grid.entities.append(player)

    # Add decorations
    for pos, sprite in [((2, 2), TORCH), ((9, 2), TORCH), ((2, 6), BARREL), ((9, 6), SKULL)]:
        entity = mcrfpy.Entity(grid_pos=pos, texture=texture, sprite_index=sprite)
        grid.entities.append(entity)

    # Center camera on player
    grid.center = (6 * 16 + 8, 4 * 16 + 8)

    # Add title
    title = mcrfpy.Caption(text="Part 1: The '@' and the Dungeon Grid", pos=(50, 20))
    title.fill_color = mcrfpy.Color(255, 255, 255)
    title.font_size = 28
    scene.children.append(title)

    subtitle = mcrfpy.Caption(text="Creating a grid, placing entities, handling input", pos=(50, 50))
    subtitle.fill_color = mcrfpy.Color(180, 180, 200)
    subtitle.font_size = 16
    scene.children.append(subtitle)

    # Activate scene
    scene.activate()

    # In headless mode, screenshot() is synchronous - renders then captures!
    result = automation.screenshot(OUTPUT_PATH)
    print(f"Screenshot saved: {OUTPUT_PATH} (result: {result})")
    sys.exit(0)


# Run it
main()
