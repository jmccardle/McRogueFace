#!/usr/bin/env python3
"""
Minimal test for Issue #9: RenderTexture resize
"""

import mcrfpy
from mcrfpy import automation
import sys

def run_test(timer, runtime):
    """Test RenderTexture resizing"""
    print("Testing Issue #9: RenderTexture resize (minimal)")
    
    try:
        # Create a grid
        print("Creating grid...")
        grid = mcrfpy.Grid(30, 30)
        grid.x = 10
        grid.y = 10
        grid.w = 300
        grid.h = 300
        
        # Add to scene
        scene_ui = test.children
        scene_ui.append(grid)
        
        # Test accessing grid points
        print("Testing grid.at()...")
        point = grid.at(5, 5)
        print(f"Got grid point: {point}")
        
        # Test color creation
        print("Testing Color creation...")
        red = mcrfpy.Color(255, 0, 0, 255)
        print(f"Created color: {red}")
        
        # Set color
        print("Setting grid point color...")
        point.color = red
        
        print("Taking screenshot before resize...")
        automation.screenshot("/tmp/issue_9_minimal_before.png")
        
        # Resize grid
        print("Resizing grid to 2500x2500...")
        grid.w = 2500
        grid.h = 2500
        
        print("Taking screenshot after resize...")
        automation.screenshot("/tmp/issue_9_minimal_after.png")
        
        print("\nTest complete - check screenshots")
        print("If RenderTexture is recreated properly, grid should render correctly at large size")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    sys.exit(0)

# Create and set scene
test = mcrfpy.Scene("test")
test.activate()

# Schedule test
test_timer = mcrfpy.Timer("test", run_test, 100, once=True)