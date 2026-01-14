#!/usr/bin/env python3
"""Test to verify timer-based screenshots work using mcrfpy.step() for synchronous execution"""
import mcrfpy
from mcrfpy import automation
import sys

# Counter to track timer calls
call_count = 0

def take_screenshot(timer, runtime):
    """Timer callback that takes screenshot"""
    global call_count
    call_count += 1
    print(f"Timer callback fired! (call #{call_count}, runtime={runtime})")

    # Take screenshot
    filename = f"timer_screenshot_test_{call_count}.png"
    result = automation.screenshot(filename)
    print(f"Screenshot result: {result} -> {filename}")

# Set up a simple scene
print("Creating test scene...")
test = mcrfpy.Scene("test")
test.activate()
ui = test.children

# Add visible content - a white frame on default background
frame = mcrfpy.Frame(pos=(100, 100), size=(200, 200),
                    fill_color=mcrfpy.Color(255, 255, 255))
ui.append(frame)

print("Setting timer to fire in 100ms...")
timer = mcrfpy.Timer("screenshot_timer", take_screenshot, 100, once=True)
print(f"Timer created: {timer}")

# Use mcrfpy.step() to advance simulation synchronously instead of waiting
print("Advancing simulation by 200ms using step()...")
mcrfpy.step(0.2)  # Advance 200ms - timer at 100ms should fire

# Verify timer fired
if call_count >= 1:
    print("SUCCESS: Timer fired and screenshot taken!")
    sys.exit(0)
else:
    print(f"FAIL: Expected call_count >= 1, got {call_count}")
    sys.exit(1)
