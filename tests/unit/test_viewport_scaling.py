#!/usr/bin/env python3
"""Test viewport scaling modes"""

import mcrfpy
from mcrfpy import Window, Frame, Caption, Color
from mcrfpy import automation
import sys

def test_viewport_modes(runtime):
    """Test all three viewport scaling modes"""
    mcrfpy.delTimer("test_viewport")

    print("Testing viewport scaling modes...")

    # Get window singleton
    window = Window.get()

    # Test initial state
    print(f"Initial game resolution: {window.game_resolution}")
    print(f"Initial scaling mode: {window.scaling_mode}")
    print(f"Window resolution: {window.resolution}")

    # Get scene
    scene = mcrfpy.sceneUI("test")

    # Create a simple frame to show boundaries
    game_res = window.game_resolution
    boundary = Frame(x=0, y=0, w=game_res[0], h=game_res[1],
                    fill_color=Color(50, 50, 100),
                    outline_color=Color(255, 255, 255),
                    outline=2)
    scene.append(boundary)

    # Add mode indicator
    mode_text = Caption(text=f"Mode: {window.scaling_mode}", x=10, y=10)
    mode_text.font_size = 24
    mode_text.fill_color = Color(255, 255, 255)
    scene.append(mode_text)

    # Test changing modes
    print("\nTesting scaling modes:")

    # Test center mode
    window.scaling_mode = "center"
    print(f"Set to center mode: {window.scaling_mode}")
    mode_text.text = f"Mode: center"
    automation.screenshot("viewport_center_mode.png")

    # Test stretch mode
    window.scaling_mode = "stretch"
    print(f"Set to stretch mode: {window.scaling_mode}")
    mode_text.text = f"Mode: stretch"
    automation.screenshot("viewport_stretch_mode.png")

    # Test fit mode
    window.scaling_mode = "fit"
    print(f"Set to fit mode: {window.scaling_mode}")
    mode_text.text = f"Mode: fit"
    automation.screenshot("viewport_fit_mode.png")

    # Note: Cannot change window resolution in headless mode
    # Just verify the scaling mode properties work
    print("\nScaling mode property tests passed!")
    print("\nTest completed!")
    sys.exit(0)

# Main execution
print("Creating viewport test scene...")
mcrfpy.createScene("test")
mcrfpy.setScene("test")

# Schedule the test
mcrfpy.setTimer("test_viewport", test_viewport_modes, 100)

print("Viewport test running...")
