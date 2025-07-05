#!/usr/bin/env python3
"""Test that timers work correctly with --exec"""
import mcrfpy
from mcrfpy import automation

print("Setting up timer test...")

# Create a scene
mcrfpy.createScene("timer_works")
mcrfpy.setScene("timer_works")
ui = mcrfpy.sceneUI("timer_works")

# Add visible content
frame = mcrfpy.Frame(100, 100, 300, 200,
                    fill_color=mcrfpy.Color(255, 0, 0),
                    outline_color=mcrfpy.Color(255, 255, 255),
                    outline=3.0)
ui.append(frame)

caption = mcrfpy.Caption(mcrfpy.Vector(150, 150),
                        text="TIMER TEST SUCCESS",
                        fill_color=mcrfpy.Color(255, 255, 255))
caption.size = 24
ui.append(caption)

# Timer callback with correct signature
def timer_callback(runtime):
    print(f"\n✓ Timer fired successfully at runtime: {runtime}")
    
    # Take screenshot
    filename = f"timer_success_{int(runtime)}.png"
    result = automation.screenshot(filename)
    print(f"Screenshot saved: {filename} - Result: {result}")
    
    # Cancel timer and exit
    mcrfpy.delTimer("success_timer")
    print("Exiting...")
    mcrfpy.exit()

# Set timer
mcrfpy.setTimer("success_timer", timer_callback, 1000)
print("Timer set for 1 second. Game loop starting...")