#!/usr/bin/env python3
"""
Test timer callback arguments with new Timer API (#173)
"""
import mcrfpy
import sys

call_count = 0

def new_style_callback(timer, runtime):
    """New style callback - receives timer object and runtime"""
    global call_count
    call_count += 1
    print(f"Callback called with: timer={timer} (type: {type(timer)}), runtime={runtime} (type: {type(runtime)})")
    if hasattr(timer, 'once'):
        print(f"Got Timer object! once={timer.once}")
    if call_count >= 2:
        print("PASS")
        sys.exit(0)

# Set up the scene
test_scene = mcrfpy.Scene("test_scene")
test_scene.activate()

print("Testing new Timer callback signature (timer, runtime)...")
timer = mcrfpy.Timer("test_timer", new_style_callback, 100)
print(f"Timer created: {timer}")
