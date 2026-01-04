#!/usr/bin/env python3
"""
Test Timer API works correctly (#173)
Replaces old legacy setTimer test
"""
import mcrfpy
import sys

count = 0

def timer_callback(timer, runtime):
    global count
    count += 1
    print(f"Timer fired! Count: {count}, Runtime: {runtime}")

    if count >= 3:
        print("Test passed - timer fired 3 times")
        print("PASS")
        sys.exit(0)

# Set up the scene
test_scene = mcrfpy.Scene("test_scene")
test_scene.activate()

# Create a timer with new API
timer = mcrfpy.Timer("test_timer", timer_callback, 100)

print("Timer test starting...")
