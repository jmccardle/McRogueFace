#!/usr/bin/env python3
"""
Test timer callback arguments
"""
import mcrfpy
import sys

call_count = 0

def old_style_callback(arg):
    """Old style callback - should receive just runtime"""
    global call_count
    call_count += 1
    print(f"Old style callback called with: {arg} (type: {type(arg)})")
    if call_count >= 2:
        sys.exit(0)

def new_style_callback(arg1, arg2=None):
    """New style callback - should receive timer object and runtime"""
    print(f"New style callback called with: arg1={arg1} (type: {type(arg1)}), arg2={arg2} (type: {type(arg2) if arg2 else 'None'})")
    if hasattr(arg1, 'once'):
        print(f"Got Timer object! once={arg1.once}")
    sys.exit(0)

# Set up the scene
mcrfpy.createScene("test_scene") 
mcrfpy.setScene("test_scene")

print("Testing old style timer with setTimer...")
mcrfpy.setTimer("old_timer", old_style_callback, 100)

print("\nTesting new style timer with Timer object...")
timer = mcrfpy.Timer("new_timer", new_style_callback, 200)
print(f"Timer created: {timer}")