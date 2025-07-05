#!/usr/bin/env python3
"""Animation System Demo - Shows all animation capabilities"""

import mcrfpy
import math

# Create main scene
mcrfpy.createScene("animation_demo")
ui = mcrfpy.sceneUI("animation_demo")
mcrfpy.setScene("animation_demo")

# Title
title = mcrfpy.Caption((400, 30), "McRogueFace Animation System Demo", mcrfpy.default_font)
title.size = 24
title.fill_color = (255, 255, 255)
# Note: centered property doesn't exist for Caption
ui.append(title)

# 1. Position Animation Demo
pos_frame = mcrfpy.Frame(50, 100, 80, 80)
pos_frame.fill_color = (255, 100, 100)
pos_frame.outline = 2
ui.append(pos_frame)

pos_label = mcrfpy.Caption((50, 80), "Position Animation", mcrfpy.default_font)
pos_label.fill_color = (200, 200, 200)
ui.append(pos_label)

# 2. Size Animation Demo
size_frame = mcrfpy.Frame(200, 100, 50, 50)
size_frame.fill_color = (100, 255, 100)
size_frame.outline = 2
ui.append(size_frame)

size_label = mcrfpy.Caption((200, 80), "Size Animation", mcrfpy.default_font)
size_label.fill_color = (200, 200, 200)
ui.append(size_label)

# 3. Color Animation Demo
color_frame = mcrfpy.Frame(350, 100, 80, 80)
color_frame.fill_color = (255, 0, 0)
ui.append(color_frame)

color_label = mcrfpy.Caption((350, 80), "Color Animation", mcrfpy.default_font)
color_label.fill_color = (200, 200, 200)
ui.append(color_label)

# 4. Easing Functions Demo
easing_y = 250
easing_frames = []
easings = ["linear", "easeIn", "easeOut", "easeInOut", "easeInElastic", "easeOutBounce"]

for i, easing in enumerate(easings):
    x = 50 + i * 120
    
    frame = mcrfpy.Frame(x, easing_y, 20, 20)
    frame.fill_color = (100, 150, 255)
    ui.append(frame)
    easing_frames.append((frame, easing))
    
    label = mcrfpy.Caption((x, easing_y - 20), easing, mcrfpy.default_font)
    label.size = 12
    label.fill_color = (200, 200, 200)
    ui.append(label)

# 5. Complex Animation Demo
complex_frame = mcrfpy.Frame(300, 350, 100, 100)
complex_frame.fill_color = (128, 128, 255)
complex_frame.outline = 3
ui.append(complex_frame)

complex_label = mcrfpy.Caption((300, 330), "Complex Multi-Property", mcrfpy.default_font)
complex_label.fill_color = (200, 200, 200)
ui.append(complex_label)

# Start animations
def start_animations(runtime):
    # 1. Position animation - back and forth
    x_anim = mcrfpy.Animation("x", 500.0, 3.0, "easeInOut")
    x_anim.start(pos_frame)
    
    # 2. Size animation - pulsing
    w_anim = mcrfpy.Animation("w", 150.0, 2.0, "easeInOut")
    h_anim = mcrfpy.Animation("h", 150.0, 2.0, "easeInOut")
    w_anim.start(size_frame)
    h_anim.start(size_frame)
    
    # 3. Color animation - rainbow cycle
    color_anim = mcrfpy.Animation("fill_color", (0, 255, 255, 255), 2.0, "linear")
    color_anim.start(color_frame)
    
    # 4. Easing demos - all move up with different easings
    for frame, easing in easing_frames:
        y_anim = mcrfpy.Animation("y", 150.0, 2.0, easing)
        y_anim.start(frame)
    
    # 5. Complex animation - multiple properties
    cx_anim = mcrfpy.Animation("x", 500.0, 4.0, "easeInOut")
    cy_anim = mcrfpy.Animation("y", 400.0, 4.0, "easeOut")
    cw_anim = mcrfpy.Animation("w", 150.0, 4.0, "easeInElastic")
    ch_anim = mcrfpy.Animation("h", 150.0, 4.0, "easeInElastic")
    outline_anim = mcrfpy.Animation("outline", 10.0, 4.0, "linear")
    
    cx_anim.start(complex_frame)
    cy_anim.start(complex_frame)
    cw_anim.start(complex_frame)
    ch_anim.start(complex_frame)
    outline_anim.start(complex_frame)
    
    # Individual color component animations
    r_anim = mcrfpy.Animation("fill_color.r", 255.0, 4.0, "easeInOut")
    g_anim = mcrfpy.Animation("fill_color.g", 100.0, 4.0, "easeInOut") 
    b_anim = mcrfpy.Animation("fill_color.b", 50.0, 4.0, "easeInOut")
    
    r_anim.start(complex_frame)
    g_anim.start(complex_frame)
    b_anim.start(complex_frame)
    
    print("All animations started!")

# Reverse some animations
def reverse_animations(runtime):
    # Position back
    x_anim = mcrfpy.Animation("x", 50.0, 3.0, "easeInOut")
    x_anim.start(pos_frame)
    
    # Size back
    w_anim = mcrfpy.Animation("w", 50.0, 2.0, "easeInOut")
    h_anim = mcrfpy.Animation("h", 50.0, 2.0, "easeInOut")
    w_anim.start(size_frame)
    h_anim.start(size_frame)
    
    # Color cycle continues
    color_anim = mcrfpy.Animation("fill_color", (255, 0, 255, 255), 2.0, "linear")
    color_anim.start(color_frame)
    
    # Easing frames back down
    for frame, easing in easing_frames:
        y_anim = mcrfpy.Animation("y", 250.0, 2.0, easing)
        y_anim.start(frame)

# Continue color cycle
def cycle_colors(runtime):
    color_anim = mcrfpy.Animation("fill_color", (255, 255, 0, 255), 2.0, "linear")
    color_anim.start(color_frame)

# Info text
info = mcrfpy.Caption((400, 550), "Watch as different properties animate with various easing functions!", mcrfpy.default_font)
info.fill_color = (255, 255, 200)
# Note: centered property doesn't exist for Caption
ui.append(info)

# Schedule animations
mcrfpy.setTimer("start", start_animations, 500)
mcrfpy.setTimer("reverse", reverse_animations, 4000)
mcrfpy.setTimer("cycle", cycle_colors, 2500)

# Exit handler
def on_key(key):
    if key == "Escape":
        mcrfpy.exit()

mcrfpy.keypressScene(on_key)

print("Animation demo started! Press Escape to exit.")