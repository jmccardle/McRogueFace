#!/usr/bin/env python3
"""Example of CORRECT test pattern using mcrfpy.step() for automation
Refactored from timer-based approach to synchronous step() pattern.

Note (#350/#341): step() is the simulation clock and never renders;
automation.screenshot() is what forces a render of the current scene.
"""
import mcrfpy
from mcrfpy import automation
from datetime import datetime
import os
import sys

failures = []

def check(condition, message):
    if condition:
        print(f"  ok: {message}")
    else:
        print(f"  FAIL: {message}")
        failures.append(message)

# This code runs during --exec script execution
print("=== Setting Up Test Scene ===")

# Create scene with visible content
timer_test_scene = mcrfpy.Scene("timer_test_scene")
timer_test_scene.activate()
mcrfpy.step(0.01)  # Initialize scene

ui = timer_test_scene.children

# Add a bright red frame that should be visible
frame = mcrfpy.Frame(pos=(100, 100), size=(400, 300),
                    fill_color=mcrfpy.Color(255, 0, 0),      # Bright red
                    outline_color=mcrfpy.Color(255, 255, 255), # White outline
                    outline=5.0)
ui.append(frame)

# Add text
caption = mcrfpy.Caption(pos=(150, 150),
                        text="STEP TEST - SHOULD BE VISIBLE",
                        fill_color=mcrfpy.Color(255, 255, 255))
caption.font_size = 24
frame.children.append(caption)

# Add click handler to demonstrate interaction
# (#230) on_click receives (pos: Vector, button: MouseButton, action: InputState)
clicks_received = []
def frame_clicked(pos, button, action):
    clicks_received.append((pos, button, action))
    print(f"Frame clicked at ({pos.x}, {pos.y}) with button {button} ({action})")

frame.on_click = frame_clicked

print("Scene setup complete.")

# Step to render the scene
mcrfpy.step(0.1)

print("\n=== Automation Test Running ===")

# NOW we can take screenshots that will show content!
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"WORKING_screenshot_{timestamp}.png"

# Take screenshot - this should now show our red frame
result = automation.screenshot(filename)
print(f"Screenshot taken: {filename} - Result: {result}")
check(result is True, "screenshot() reported success")
check(os.path.exists(filename), f"{filename} exists on disk")
# A blank 1024x768 PNG compresses to a few hundred bytes; real content is far bigger
check(os.path.getsize(filename) > 2000,
      f"{filename} contains rendered content (size {os.path.getsize(filename)} > 2000)")

# Test clicking on the frame
automation.click((200, 200))  # Click in center of red frame

# Step to process the click
mcrfpy.step(0.1)

check(len(clicks_received) > 0, "frame.on_click fired for click inside the frame")
if clicks_received:
    pos, button, action = clicks_received[0]
    check((pos.x, pos.y) == (200.0, 200.0), "click reported the position it was sent to")
    check(button == mcrfpy.MouseButton.LEFT, "click reported the LEFT button")
    check(action == mcrfpy.InputState.PRESSED, "click reported the PRESSED state")

# Test keyboard input
automation.typewrite("Hello from step-based test!")

# Step to process keyboard input
mcrfpy.step(0.1)

# Take another screenshot to show any changes
filename2 = f"WORKING_screenshot_after_click_{timestamp}.png"
result2 = automation.screenshot(filename2)
print(f"Second screenshot: {filename2}")
check(result2 is True, "second screenshot() reported success")
check(os.path.exists(filename2), f"{filename2} exists on disk")

# Clean up the artifacts this test produced
for f in (filename, filename2):
    if os.path.exists(f):
        os.remove(f)

print("\nThis works because:")
print("1. mcrfpy.step() advances simulation synchronously")
print("2. automation.screenshot() forces a render of the active scene")
print("3. The RenderTexture contains actual rendered content")

if failures:
    print(f"\nFAIL: {len(failures)} check(s) failed")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("\nPASS")
sys.exit(0)
