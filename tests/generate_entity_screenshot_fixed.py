#!/usr/bin/env python3
"""Generate entity documentation screenshot with proper font loading"""

import mcrfpy
from mcrfpy import automation
import sys

def capture_entity(runtime):
    """Capture entity example after render loop starts"""
    
    # Take screenshot
    automation.screenshot("mcrogueface.github.io/images/ui_entity_example.png")
    print("Entity screenshot saved!")
    
    # Exit after capturing
    sys.exit(0)

# Create scene
mcrfpy.createScene("entities")

# Use the default font which is already loaded
# Instead of: font = mcrfpy.Font("assets/JetbrainsMono.ttf")
# We use: mcrfpy.default_font (which is already loaded by the engine)

# Title
title = mcrfpy.Caption((400, 30), "Entity Example - Roguelike Characters", font=mcrfpy.default_font)
#title.font = mcrfpy.default_font
#title.font_size = 24
title.size=24
#title.font_color = (255, 255, 255)
#title.text_color = (255,255,255)

# Create a grid background
texture = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16)

# Create grid with entities - using 2x scale (32x32 pixel tiles)
#grid = mcrfpy.Grid((100, 100), (20, 15), texture, 16, 16) # I can never get the args right for this thing
t = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16)
grid = mcrfpy.Grid(20, 15, t, (10, 10), (1014, 758))
grid.zoom = 2.0
#grid.texture = texture

# Define tile types
FLOOR = 58      # Stone floor
WALL = 11       # Stone wall

# Fill with floor
for x in range(20):
    for y in range(15):
        grid.at((x, y)).tilesprite = WALL

# Add walls around edges
for x in range(20):
    grid.at((x, 0)).tilesprite = WALL
    grid.at((x, 14)).tilesprite = WALL
for y in range(15):
    grid.at((0, y)).tilesprite = WALL
    grid.at((19, y)).tilesprite = WALL

# Create entities
# Player at center
player = mcrfpy.Entity((10, 7), t, 84)
#player.texture = texture
#player.sprite_index = 84  # Player sprite

# Enemies
rat1 = mcrfpy.Entity((5, 5), t, 123)
#rat1.texture = texture
#rat1.sprite_index = 123  # Rat

rat2 = mcrfpy.Entity((15, 5), t, 123)
#rat2.texture = texture  
#rat2.sprite_index = 123  # Rat

big_rat = mcrfpy.Entity((7, 10), t, 130)
#big_rat.texture = texture
#big_rat.sprite_index = 130  # Big rat

cyclops = mcrfpy.Entity((13, 10), t, 109)
#cyclops.texture = texture
#cyclops.sprite_index = 109  # Cyclops

# Items
chest = mcrfpy.Entity((3, 3), t, 89)
#chest.texture = texture
#chest.sprite_index = 89  # Chest

boulder = mcrfpy.Entity((10, 5), t, 66)
#boulder.texture = texture
#boulder.sprite_index = 66  # Boulder
key = mcrfpy.Entity((17, 12), t, 384)
#key.texture = texture
#key.sprite_index = 384  # Key

# Add all entities to grid
grid.entities.append(player)
grid.entities.append(rat1)
grid.entities.append(rat2)
grid.entities.append(big_rat)
grid.entities.append(cyclops)
grid.entities.append(chest)
grid.entities.append(boulder)
grid.entities.append(key)

# Labels
entity_label = mcrfpy.Caption((100, 580), "Entities move independently on the grid. Grid scale: 2x (32x32 pixels)")
#entity_label.font = mcrfpy.default_font
#entity_label.font_color = (255, 255, 255)

info = mcrfpy.Caption((100, 600), "Player (center), Enemies (rats, cyclops), Items (chest, boulder, key)")
#info.font = mcrfpy.default_font
#info.font_size = 14
#info.font_color = (200, 200, 200)

# Legend frame
legend_frame = mcrfpy.Frame(50, 50, 200, 150)
#legend_frame.bgcolor = (64, 64, 128)
#legend_frame.outline = 2

legend_title = mcrfpy.Caption((150, 60), "Entity Types")
#legend_title.font = mcrfpy.default_font
#legend_title.font_color = (255, 255, 255)
#legend_title.centered = True

#legend_text = mcrfpy.Caption((60, 90), "Player: @\nRat: r\nBig Rat: R\nCyclops: C\nChest: $\nBoulder: O\nKey: k")
#legend_text.font = mcrfpy.default_font
#legend_text.font_size = 12
#legend_text.font_color = (255, 255, 255)

# Add all to scene
ui = mcrfpy.sceneUI("entities")
ui.append(grid)
ui.append(title)
ui.append(entity_label)
ui.append(info)
ui.append(legend_frame)
ui.append(legend_title)
#ui.append(legend_text)

# Switch to scene
mcrfpy.setScene("entities")

# Set timer to capture after rendering starts
mcrfpy.setTimer("capture", capture_entity, 100)
