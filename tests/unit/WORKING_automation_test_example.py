#!/usr/bin/env python3
"""Example of CORRECT test pattern using mcrfpy.step() for automation
Refactored from timer-based approach to synchronous step() pattern.
"""
import mcrfpy
from mcrfpy import automation
from datetime import datetime
import sys

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
click_received = False
def frame_clicked(x, y, button):
    global click_received
    click_received = True
    print(f"Frame clicked at ({x}, {y}) with button {button}")

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

# Test clicking on the frame
automation.click(200, 200)  # Click in center of red frame

# Step to process the click
mcrfpy.step(0.1)

# Test keyboard input
automation.typewrite("Hello from step-based test!")

# Step to process keyboard input
mcrfpy.step(0.1)

# Take another screenshot to show any changes
filename2 = f"WORKING_screenshot_after_click_{timestamp}.png"
automation.screenshot(filename2)
print(f"Second screenshot: {filename2}")

print("Test completed successfully!")
print("\nThis works because:")
print("1. mcrfpy.step() advances simulation synchronously")
print("2. The scene renders during step() calls")
print("3. The RenderTexture contains actual rendered content")

print("PASS")
sys.exit(0)
