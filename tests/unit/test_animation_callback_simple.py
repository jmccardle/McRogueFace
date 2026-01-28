#!/usr/bin/env python3
"""Simple test for animation callbacks using mcrfpy.step() for synchronous execution"""

import mcrfpy
import sys

print("Animation Callback Demo")
print("=" * 30)

# Global state to track callback
callback_count = 0

# #229 - Animation callbacks now receive (target, property, value) instead of (anim, target)
def my_callback(target, prop, value):
    """Simple callback that prints when animation completes"""
    global callback_count
    callback_count += 1
    print(f"Animation completed! Callback #{callback_count}")
    print(f"  Target: {type(target).__name__}, Property: {prop}, Value: {value}")

# Create scene
callback_demo = mcrfpy.Scene("callback_demo")
callback_demo.activate()

# Create a frame to animate
frame = mcrfpy.Frame((100, 100), (200, 200), fill_color=(255, 0, 0))
ui = callback_demo.children
ui.append(frame)

# Test 1: Animation with callback
print("Starting animation with callback (1.0s duration)...")
anim = mcrfpy.Animation("x", 400.0, 1.0, "easeInOutQuad", callback=my_callback)
anim.start(frame)

# Use mcrfpy.step() to advance past animation completion
mcrfpy.step(1.5)  # Advance 1.5 seconds - animation completes at 1.0s

if callback_count != 1:
    print(f"FAIL: Expected 1 callback, got {callback_count}")
    sys.exit(1)
print("SUCCESS: Callback fired exactly once!")

# Test 2: Animation without callback
print("\nTesting animation without callback (0.5s duration)...")
anim2 = mcrfpy.Animation("y", 300.0, 0.5, "linear")
anim2.start(frame)

# Advance past second animation
mcrfpy.step(0.7)

if callback_count != 1:
    print(f"FAIL: Callback count changed to {callback_count}")
    sys.exit(1)

print("SUCCESS: No unexpected callbacks fired!")
print("\nAnimation callback feature working correctly!")
sys.exit(0)
