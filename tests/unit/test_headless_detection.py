#!/usr/bin/env python3
"""Test to detect if we're running in headless mode"""

import mcrfpy
from mcrfpy import automation
import sys

# Create scene
detect_test = mcrfpy.Scene("detect_test")
ui = detect_test.children
detect_test.activate()

# Create a frame
frame = mcrfpy.Frame(pos=(100, 100), size=(200, 200))
frame.fill_color = mcrfpy.Color(255, 100, 100, 255)
ui.append(frame)

def test_mode(runtime):
    try:
        # Try to take a screenshot - this should work in both modes
        automation.screenshot("test_screenshot.png")
        print("PASS: Screenshot capability available")
        
        # Check if we can interact with the window
        try:
            # In headless mode, this should still work but via the headless renderer
            automation.click(200, 200)
            print("PASS: Click automation available")
        except Exception as e:
            print(f"Click failed: {e}")
            
    except Exception as e:
        print(f"Screenshot failed: {e}")
    
    print("Test complete")
    sys.exit(0)

# Run test after render loop starts
mcrfpy.setTimer("test", test_mode, 100)