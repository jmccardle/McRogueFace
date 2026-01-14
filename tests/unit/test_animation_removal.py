#!/usr/bin/env python3
"""
Test if the crash is related to removing animated objects.
Uses mcrfpy.step() for synchronous test execution.
"""

import mcrfpy
import sys

print("Animation Removal Test")
print("=" * 40)

# Create initial scene
print("Creating scene...")
test = mcrfpy.Scene("test")
test.activate()
ui = test.children

# Add title and subtitle (to preserve during clearing)
title = mcrfpy.Caption(pos=(400, 20), text="Test Title")
subtitle = mcrfpy.Caption(pos=(400, 50), text="Test Subtitle")
ui.extend([title, subtitle])

# Initialize scene
mcrfpy.step(0.1)

# Create initial animated objects
print("Creating initial animated objects...")
initial_frames = []
for i in range(10):
    f = mcrfpy.Frame(pos=(50 + i*30, 100), size=(25, 25))
    f.fill_color = mcrfpy.Color(255, 100, 100)
    ui.append(f)
    initial_frames.append(f)

    # Animate them
    anim = mcrfpy.Animation("y", 300.0, 2.0, "easeOutBounce")
    anim.start(f)

print(f"Initial scene has {len(ui)} elements")

# Let animations run a bit
mcrfpy.step(0.5)

# Clear and recreate - mimics demo switching
print("\nClearing and recreating...")
print(f"Scene has {len(ui)} elements before clearing")

# Remove all but first 2 items (like clear_demo_objects)
# Use reverse iteration to remove by element
while len(ui) > 2:
    ui.remove(ui[-1])

print(f"Scene has {len(ui)} elements after clearing")

# Create new animated objects
print("Creating new animated objects...")
for i in range(5):
    f = mcrfpy.Frame(pos=(100 + i*50, 200), size=(40, 40))
    f.fill_color = mcrfpy.Color(100 + i*30, 50, 200)
    ui.append(f)

    # Start animation on the new frame
    target_x = 300 + i * 50
    anim = mcrfpy.Animation("x", float(target_x), 1.0, "easeInOut")
    anim.start(f)

print("New objects created and animated")
print(f"Scene now has {len(ui)} elements")

# Let new animations run
mcrfpy.step(1.5)

# Final check
print(f"\nFinal scene has {len(ui)} elements")
if len(ui) == 7:  # 2 captions + 5 new frames
    print("SUCCESS: Animation removal test passed!")
    sys.exit(0)
else:
    print(f"FAIL: Expected 7 elements, got {len(ui)}")
    sys.exit(1)
