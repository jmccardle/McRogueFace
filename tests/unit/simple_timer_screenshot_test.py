#!/usr/bin/env python3
"""Simplified test to verify timer-based screenshots work"""
import mcrfpy
from mcrfpy import automation

# Counter to track timer calls
call_count = 0

def take_screenshot_and_exit():
    """Timer callback that takes screenshot then exits"""
    global call_count
    call_count += 1
    
    print(f"\nTimer callback fired! (call #{call_count})")
    
    # Take screenshot
    filename = f"timer_screenshot_test_{call_count}.png"
    result = automation.screenshot(filename)
    print(f"Screenshot result: {result} -> {filename}")
    
    # Exit after first call
    if call_count >= 1:
        print("Exiting game...")
        mcrfpy.exit()

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
mcrfpy.setTimer("screenshot_timer", take_screenshot_and_exit, 100)

print("Setup complete. Game loop starting...")