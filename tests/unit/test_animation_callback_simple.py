#!/usr/bin/env python3
"""Simple test for animation callbacks using mcrfpy.step() for synchronous execution"""

import mcrfpy
import sys

print("Animation Callback Demo")
print("=" * 30)

# Global state to track callback
callback_count = 0
callback_args = []

# #229 - Animation callbacks now receive (target, property, value) instead of (anim, target)
def my_callback(target, prop, value):
    """Simple callback that prints when animation completes"""
    global callback_count
    callback_count += 1
    callback_args.append((target, prop, value))
    print(f"Animation completed! Callback #{callback_count}")
    print(f"  Target: {type(target).__name__}, Property: {prop}, Value: {value}")

# Create scene
callback_demo = mcrfpy.Scene("callback_demo")
callback_demo.activate()

# Create a frame to animate
frame = mcrfpy.Frame(pos=(100, 100), size=(200, 200), fill_color=(255, 0, 0))
ui = callback_demo.children
ui.append(frame)

# Test 1: Animation with callback
# mcrfpy.Animation is no longer exported; animations are constructed via the
# target drawable's .animate() method, which starts them immediately.
print("Starting animation with callback (1.0s duration)...")
frame.animate("x", 400.0, 1.0, mcrfpy.Easing.EASE_IN_OUT_QUAD, callback=my_callback)

# Use mcrfpy.step() to advance past animation completion
mcrfpy.step(1.5)  # Advance 1.5 seconds - animation completes at 1.0s

if callback_count != 1:
    print(f"FAIL: Expected 1 callback, got {callback_count}")
    sys.exit(1)

# The callback receives (target, property, final_value) -- and the animation must
# have actually driven the property to its target.
cb_target, cb_prop, cb_value = callback_args[0]
if cb_target is not frame or cb_prop != "x" or cb_value != 400.0:
    print(f"FAIL: Bad callback args: {callback_args[0]}")
    sys.exit(1)
if frame.x != 400.0:
    print(f"FAIL: Expected frame.x == 400.0, got {frame.x}")
    sys.exit(1)
print("SUCCESS: Callback fired exactly once!")

# Test 2: Animation without callback
print("\nTesting animation without callback (0.5s duration)...")
frame.animate("y", 300.0, 0.5, mcrfpy.Easing.LINEAR)

# Advance past second animation
mcrfpy.step(0.7)

if callback_count != 1:
    print(f"FAIL: Callback count changed to {callback_count}")
    sys.exit(1)
if frame.y != 300.0:
    print(f"FAIL: Expected frame.y == 300.0, got {frame.y}")
    sys.exit(1)

print("SUCCESS: No unexpected callbacks fired!")
print("\nAnimation callback feature working correctly!")
print("PASS")
sys.exit(0)
