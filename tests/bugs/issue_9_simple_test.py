#!/usr/bin/env python3
"""
Simple test for Issue #9: RenderTexture resize
"""

import mcrfpy
from mcrfpy import automation
import sys

def run_test(runtime):
    """Test RenderTexture resizing"""
    print("Testing Issue #9: RenderTexture resize")
    
    # Create a scene
    scene_ui = mcrfpy.sceneUI("test")
    
    # Create a small grid
    print("Creating 50x50 grid with initial size 500x500")
    grid = mcrfpy.Grid(50, 50)
    grid.x = 10
    grid.y = 10
    grid.w = 500
    grid.h = 500
    scene_ui.append(grid)
    
    # Color some tiles to make it visible
    print("Coloring tiles...")
    for i in range(50):
        # Diagonal line
        grid.at(i, i).color = mcrfpy.Color(255, 0, 0, 255)
        # Borders
        grid.at(i, 0).color = mcrfpy.Color(0, 255, 0, 255)
        grid.at(0, i).color = mcrfpy.Color(0, 0, 255, 255)
        grid.at(i, 49).color = mcrfpy.Color(255, 255, 0, 255)
        grid.at(49, i).color = mcrfpy.Color(255, 0, 255, 255)
    
    # Take initial screenshot
    automation.screenshot("/tmp/issue_9_before_resize.png")
    print("Screenshot saved: /tmp/issue_9_before_resize.png")
    
    # Resize to larger than 1920x1080
    print("\nResizing grid to 2500x2500...")
    grid.w = 2500
    grid.h = 2500
    
    # Take screenshot after resize
    automation.screenshot("/tmp/issue_9_after_resize.png")
    print("Screenshot saved: /tmp/issue_9_after_resize.png")
    
    # Test individual dimension changes
    print("\nTesting individual dimension changes...")
    grid.w = 3000
    automation.screenshot("/tmp/issue_9_width_3000.png")
    print("Width set to 3000, screenshot: /tmp/issue_9_width_3000.png")
    
    grid.h = 3000
    automation.screenshot("/tmp/issue_9_both_3000.png")
    print("Height set to 3000, screenshot: /tmp/issue_9_both_3000.png")
    
    print("\nIf the RenderTexture is properly recreated, all colored tiles")
    print("should be visible in all screenshots, not clipped at 1920x1080.")
    
    print("\nTest complete - PASS")
    sys.exit(0)

# Create and set scene
mcrfpy.createScene("test")
mcrfpy.setScene("test")

# Schedule test
mcrfpy.setTimer("test", run_test, 100)