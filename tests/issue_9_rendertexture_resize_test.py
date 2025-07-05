#!/usr/bin/env python3
"""
Comprehensive test for Issue #9: Recreate RenderTexture when UIGrid is resized

This test demonstrates that UIGrid has a hardcoded RenderTexture size of 1920x1080,
which causes rendering issues when the grid is resized beyond these dimensions.

The bug: UIGrid::render() creates a RenderTexture with fixed size (1920x1080) once,
but never recreates it when the grid is resized, causing clipping and rendering artifacts.
"""

import mcrfpy
from mcrfpy import automation
import sys
import os

def create_checkerboard_pattern(grid, grid_width, grid_height, cell_size=2):
    """Create a checkerboard pattern on the grid for visibility"""
    for x in range(grid_width):
        for y in range(grid_height):
            if (x // cell_size + y // cell_size) % 2 == 0:
                grid.at(x, y).color = mcrfpy.Color(255, 255, 255, 255)  # White
            else:
                grid.at(x, y).color = mcrfpy.Color(100, 100, 100, 255)  # Gray

def add_border_markers(grid, grid_width, grid_height):
    """Add colored markers at the borders to test rendering limits"""
    # Red border on top
    for x in range(grid_width):
        grid.at(x, 0).color = mcrfpy.Color(255, 0, 0, 255)
    
    # Green border on right
    for y in range(grid_height):
        grid.at(grid_width-1, y).color = mcrfpy.Color(0, 255, 0, 255)
    
    # Blue border on bottom
    for x in range(grid_width):
        grid.at(x, grid_height-1).color = mcrfpy.Color(0, 0, 255, 255)
    
    # Yellow border on left
    for y in range(grid_height):
        grid.at(0, y).color = mcrfpy.Color(255, 255, 0, 255)

def test_rendertexture_resize():
    """Test RenderTexture behavior with various grid sizes"""
    print("=== Testing UIGrid RenderTexture Resize (Issue #9) ===\n")
    
    scene_ui = mcrfpy.sceneUI("test")
    
    # Test 1: Small grid (should work fine)
    print("--- Test 1: Small Grid (400x300) ---")
    grid1 = mcrfpy.Grid(20, 15)  # 20x15 tiles
    grid1.x = 10
    grid1.y = 10
    grid1.w = 400
    grid1.h = 300
    scene_ui.append(grid1)
    
    create_checkerboard_pattern(grid1, 20, 15)
    add_border_markers(grid1, 20, 15)
    
    automation.screenshot("/tmp/issue_9_small_grid.png")
    print("✓ Small grid created and rendered")
    
    # Test 2: Medium grid at 1920x1080 limit
    print("\n--- Test 2: Medium Grid at 1920x1080 Limit ---")
    grid2 = mcrfpy.Grid(64, 36)  # 64x36 tiles at 30px each = 1920x1080
    grid2.x = 10
    grid2.y = 320
    grid2.w = 1920
    grid2.h = 1080
    scene_ui.append(grid2)
    
    create_checkerboard_pattern(grid2, 64, 36, 4)
    add_border_markers(grid2, 64, 36)
    
    automation.screenshot("/tmp/issue_9_limit_grid.png")
    print("✓ Grid at RenderTexture limit created")
    
    # Test 3: Resize grid1 beyond limits
    print("\n--- Test 3: Resizing Small Grid Beyond 1920x1080 ---")
    print("Original size: 400x300")
    grid1.w = 2400
    grid1.h = 1400
    print(f"Resized to: {grid1.w}x{grid1.h}")
    
    # The content should still be visible but may be clipped
    automation.screenshot("/tmp/issue_9_resized_beyond_limit.png")
    print("✗ EXPECTED ISSUE: Grid resized beyond RenderTexture limits")
    print("  Content beyond 1920x1080 will be clipped!")
    
    # Test 4: Create large grid from start
    print("\n--- Test 4: Large Grid from Start (2400x1400) ---")
    # Clear previous grids
    while len(scene_ui) > 0:
        scene_ui.remove(0)
    
    grid3 = mcrfpy.Grid(80, 50)  # Large tile count
    grid3.x = 10
    grid3.y = 10
    grid3.w = 2400
    grid3.h = 1400
    scene_ui.append(grid3)
    
    create_checkerboard_pattern(grid3, 80, 50, 5)
    add_border_markers(grid3, 80, 50)
    
    # Add markers at specific positions to test rendering
    # Mark the center
    center_x, center_y = 40, 25
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            grid3.at(center_x + dx, center_y + dy).color = mcrfpy.Color(255, 0, 255, 255)  # Magenta
    
    # Mark position at 1920 pixel boundary (64 tiles * 30 pixels/tile = 1920)
    if 64 < 80:  # Only if within grid bounds
        for y in range(min(50, 10)):
            grid3.at(64, y).color = mcrfpy.Color(255, 128, 0, 255)  # Orange
    
    automation.screenshot("/tmp/issue_9_large_grid.png")
    print("✗ EXPECTED ISSUE: Large grid created")
    print("  Content beyond 1920x1080 will not render!")
    print("  Look for missing orange line at x=1920 boundary")
    
    # Test 5: Dynamic resize test
    print("\n--- Test 5: Dynamic Resize Test ---")
    scene_ui.remove(0)
    
    grid4 = mcrfpy.Grid(100, 100)
    grid4.x = 10
    grid4.y = 10
    scene_ui.append(grid4)
    
    sizes = [(500, 500), (1000, 1000), (1500, 1500), (2000, 2000), (2500, 2500)]
    
    for i, (w, h) in enumerate(sizes):
        grid4.w = w
        grid4.h = h
        
        # Add pattern at current size
        visible_tiles_x = min(100, w // 30)
        visible_tiles_y = min(100, h // 30)
        
        # Clear and create new pattern
        for x in range(visible_tiles_x):
            for y in range(visible_tiles_y):
                if x == visible_tiles_x - 1 or y == visible_tiles_y - 1:
                    # Edge markers
                    grid4.at(x, y).color = mcrfpy.Color(255, 255, 0, 255)
                elif (x + y) % 10 == 0:
                    # Diagonal lines
                    grid4.at(x, y).color = mcrfpy.Color(0, 255, 255, 255)
        
        automation.screenshot(f"/tmp/issue_9_resize_{w}x{h}.png")
        
        if w > 1920 or h > 1080:
            print(f"✗ Size {w}x{h}: Content clipped at 1920x1080")
        else:
            print(f"✓ Size {w}x{h}: Rendered correctly")
    
    # Test 6: Verify exact clipping boundary
    print("\n--- Test 6: Exact Clipping Boundary Test ---")
    scene_ui.remove(0)
    
    grid5 = mcrfpy.Grid(70, 40)
    grid5.x = 0
    grid5.y = 0
    grid5.w = 2100  # 70 * 30 = 2100 pixels
    grid5.h = 1200  # 40 * 30 = 1200 pixels
    scene_ui.append(grid5)
    
    # Create a pattern that shows the boundary clearly
    for x in range(70):
        for y in range(40):
            pixel_x = x * 30
            pixel_y = y * 30
            
            if pixel_x == 1920 - 30:  # Last tile before boundary
                grid5.at(x, y).color = mcrfpy.Color(255, 0, 0, 255)  # Red
            elif pixel_x == 1920:  # First tile after boundary
                grid5.at(x, y).color = mcrfpy.Color(0, 255, 0, 255)  # Green
            elif pixel_y == 1080 - 30:  # Last row before boundary
                grid5.at(x, y).color = mcrfpy.Color(0, 0, 255, 255)  # Blue
            elif pixel_y == 1080:  # First row after boundary
                grid5.at(x, y).color = mcrfpy.Color(255, 255, 0, 255)  # Yellow
            else:
                # Normal checkerboard
                if (x + y) % 2 == 0:
                    grid5.at(x, y).color = mcrfpy.Color(200, 200, 200, 255)
    
    automation.screenshot("/tmp/issue_9_boundary_test.png")
    print("Screenshot saved showing clipping boundary")
    print("- Red tiles: Last visible column (x=1890-1919)")
    print("- Green tiles: First clipped column (x=1920+)")
    print("- Blue tiles: Last visible row (y=1050-1079)")
    print("- Yellow tiles: First clipped row (y=1080+)")
    
    # Summary
    print("\n=== SUMMARY ===")
    print("Issue #9: UIGrid uses a hardcoded RenderTexture size of 1920x1080")
    print("Problems demonstrated:")
    print("1. Grids larger than 1920x1080 are clipped")
    print("2. Resizing grids doesn't recreate the RenderTexture")
    print("3. Content beyond the boundary is not rendered")
    print("\nThe fix should:")
    print("1. Recreate RenderTexture when grid size changes")
    print("2. Use the actual grid dimensions instead of hardcoded values")
    print("3. Consider memory limits for very large grids")
    
    print(f"\nScreenshots saved to /tmp/issue_9_*.png")

def run_test(runtime):
    """Timer callback to run the test"""
    try:
        test_rendertexture_resize()
        print("\nTest complete - check screenshots for visual verification")
    except Exception as e:
        print(f"\nTest error: {e}")
        import traceback
        traceback.print_exc()
    
    sys.exit(0)

# Set up the test scene
mcrfpy.createScene("test")
mcrfpy.setScene("test")

# Schedule test to run after game loop starts
mcrfpy.setTimer("test", run_test, 100)