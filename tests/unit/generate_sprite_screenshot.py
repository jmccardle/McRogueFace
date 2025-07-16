#!/usr/bin/env python3
"""Generate sprite documentation screenshots for McRogueFace"""

import mcrfpy
from mcrfpy import automation
import sys

def capture_sprites(runtime):
    """Capture sprite examples after render loop starts"""
    
    # Take screenshot
    automation.screenshot("mcrogueface.github.io/images/ui_sprite_example.png")
    print("Sprite screenshot saved!")
    
    # Exit after capturing
    sys.exit(0)

# Create scene
mcrfpy.createScene("sprites")

# Load texture
texture = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16)

# Title
title = mcrfpy.Caption(400, 30, "Sprite Examples")
title.font = mcrfpy.default_font
title.font_size = 24
title.font_color = (255, 255, 255)

# Create a frame background
frame = mcrfpy.Frame(50, 80, 700, 500)
frame.bgcolor = (64, 64, 128)
frame.outline = 2

# Player sprite
player_label = mcrfpy.Caption(100, 120, "Player")
player_label.font = mcrfpy.default_font
player_label.font_color = (255, 255, 255)

player = mcrfpy.Sprite(120, 150)
player.texture = texture
player.sprite_index = 84  # Player sprite
player.scale = (3.0, 3.0)

# Enemy sprites
enemy_label = mcrfpy.Caption(250, 120, "Enemies")
enemy_label.font = mcrfpy.default_font
enemy_label.font_color = (255, 255, 255)

rat = mcrfpy.Sprite(250, 150)
rat.texture = texture
rat.sprite_index = 123  # Rat
rat.scale = (3.0, 3.0)

big_rat = mcrfpy.Sprite(320, 150)
big_rat.texture = texture
big_rat.sprite_index = 130  # Big rat
big_rat.scale = (3.0, 3.0)

cyclops = mcrfpy.Sprite(390, 150)
cyclops.texture = texture
cyclops.sprite_index = 109  # Cyclops
cyclops.scale = (3.0, 3.0)

# Items row
items_label = mcrfpy.Caption(100, 250, "Items")
items_label.font = mcrfpy.default_font
items_label.font_color = (255, 255, 255)

# Boulder
boulder = mcrfpy.Sprite(100, 280)
boulder.texture = texture
boulder.sprite_index = 66  # Boulder
boulder.scale = (3.0, 3.0)

# Chest
chest = mcrfpy.Sprite(170, 280)
chest.texture = texture
chest.sprite_index = 89  # Closed chest
chest.scale = (3.0, 3.0)

# Key
key = mcrfpy.Sprite(240, 280)
key.texture = texture
key.sprite_index = 384  # Key
key.scale = (3.0, 3.0)

# Button
button = mcrfpy.Sprite(310, 280)
button.texture = texture
button.sprite_index = 250  # Button
button.scale = (3.0, 3.0)

# UI elements row
ui_label = mcrfpy.Caption(100, 380, "UI Elements")
ui_label.font = mcrfpy.default_font
ui_label.font_color = (255, 255, 255)

# Hearts
heart_full = mcrfpy.Sprite(100, 410)
heart_full.texture = texture
heart_full.sprite_index = 210  # Full heart
heart_full.scale = (3.0, 3.0)

heart_half = mcrfpy.Sprite(170, 410)
heart_half.texture = texture
heart_half.sprite_index = 209  # Half heart
heart_half.scale = (3.0, 3.0)

heart_empty = mcrfpy.Sprite(240, 410)
heart_empty.texture = texture
heart_empty.sprite_index = 208  # Empty heart
heart_empty.scale = (3.0, 3.0)

# Armor
armor = mcrfpy.Sprite(340, 410)
armor.texture = texture
armor.sprite_index = 211  # Armor
armor.scale = (3.0, 3.0)

# Scale demonstration
scale_label = mcrfpy.Caption(500, 120, "Scale Demo")
scale_label.font = mcrfpy.default_font
scale_label.font_color = (255, 255, 255)

# Same sprite at different scales
for i, scale in enumerate([1.0, 2.0, 3.0, 4.0]):
    s = mcrfpy.Sprite(500 + i * 60, 150)
    s.texture = texture
    s.sprite_index = 84  # Player
    s.scale = (scale, scale)
    mcrfpy.sceneUI("sprites").append(s)

# Add all elements to scene
ui = mcrfpy.sceneUI("sprites")
ui.append(frame)
ui.append(title)
ui.append(player_label)
ui.append(player)
ui.append(enemy_label)
ui.append(rat)
ui.append(big_rat)
ui.append(cyclops)
ui.append(items_label)
ui.append(boulder)
ui.append(chest)
ui.append(key)
ui.append(button)
ui.append(ui_label)
ui.append(heart_full)
ui.append(heart_half)
ui.append(heart_empty)
ui.append(armor)
ui.append(scale_label)

# Switch to scene
mcrfpy.setScene("sprites")

# Set timer to capture after rendering starts
mcrfpy.setTimer("capture", capture_sprites, 100)