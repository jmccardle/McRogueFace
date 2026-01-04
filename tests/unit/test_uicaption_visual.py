#!/usr/bin/env python3
"""Visual test for UICaption's visible and opacity properties."""

import mcrfpy
from mcrfpy import automation
import sys
import time

def run_visual_test(timer, runtime):
    """Timer callback to run visual tests and take screenshots."""
    print("\nRunning visual tests...")
    
    # Get our captions
    ui = test.children
    
    # Test 1: Make caption2 invisible
    print("Test 1: Making caption2 invisible")
    ui[1].visible = False
    automation.screenshot("caption_invisible.png")
    time.sleep(0.1)
    
    # Test 2: Make caption2 visible again
    print("Test 2: Making caption2 visible again")
    ui[1].visible = True
    automation.screenshot("caption_visible.png")
    time.sleep(0.1)
    
    # Test 3: Set different opacity levels
    print("Test 3: Testing opacity levels")
    
    # Caption 3 at 50% opacity
    ui[2].opacity = 0.5
    automation.screenshot("caption_opacity_50.png")
    time.sleep(0.1)
    
    # Caption 4 at 25% opacity
    ui[3].opacity = 0.25
    automation.screenshot("caption_opacity_25.png")
    time.sleep(0.1)
    
    # Caption 5 at 0% opacity (fully transparent)
    ui[4].opacity = 0.0
    automation.screenshot("caption_opacity_0.png")
    time.sleep(0.1)
    
    # Test 4: Move captions
    print("Test 4: Testing move method")
    ui[0].move(100, 0)  # Move first caption right
    ui[1].move(0, 50)   # Move second caption down
    automation.screenshot("caption_moved.png")
    
    print("\nVisual tests completed!")
    print("Screenshots saved:")
    print("  - caption_invisible.png")
    print("  - caption_visible.png")
    print("  - caption_opacity_50.png")
    print("  - caption_opacity_25.png")
    print("  - caption_opacity_0.png")
    print("  - caption_moved.png")
    
    sys.exit(0)

def main():
    """Set up the visual test scene."""
    print("=== UICaption Visual Test ===\n")
    
    # Create test scene
    test = mcrfpy.Scene("test")
    test.activate()
    
    # Create multiple captions for testing
    caption1 = mcrfpy.Caption(pos=(50, 50), text="Caption 1: Normal", fill_color=mcrfpy.Color(255, 255, 255))
    caption2 = mcrfpy.Caption(pos=(50, 100), text="Caption 2: Will be invisible", fill_color=mcrfpy.Color(255, 200, 200))
    caption3 = mcrfpy.Caption(pos=(50, 150), text="Caption 3: 50% opacity", fill_color=mcrfpy.Color(200, 255, 200))
    caption4 = mcrfpy.Caption(pos=(50, 200), text="Caption 4: 25% opacity", fill_color=mcrfpy.Color(200, 200, 255))
    caption5 = mcrfpy.Caption(pos=(50, 250), text="Caption 5: 0% opacity", fill_color=mcrfpy.Color(255, 255, 200))
    
    # Add captions to scene
    ui = test.children
    ui.append(caption1)
    ui.append(caption2)
    ui.append(caption3)
    ui.append(caption4)
    ui.append(caption5)
    
    # Also add a frame as background to see transparency better
    frame = mcrfpy.Frame(pos=(40, 40), size=(400, 250), fill_color=mcrfpy.Color(50, 50, 50))
    frame.z_index = -1  # Put it behind the captions
    ui.append(frame)
    
    print("Scene setup complete. Scheduling visual tests...")

    # Schedule visual test to run after render loop starts
    visual_test_timer = mcrfpy.Timer("visual_test", run_visual_test, 100, once=True)

if __name__ == "__main__":
    main()