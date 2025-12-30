#!/usr/bin/env python3
"""
Test if the crash is related to removing animated objects
"""

import mcrfpy
import sys

def clear_and_recreate(runtime):
    """Clear UI and recreate - mimics demo switching"""
    print(f"\nTimer called at {runtime}")
    
    ui = mcrfpy.sceneUI("test")
    
    # Remove all but first 2 items (like clear_demo_objects)
    print(f"Scene has {len(ui)} elements before clearing")
    while len(ui) > 2:
        ui.remove(len(ui)-1)
    print(f"Scene has {len(ui)} elements after clearing")
    
    # Create new animated objects
    print("Creating new animated objects...")
    for i in range(5):
        f = mcrfpy.Frame(100 + i*50, 200, 40, 40)
        f.fill_color = mcrfpy.Color(100 + i*30, 50, 200)
        ui.append(f)
        
        # Start animation on the new frame
        target_x = 300 + i * 50
        anim = mcrfpy.Animation("x", float(target_x), 1.0, "easeInOut")
        anim.start(f)
    
    print("New objects created and animated")
    
    # Schedule exit
    mcrfpy.setTimer("exit", lambda t: sys.exit(0), 2000)

# Create initial scene
print("Creating scene...")
mcrfpy.createScene("test")
mcrfpy.setScene("test")
ui = mcrfpy.sceneUI("test")

# Add title and subtitle (to preserve during clearing)
title = mcrfpy.Caption(pos=(400, 20), text="Test Title")
subtitle = mcrfpy.Caption(pos=(400, 50), text="Test Subtitle")
ui.extend([title, subtitle])

# Create initial animated objects
print("Creating initial animated objects...")
for i in range(10):
    f = mcrfpy.Frame(pos=(50 + i*30, 100), size=(25, 25))
    f.fill_color = mcrfpy.Color(255, 100, 100)
    ui.append(f)
    
    # Animate them
    anim = mcrfpy.Animation("y", 300.0, 2.0, "easeOutBounce")
    anim.start(f)

print(f"Initial scene has {len(ui)} elements")

# Schedule the clear and recreate
mcrfpy.setTimer("switch", clear_and_recreate, 1000)

print("\nEntering game loop...")