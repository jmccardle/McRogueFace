#!/usr/bin/env python3
"""Simple test for animation callbacks - demonstrates basic usage"""

import mcrfpy
import sys

# Global state to track callback
callback_count = 0
callback_demo = None  # Will be set in setup_and_run

def my_callback(anim, target):
    """Simple callback that prints when animation completes"""
    global callback_count
    callback_count += 1
    print(f"Animation completed! Callback #{callback_count}")
    # For now, anim and target are None - future enhancement

def setup_and_run():
    """Set up scene and run animation with callback"""
    global callback_demo
    # Create scene
    callback_demo = mcrfpy.Scene("callback_demo")
    callback_demo.activate()

    # Create a frame to animate
    frame = mcrfpy.Frame((100, 100), (200, 200), fill_color=(255, 0, 0))
    ui = callback_demo.children
    ui.append(frame)

    # Create animation with callback
    print("Starting animation with callback...")
    anim = mcrfpy.Animation("x", 400.0, 1.0, "easeInOutQuad", callback=my_callback)
    anim.start(frame)

    # Schedule check after animation should complete
    mcrfpy.Timer("check", check_result, 1500, once=True)

def check_result(timer, runtime):
    """Check if callback fired correctly"""
    global callback_count, callback_demo

    if callback_count == 1:
        print("SUCCESS: Callback fired exactly once!")

        # Test 2: Animation without callback
        print("\nTesting animation without callback...")
        ui = callback_demo.children
        frame = ui[0]

        anim2 = mcrfpy.Animation("y", 300.0, 0.5, "linear")
        anim2.start(frame)

        mcrfpy.Timer("final", final_check, 700, once=True)
    else:
        print(f"FAIL: Expected 1 callback, got {callback_count}")
        sys.exit(1)

def final_check(timer, runtime):
    """Final check - callback count should still be 1"""
    global callback_count

    if callback_count == 1:
        print("SUCCESS: No unexpected callbacks fired!")
        print("\nAnimation callback feature working correctly!")
        sys.exit(0)
    else:
        print(f"FAIL: Callback count changed to {callback_count}")
        sys.exit(1)

# Start the demo
print("Animation Callback Demo")
print("=" * 30)
setup_and_run()
