#!/usr/bin/env python3
"""Debug rendering to find why screenshots are transparent"""
import mcrfpy
from mcrfpy import automation
import sys

# Check if we're in headless mode
print("=== Debug Render Test ===")
print(f"Module loaded: {mcrfpy}")
print(f"Automation available: {'automation' in dir(mcrfpy)}")

# Try to understand the scene state
print("\nCreating and checking scene...")
mcrfpy.createScene("debug_scene")
mcrfpy.setScene("debug_scene")
current = mcrfpy.currentScene()
print(f"Current scene: {current}")

# Get UI collection
ui = mcrfpy.sceneUI("debug_scene")
print(f"UI collection type: {type(ui)}")
print(f"Initial UI elements: {len(ui)}")

# Add a simple frame
frame = mcrfpy.Frame(0, 0, 100, 100, 
                    fill_color=mcrfpy.Color(255, 255, 255))
ui.append(frame)
print(f"After adding frame: {len(ui)} elements")

# Check if the issue is with timing
print("\nTaking immediate screenshot...")
result1 = automation.screenshot("debug_immediate.png")
print(f"Immediate screenshot result: {result1}")

# Maybe we need to let the engine process the frame?
# In headless mode with --exec, the game loop might not be running
print("\nNote: In --exec mode, the game loop doesn't run continuously.")
print("This might prevent rendering from occurring.")

# Let's also check what happens with multiple screenshots
for i in range(3):
    result = automation.screenshot(f"debug_multi_{i}.png")
    print(f"Screenshot {i}: {result}")

print("\nConclusion: The issue appears to be that in --exec mode,")
print("the render loop never runs, so nothing is drawn to the RenderTexture.")
print("The screenshot captures an uninitialized/unrendered texture.")

sys.exit(0)