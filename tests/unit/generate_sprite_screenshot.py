#!/usr/bin/env python3
"""Generate sprite documentation screenshots for McRogueFace"""

import mcrfpy
from mcrfpy import automation
import os
import sys

SCREENSHOT = "ui_sprite_example.png"

results = []

def check(label, condition):
    results.append((label, bool(condition)))
    print(f"{'PASS' if condition else 'FAIL'}: {label}")

def capture_sprites(timer, runtime):
    """Capture sprite examples once the timer fires"""

    # Take screenshot (rendering is on-demand in headless: screenshot forces a render)
    automation.screenshot(SCREENSHOT)
    print("Sprite screenshot saved!")

    check("screenshot file created", os.path.exists(SCREENSHOT))
    check("screenshot is non-empty", os.path.exists(SCREENSHOT) and os.path.getsize(SCREENSHOT) > 0)

# Create scene
sprites = mcrfpy.Scene("sprites")

# Load texture
texture = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16)

# Title (Caption.font is read-only: pass it to the constructor)
title = mcrfpy.Caption(pos=(400, 30), font=mcrfpy.default_font, text="Sprite Examples")
title.font_size = 24
title.fill_color = mcrfpy.Color(255, 255, 255)

# Create a frame background
frame = mcrfpy.Frame(pos=(50, 80), size=(700, 500))
frame.fill_color = mcrfpy.Color(64, 64, 128)
frame.outline = 2

# Player sprite
player_label = mcrfpy.Caption(pos=(100, 120), font=mcrfpy.default_font, text="Player")
player_label.fill_color = mcrfpy.Color(255, 255, 255)

player = mcrfpy.Sprite(pos=(120, 150), texture=texture, sprite_index=84)  # Player sprite
player.scale = 3.0

# Enemy sprites
enemy_label = mcrfpy.Caption(pos=(250, 120), font=mcrfpy.default_font, text="Enemies")
enemy_label.fill_color = mcrfpy.Color(255, 255, 255)

rat = mcrfpy.Sprite(pos=(250, 150), texture=texture, sprite_index=123)  # Rat
rat.scale = 3.0

big_rat = mcrfpy.Sprite(pos=(320, 150), texture=texture, sprite_index=130)  # Big rat
big_rat.scale = 3.0

cyclops = mcrfpy.Sprite(pos=(390, 150), texture=texture, sprite_index=109)  # Cyclops
cyclops.scale = 3.0

# Items row
items_label = mcrfpy.Caption(pos=(100, 250), font=mcrfpy.default_font, text="Items")
items_label.fill_color = mcrfpy.Color(255, 255, 255)

# Boulder
boulder = mcrfpy.Sprite(pos=(100, 280), texture=texture, sprite_index=66)  # Boulder
boulder.scale = 3.0

# Chest
chest = mcrfpy.Sprite(pos=(170, 280), texture=texture, sprite_index=89)  # Closed chest
chest.scale = 3.0

# Key
key = mcrfpy.Sprite(pos=(240, 280), texture=texture, sprite_index=384)  # Key
key.scale = 3.0

# Button
button = mcrfpy.Sprite(pos=(310, 280), texture=texture, sprite_index=250)  # Button
button.scale = 3.0

# UI elements row
ui_label = mcrfpy.Caption(pos=(100, 380), font=mcrfpy.default_font, text="UI Elements")
ui_label.fill_color = mcrfpy.Color(255, 255, 255)

# Hearts
heart_full = mcrfpy.Sprite(pos=(100, 410), texture=texture, sprite_index=210)  # Full heart
heart_full.scale = 3.0

heart_half = mcrfpy.Sprite(pos=(170, 410), texture=texture, sprite_index=209)  # Half heart
heart_half.scale = 3.0

heart_empty = mcrfpy.Sprite(pos=(240, 410), texture=texture, sprite_index=208)  # Empty heart
heart_empty.scale = 3.0

# Armor
armor = mcrfpy.Sprite(pos=(340, 410), texture=texture, sprite_index=211)  # Armor
armor.scale = 3.0

# Scale demonstration
scale_label = mcrfpy.Caption(pos=(500, 120), font=mcrfpy.default_font, text="Scale Demo")
scale_label.fill_color = mcrfpy.Color(255, 255, 255)

# Same sprite at different scales
for i, scale in enumerate([1.0, 2.0, 3.0, 4.0]):
    s = mcrfpy.Sprite(pos=(500 + i * 60, 150), texture=texture, sprite_index=84)  # Player
    s.scale = scale
    sprites.children.append(s)

# Add all elements to scene
ui = sprites.children
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
sprites.activate()

# Everything got built and attached
check("scene populated with sprite showcase", len(sprites.children) == 23)
check("sprite scale applied", player.scale == 3.0)
check("sprite index applied", player.sprite_index == 84)

# Set timer to capture; headless has no clock of its own, so drive it with step()
capture_timer = mcrfpy.Timer("capture", capture_sprites, 100, once=True)
for _ in range(4):
    mcrfpy.step(0.05)

check("capture timer fired", any(label.startswith("screenshot") for label, _ in results))

failures = [label for label, ok in results if not ok]
if failures:
    print(f"FAIL - {len(failures)} check(s) failed: {failures}")
    sys.exit(1)

print("PASS")
sys.exit(0)
