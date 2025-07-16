#!/usr/bin/env python3
"""Simple screenshot test to verify automation API"""

import mcrfpy
from mcrfpy import automation
import sys
import time

def take_screenshot(runtime):
    """Take screenshot after render starts"""
    print(f"Timer callback fired at runtime: {runtime}")
    
    # Try different paths
    paths = [
        "test_screenshot.png",
        "./test_screenshot.png", 
        "mcrogueface.github.io/images/test_screenshot.png"
    ]
    
    for path in paths:
        try:
            print(f"Trying to save to: {path}")
            automation.screenshot(path)
            print(f"Success: {path}")
        except Exception as e:
            print(f"Failed {path}: {e}")
    
    sys.exit(0)

# Create minimal scene
mcrfpy.createScene("test")

# Add a visible element
caption = mcrfpy.Caption(100, 100, "Screenshot Test")
caption.font = mcrfpy.default_font
caption.font_color = (255, 255, 255)
caption.font_size = 24

mcrfpy.sceneUI("test").append(caption)
mcrfpy.setScene("test")

# Use timer to ensure rendering has started
print("Setting timer...")
mcrfpy.setTimer("screenshot", take_screenshot, 500)  # Wait 0.5 seconds
print("Timer set, entering game loop...")