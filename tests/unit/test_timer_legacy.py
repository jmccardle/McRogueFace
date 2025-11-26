#!/usr/bin/env python3
"""
Test legacy timer API still works
"""
import mcrfpy
import sys

count = 0

def timer_callback(runtime):
    global count
    count += 1
    print(f"Timer fired! Count: {count}, Runtime: {runtime}")
    
    if count >= 3:
        print("Test passed - timer fired 3 times")
        sys.exit(0)

# Set up the scene
mcrfpy.createScene("test_scene")
mcrfpy.setScene("test_scene")

# Create a timer the old way
mcrfpy.setTimer("test_timer", timer_callback, 100)

print("Legacy timer test starting...")