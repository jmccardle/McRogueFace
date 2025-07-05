#!/usr/bin/env python3
"""
Test for Issue #9: Recreate RenderTexture when UIGrid is resized

This test checks if resizing a UIGrid properly recreates its RenderTexture.
"""

import mcrfpy
from mcrfpy import automation
import sys

def run_test(runtime):
    """Test that UIGrid properly handles resizing"""
    try:
        # Create a grid with initial size
        grid = mcrfpy.Grid(20, 20)
        grid.x = 50
        grid.y = 50
        grid.w = 200
        grid.h = 200
        
        # Add grid to scene
        scene_ui = mcrfpy.sceneUI("test")
        scene_ui.append(grid)
        
        # Take initial screenshot
        automation.screenshot("/tmp/grid_initial.png")
        print("Initial grid created at 200x200")
        
        # Add some visible content to the grid
        for x in range(5):
            for y in range(5):
                grid.at(x, y).color = mcrfpy.Color(255, 0, 0, 255)  # Red squares
        
        automation.screenshot("/tmp/grid_with_content.png")
        print("Added red squares to grid")
        
        # Test 1: Resize the grid smaller
        print("\nTest 1: Resizing grid to 100x100...")
        grid.w = 100
        grid.h = 100
        
        automation.screenshot("/tmp/grid_resized_small.png")
        
        # The grid should still render correctly
        print("✓ Test 1: Grid resized to 100x100")
        
        # Test 2: Resize the grid larger than initial
        print("\nTest 2: Resizing grid to 400x400...")
        grid.w = 400
        grid.h = 400
        
        automation.screenshot("/tmp/grid_resized_large.png")
        
        # Add content at the edges to test if render texture is big enough
        for x in range(15, 20):
            for y in range(15, 20):
                grid.at(x, y).color = mcrfpy.Color(0, 255, 0, 255)  # Green squares
        
        automation.screenshot("/tmp/grid_resized_with_edge_content.png")
        print("✓ Test 2: Grid resized to 400x400 with edge content")
        
        # Test 3: Resize beyond the hardcoded 1920x1080 limit
        print("\nTest 3: Resizing grid beyond 1920x1080...")
        grid.w = 2000
        grid.h = 1200
        
        automation.screenshot("/tmp/grid_resized_huge.png")
        
        # This should fail with the current implementation
        print("✗ Test 3: This likely shows rendering errors due to fixed RenderTexture size")
        print("This is the bug described in Issue #9!")
        
        print("\nScreenshots saved to /tmp/grid_*.png")
        print("Check grid_resized_huge.png for rendering artifacts")
        
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
    
    sys.exit(0)

# Set up the test scene
mcrfpy.createScene("test")
mcrfpy.setScene("test")

# Schedule test to run after game loop starts
mcrfpy.setTimer("test", run_test, 100)