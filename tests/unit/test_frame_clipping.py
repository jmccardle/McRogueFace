#!/usr/bin/env python3
"""Test UIFrame clipping functionality
Refactored to use mcrfpy.step() for synchronous execution.
"""

import mcrfpy
from mcrfpy import Color, Frame, Caption, automation
import sys

print("Creating test scene...")
test = mcrfpy.Scene("test")
test.activate()
mcrfpy.step(0.01)  # Initialize

print("Testing UIFrame clipping functionality...")

scene = test.children

# Create parent frame with clipping disabled (default)
parent1 = Frame(pos=(50, 50), size=(200, 150),
               fill_color=Color(100, 100, 200),
               outline_color=Color(255, 255, 255),
               outline=2)
parent1.name = "parent1"
scene.append(parent1)

# Create parent frame with clipping enabled
parent2 = Frame(pos=(300, 50), size=(200, 150),
               fill_color=Color(200, 100, 100),
               outline_color=Color(255, 255, 255),
               outline=2)
parent2.name = "parent2"
parent2.clip_children = True
scene.append(parent2)

# Add captions to both frames
caption1 = Caption(text="This text should overflow the frame bounds", pos=(10, 10))
caption1.font_size = 16
caption1.fill_color = Color(255, 255, 255)
parent1.children.append(caption1)

caption2 = Caption(text="This text should be clipped to frame bounds", pos=(10, 10))
caption2.font_size = 16
caption2.fill_color = Color(255, 255, 255)
parent2.children.append(caption2)

# Add child frames that extend beyond parent bounds
child1 = Frame(pos=(150, 100), size=(100, 100),
               fill_color=Color(50, 255, 50),
               outline_color=Color(0, 0, 0),
               outline=1)
parent1.children.append(child1)

child2 = Frame(pos=(150, 100), size=(100, 100),
               fill_color=Color(50, 255, 50),
               outline_color=Color(0, 0, 0),
               outline=1)
parent2.children.append(child2)

# Add caption to show clip state
status = Caption(text=f"Left frame: clip_children={parent1.clip_children}\n"
                      f"Right frame: clip_children={parent2.clip_children}",
                 pos=(50, 250))
status.font_size = 14
status.fill_color = Color(255, 255, 255)
scene.append(status)

# Add instructions
instructions = Caption(text="Left: Children should overflow (no clipping)\n"
                           "Right: Children should be clipped to frame bounds",
                      pos=(50, 300))
instructions.font_size = 12
instructions.fill_color = Color(200, 200, 200)
scene.append(instructions)

# Step to render
mcrfpy.step(0.1)

# Take screenshot
automation.screenshot("frame_clipping_test.png")

print(f"Parent1 clip_children: {parent1.clip_children}")
print(f"Parent2 clip_children: {parent2.clip_children}")

# Test toggling clip_children
parent1.clip_children = True
print(f"After toggle - Parent1 clip_children: {parent1.clip_children}")

# Verify the property setter works
test_passed = True
try:
    parent1.clip_children = "not a bool"
    print("ERROR: clip_children accepted non-boolean value")
    test_passed = False
except TypeError as e:
    print(f"PASS: clip_children correctly rejected non-boolean: {e}")

# Animate frames (move children)
parent1.children[1].x = 50
parent2.children[1].x = 50

# Step to render animation
mcrfpy.step(0.1)

# Take second screenshot
automation.screenshot("frame_clipping_animated.png")

print("\nTest completed successfully!")
print("Screenshots saved:")
print("  - frame_clipping_test.png (initial state)")
print("  - frame_clipping_animated.png (with animation)")

if test_passed:
    print("PASS")
    sys.exit(0)
else:
    print("FAIL")
    sys.exit(1)
