#!/usr/bin/env python3
"""Test for quickstart.md 'Main Menu' example.

Original (DEPRECATED - lines 82-125):
    mcrfpy.createScene("main_menu")
    ui = mcrfpy.sceneUI("main_menu")
    bg = mcrfpy.Frame(0, 0, 1024, 768, fill_color=(20, 20, 40))
    title = mcrfpy.Caption((312, 100), "My Awesome Game", font, fill_color=(255, 255, 100))
    button_frame.click = start_game
    mcrfpy.setScene("main_menu")

Modern equivalent below.
"""
import mcrfpy
from mcrfpy import automation
import sys

# Create scene using modern API
scene = mcrfpy.Scene("main_menu")
scene.activate()
mcrfpy.step(0.01)

# Load font
font = mcrfpy.Font("assets/JetbrainsMono.ttf")

# Add background using modern Frame API (keyword args)
bg = mcrfpy.Frame(
    pos=(0, 0),
    size=(1024, 768),
    fill_color=mcrfpy.Color(20, 20, 40)
)
scene.children.append(bg)

# Add title using modern Caption API
title = mcrfpy.Caption(
    pos=(312, 100),
    text="My Awesome Game",
    font=font,
    fill_color=mcrfpy.Color(255, 255, 100)
)
title.font_size = 48
title.outline = 2
title.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(title)

# Create button frame
button_frame = mcrfpy.Frame(
    pos=(362, 300),
    size=(300, 80),
    fill_color=mcrfpy.Color(50, 150, 50)
)

# Button caption
button_caption = mcrfpy.Caption(
    pos=(90, 25),  # Centered in button
    text="Start Game",
    fill_color=mcrfpy.Color(255, 255, 255)
)
button_caption.font_size = 24
button_frame.children.append(button_caption)

# Click handler using modern on_click (3 args: x, y, button)
def start_game(x, y, button):
    print("Starting the game!")

button_frame.on_click = start_game
scene.children.append(button_frame)

# Render and screenshot
mcrfpy.step(0.1)
automation.screenshot("/opt/goblincorps/repos/McRogueFace/tests/docs/screenshots/quickstart_main_menu.png")

print("PASS - quickstart main menu")
sys.exit(0)
