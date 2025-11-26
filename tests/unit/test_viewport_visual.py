#!/usr/bin/env python3
"""Visual viewport test with screenshots"""

import mcrfpy
from mcrfpy import Window, Frame, Caption, Color
import sys

def test_viewport_visual(runtime):
    """Visual test of viewport modes"""
    mcrfpy.delTimer("test")
    
    print("Creating visual viewport test...")
    
    # Get window singleton
    window = Window.get()
    
    # Create test scene
    scene = mcrfpy.sceneUI("test")
    
    # Create visual elements at game resolution boundaries
    game_res = window.game_resolution
    
    # Full boundary frame
    boundary = Frame(0, 0, game_res[0], game_res[1],
                    fill_color=Color(40, 40, 80),
                    outline_color=Color(255, 255, 0),
                    outline=3)
    scene.append(boundary)
    
    # Corner markers
    corner_size = 100
    colors = [
        Color(255, 100, 100),  # Red TL
        Color(100, 255, 100),  # Green TR
        Color(100, 100, 255),  # Blue BL
        Color(255, 255, 100),  # Yellow BR
    ]
    positions = [
        (0, 0),  # Top-left
        (game_res[0] - corner_size, 0),  # Top-right
        (0, game_res[1] - corner_size),  # Bottom-left
        (game_res[0] - corner_size, game_res[1] - corner_size)  # Bottom-right
    ]
    labels = ["TL", "TR", "BL", "BR"]
    
    for (x, y), color, label in zip(positions, colors, labels):
        corner = Frame(x, y, corner_size, corner_size,
                      fill_color=color,
                      outline_color=Color(255, 255, 255),
                      outline=2)
        scene.append(corner)
        
        text = Caption(x + 10, y + 10, label)
        text.font_size = 32
        text.fill_color = Color(0, 0, 0)
        scene.append(text)
    
    # Center crosshair
    center_x = game_res[0] // 2
    center_y = game_res[1] // 2
    h_line = Frame(0, center_y - 1, game_res[0], 2,
                  fill_color=Color(255, 255, 255, 128))
    v_line = Frame(center_x - 1, 0, 2, game_res[1],
                  fill_color=Color(255, 255, 255, 128))
    scene.append(h_line)
    scene.append(v_line)
    
    # Mode text
    mode_text = Caption(center_x - 100, center_y - 50, 
                       f"Mode: {window.scaling_mode}")
    mode_text.font_size = 36
    mode_text.fill_color = Color(255, 255, 255)
    scene.append(mode_text)
    
    # Resolution text
    res_text = Caption(center_x - 150, center_y + 10,
                      f"Game: {game_res[0]}x{game_res[1]}")
    res_text.font_size = 24
    res_text.fill_color = Color(200, 200, 200)
    scene.append(res_text)
    
    from mcrfpy import automation
    
    # Test different modes and window sizes
    def test_sequence(runtime):
        mcrfpy.delTimer("seq")
        
        # Test 1: Fit mode with original size
        print("Test 1: Fit mode, original window size")
        automation.screenshot("viewport_01_fit_original.png")
        
        # Test 2: Wider window
        window.resolution = (1400, 768)
        print(f"Test 2: Fit mode, wider window {window.resolution}")
        automation.screenshot("viewport_02_fit_wide.png")
        
        # Test 3: Taller window  
        window.resolution = (1024, 900)
        print(f"Test 3: Fit mode, taller window {window.resolution}")
        automation.screenshot("viewport_03_fit_tall.png")
        
        # Test 4: Center mode
        window.scaling_mode = "center"
        mode_text.text = "Mode: center"
        print(f"Test 4: Center mode {window.resolution}")
        automation.screenshot("viewport_04_center.png")
        
        # Test 5: Stretch mode
        window.scaling_mode = "stretch"
        mode_text.text = "Mode: stretch"
        window.resolution = (1280, 720)
        print(f"Test 5: Stretch mode {window.resolution}")
        automation.screenshot("viewport_05_stretch.png")
        
        # Test 6: Small window with fit
        window.scaling_mode = "fit"
        mode_text.text = "Mode: fit"
        window.resolution = (640, 480)
        print(f"Test 6: Fit mode, small window {window.resolution}")
        automation.screenshot("viewport_06_fit_small.png")
        
        print("\nViewport visual test completed!")
        print("Screenshots saved:")
        print("  - viewport_01_fit_original.png")
        print("  - viewport_02_fit_wide.png")
        print("  - viewport_03_fit_tall.png")
        print("  - viewport_04_center.png")
        print("  - viewport_05_stretch.png")
        print("  - viewport_06_fit_small.png")
        
        sys.exit(0)
    
    # Start test sequence after a short delay
    mcrfpy.setTimer("seq", test_sequence, 500)

# Main execution
print("Starting visual viewport test...")
mcrfpy.createScene("test")
mcrfpy.setScene("test")
mcrfpy.setTimer("test", test_viewport_visual, 100)
print("Test scheduled...")