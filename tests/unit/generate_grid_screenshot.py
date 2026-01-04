#!/usr/bin/env python3
"""Generate grid documentation screenshot for McRogueFace"""

import mcrfpy
from mcrfpy import automation
import sys

def capture_grid(timer, runtime):
    """Capture grid example after render loop starts"""

    # Take screenshot
    automation.screenshot("mcrogueface.github.io/images/ui_grid_example.png")
    print("Grid screenshot saved!")

    # Exit after capturing
    sys.exit(0)

# Create scene
grid = mcrfpy.Scene("grid")

# Load texture
texture = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16)

# Title
title = mcrfpy.Caption(pos=(400, 30), text="Grid Example - Dungeon View")
title.font = mcrfpy.default_font
title.font_size = 24
title.fill_color = mcrfpy.Color(255, 255, 255)

# Create main grid (20x15 tiles, each 32x32 pixels)
grid = mcrfpy.Grid(pos=(100, 100), grid_size=(20, 15), texture=texture, size=(640, 480))

# Define tile types from Crypt of Sokoban
FLOOR = 58      # Stone floor
WALL = 11       # Stone wall
DOOR = 28       # Closed door
CHEST = 89      # Treasure chest
BUTTON = 250    # Floor button
EXIT = 45       # Locked exit
BOULDER = 66    # Boulder

# Create a simple dungeon room layout
# Fill with walls first
for x in range(20):
    for y in range(15):
        grid.set_tile(x, y, WALL)

# Carve out room
for x in range(2, 18):
    for y in range(2, 13):
        grid.set_tile(x, y, FLOOR)

# Add door
grid.set_tile(10, 2, DOOR)

# Add some features
grid.set_tile(5, 5, CHEST)
grid.set_tile(15, 10, BUTTON)
grid.set_tile(10, 12, EXIT)
grid.set_tile(8, 8, BOULDER)
grid.set_tile(12, 8, BOULDER)

# Create some entities on the grid
# Player entity
player = mcrfpy.Entity((5, 7), texture=texture, sprite_index=84, grid=grid)  # Player sprite

# Enemy entities
rat1 = mcrfpy.Entity((12, 5), texture=texture, sprite_index=123, grid=grid)  # Rat

rat2 = mcrfpy.Entity((14, 9), texture=texture, sprite_index=123, grid=grid)  # Rat

cyclops = mcrfpy.Entity((10, 10), texture=texture, sprite_index=109, grid=grid)  # Cyclops

# Create a smaller grid showing tile palette
palette_label = mcrfpy.Caption(pos=(100, 600), text="Tile Types:")
palette_label.font = mcrfpy.default_font
palette_label.fill_color = mcrfpy.Color(255, 255, 255)

palette = mcrfpy.Grid(pos=(250, 580), grid_size=(7, 1), texture=texture, size=(224, 32))
palette.set_tile(0, 0, FLOOR)
palette.set_tile(1, 0, WALL)
palette.set_tile(2, 0, DOOR)
palette.set_tile(3, 0, CHEST)
palette.set_tile(4, 0, BUTTON)
palette.set_tile(5, 0, EXIT)
palette.set_tile(6, 0, BOULDER)

# Labels for palette
labels = ["Floor", "Wall", "Door", "Chest", "Button", "Exit", "Boulder"]
for i, label in enumerate(labels):
    l = mcrfpy.Caption(pos=(250 + i * 32, 615), text=label)
    l.font = mcrfpy.default_font
    l.font_size = 10
    l.fill_color = mcrfpy.Color(255, 255, 255)
    grid.children.append(l)

# Add info caption
info = mcrfpy.Caption(pos=(100, 680), text="Grid supports tiles and entities. Entities can move independently of the tile grid.")
info.font = mcrfpy.default_font
info.font_size = 14
info.fill_color = mcrfpy.Color(200, 200, 200)

# Add all elements to scene
ui = grid.children
ui.append(title)
ui.append(grid)
ui.append(palette_label)
ui.append(palette)
ui.append(info)

# Switch to scene
grid.activate()

# Set timer to capture after rendering starts
capture_timer = mcrfpy.Timer("capture", capture_grid, 100, once=True)