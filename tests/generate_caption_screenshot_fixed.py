#!/usr/bin/env python3
"""Generate caption documentation screenshot with proper font"""

import mcrfpy
from mcrfpy import automation
import sys

def capture_caption(runtime):
    """Capture caption example after render loop starts"""
    
    # Take screenshot
    automation.screenshot("mcrogueface.github.io/images/ui_caption_example.png")
    print("Caption screenshot saved!")
    
    # Exit after capturing
    sys.exit(0)

# Create scene
mcrfpy.createScene("captions")

# Title
title = mcrfpy.Caption(400, 30, "Caption Examples")
title.font = mcrfpy.default_font
title.font_size = 28
title.font_color = (255, 255, 255)

# Different sizes
size_label = mcrfpy.Caption(100, 100, "Different Sizes:")
size_label.font = mcrfpy.default_font
size_label.font_color = (200, 200, 200)

large = mcrfpy.Caption(300, 100, "Large Text (24pt)")
large.font = mcrfpy.default_font
large.font_size = 24
large.font_color = (255, 255, 255)

medium = mcrfpy.Caption(300, 140, "Medium Text (18pt)")
medium.font = mcrfpy.default_font
medium.font_size = 18
medium.font_color = (255, 255, 255)

small = mcrfpy.Caption(300, 170, "Small Text (14pt)")
small.font = mcrfpy.default_font
small.font_size = 14
small.font_color = (255, 255, 255)

# Different colors
color_label = mcrfpy.Caption(100, 230, "Different Colors:")
color_label.font = mcrfpy.default_font
color_label.font_color = (200, 200, 200)

white_text = mcrfpy.Caption(300, 230, "White Text")
white_text.font = mcrfpy.default_font
white_text.font_color = (255, 255, 255)

green_text = mcrfpy.Caption(300, 260, "Green Text")
green_text.font = mcrfpy.default_font
green_text.font_color = (100, 255, 100)

red_text = mcrfpy.Caption(300, 290, "Red Text")
red_text.font = mcrfpy.default_font
red_text.font_color = (255, 100, 100)

blue_text = mcrfpy.Caption(300, 320, "Blue Text")
blue_text.font = mcrfpy.default_font
blue_text.font_color = (100, 150, 255)

# Caption with background
bg_label = mcrfpy.Caption(100, 380, "With Background:")
bg_label.font = mcrfpy.default_font
bg_label.font_color = (200, 200, 200)

# Frame background
frame = mcrfpy.Frame(280, 370, 250, 50)
frame.bgcolor = (64, 64, 128)
frame.outline = 2

framed_text = mcrfpy.Caption(405, 395, "Caption on Frame")
framed_text.font = mcrfpy.default_font
framed_text.font_size = 18
framed_text.font_color = (255, 255, 255)
framed_text.centered = True

# Centered text example
center_label = mcrfpy.Caption(100, 460, "Centered Text:")
center_label.font = mcrfpy.default_font
center_label.font_color = (200, 200, 200)

centered = mcrfpy.Caption(400, 460, "This text is centered")
centered.font = mcrfpy.default_font
centered.font_size = 20
centered.font_color = (255, 255, 100)
centered.centered = True

# Multi-line example
multi_label = mcrfpy.Caption(100, 520, "Multi-line:")
multi_label.font = mcrfpy.default_font
multi_label.font_color = (200, 200, 200)

multiline = mcrfpy.Caption(300, 520, "Line 1: McRogueFace\nLine 2: Game Engine\nLine 3: Python API")
multiline.font = mcrfpy.default_font
multiline.font_size = 14
multiline.font_color = (255, 255, 255)

# Add all to scene
ui = mcrfpy.sceneUI("captions")
ui.append(title)
ui.append(size_label)
ui.append(large)
ui.append(medium)
ui.append(small)
ui.append(color_label)
ui.append(white_text)
ui.append(green_text)
ui.append(red_text)
ui.append(blue_text)
ui.append(bg_label)
ui.append(frame)
ui.append(framed_text)
ui.append(center_label)
ui.append(centered)
ui.append(multi_label)
ui.append(multiline)

# Switch to scene
mcrfpy.setScene("captions")

# Set timer to capture after rendering starts
mcrfpy.setTimer("capture", capture_caption, 100)