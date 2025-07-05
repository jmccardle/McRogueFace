#!/usr/bin/env python3
"""Generate grid documentation screenshot for McRogueFace"""

import mcrfpy
from mcrfpy import automation
import sys

def capture_grid(runtime):
    """Capture grid example after render loop starts"""
    
    # Take screenshot
    automation.screenshot("mcrogueface.github.io/images/ui_grid_example.png")
    print("Grid screenshot saved!")
    
    # Exit after capturing
    sys.exit(0)

# Create scene
mcrfpy.createScene("grid")

# Load texture
texture = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16)

# Title
title = mcrfpy.Caption(400, 30, "Grid Example - Dungeon View")
title.font = mcrfpy.default_font
title.font_size = 24
title.font_color = (255, 255, 255)

# Create main grid (20x15 tiles, each 32x32 pixels)
grid = mcrfpy.Grid(100, 100, 20, 15, texture, 32, 32)
grid.texture = texture

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
player = mcrfpy.Entity(5, 7)
player.texture = texture
player.sprite_index = 84  # Player sprite

# Enemy entities
rat1 = mcrfpy.Entity(12, 5)
rat1.texture = texture
rat1.sprite_index = 123  # Rat

rat2 = mcrfpy.Entity(14, 9)
rat2.texture = texture
rat2.sprite_index = 123  # Rat

cyclops = mcrfpy.Entity(10, 10)
cyclops.texture = texture
cyclops.sprite_index = 109  # Cyclops

# Add entities to grid
grid.entities.append(player)
grid.entities.append(rat1)
grid.entities.append(rat2)
grid.entities.append(cyclops)

# Create a smaller grid showing tile palette
palette_label = mcrfpy.Caption(100, 600, "Tile Types:")
palette_label.font = mcrfpy.default_font
palette_label.font_color = (255, 255, 255)

palette = mcrfpy.Grid(250, 580, 7, 1, texture, 32, 32)
palette.texture = texture
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
    l = mcrfpy.Caption(250 + i * 32, 615, label)
    l.font = mcrfpy.default_font
    l.font_size = 10
    l.font_color = (255, 255, 255)
    mcrfpy.sceneUI("grid").append(l)

# Add info caption
info = mcrfpy.Caption(100, 680, "Grid supports tiles and entities. Entities can move independently of the tile grid.")
info.font = mcrfpy.default_font
info.font_size = 14
info.font_color = (200, 200, 200)

# Add all elements to scene
ui = mcrfpy.sceneUI("grid")
ui.append(title)
ui.append(grid)
ui.append(palette_label)
ui.append(palette)
ui.append(info)

# Switch to scene
mcrfpy.setScene("grid")

# Set timer to capture after rendering starts
mcrfpy.setTimer("capture", capture_grid, 100)