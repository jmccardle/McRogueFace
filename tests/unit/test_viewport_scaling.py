#!/usr/bin/env python3
"""Test viewport scaling modes"""

import mcrfpy
from mcrfpy import Window, Frame, Caption, Color, Vector
import sys

def test_viewport_modes(timer, runtime):
    """Test all three viewport scaling modes"""
    timer.stop()
    
    print("Testing viewport scaling modes...")
    
    # Get window singleton
    window = Window.get()
    
    # Test initial state
    print(f"Initial game resolution: {window.game_resolution}")
    print(f"Initial scaling mode: {window.scaling_mode}")
    print(f"Window resolution: {window.resolution}")
    
    # Create test scene with visual elements
    scene = test.children
    
    # Create a frame that fills the game resolution to show boundaries
    game_res = window.game_resolution
    boundary = Frame(pos=(0, 0), size=(game_res[0], game_res[1]),
                    fill_color=Color(50, 50, 100),
                    outline_color=Color(255, 255, 255),
                    outline=2)
    boundary.name = "boundary"
    scene.append(boundary)
    
    # Add corner markers
    corner_size = 50
    corners = [
        (0, 0, "TL"),  # Top-left
        (game_res[0] - corner_size, 0, "TR"),  # Top-right
        (0, game_res[1] - corner_size, "BL"),  # Bottom-left
        (game_res[0] - corner_size, game_res[1] - corner_size, "BR")  # Bottom-right
    ]
    
    for x, y, label in corners:
        corner = Frame(pos=(x, y), size=(corner_size, corner_size),
                      fill_color=Color(255, 100, 100),
                      outline_color=Color(255, 255, 255),
                      outline=1)
        scene.append(corner)
        
        text = Caption(text=label, pos=(x + 5, y + 5))
        text.font_size = 20
        text.fill_color = Color(255, 255, 255)
        scene.append(text)
    
    # Add center crosshair
    center_x = game_res[0] // 2
    center_y = game_res[1] // 2
    h_line = Frame(pos=(center_x - 50, center_y - 1), size=(100, 2),
                  fill_color=Color(255, 255, 0))
    v_line = Frame(pos=(center_x - 1, center_y - 50), size=(2, 100),
                  fill_color=Color(255, 255, 0))
    scene.append(h_line)
    scene.append(v_line)
    
    # Add mode indicator
    mode_text = Caption(text=f"Mode: {window.scaling_mode}", pos=(10, 10))
    mode_text.font_size = 24
    mode_text.fill_color = Color(255, 255, 255)
    mode_text.name = "mode_text"
    scene.append(mode_text)

    # Add instructions
    instructions = Caption(text="Press 1: Center mode (1:1 pixels)\n"
                               "Press 2: Stretch mode (fill window)\n"
                               "Press 3: Fit mode (maintain aspect ratio)\n"
                               "Press R: Change resolution\n"
                               "Press G: Change game resolution\n"
                               "Press Esc: Exit",
                          pos=(10, 40))
    instructions.font_size = 14
    instructions.fill_color = Color(200, 200, 200)
    scene.append(instructions)
    
    # Test changing modes
    def test_mode_changes(t, r):
        t.stop()
        from mcrfpy import automation

        print("\nTesting scaling modes:")

        # Test center mode
        window.scaling_mode = "center"
        print(f"Set to center mode: {window.scaling_mode}")
        mode_text.text = f"Mode: center (1:1 pixels)"
        automation.screenshot("viewport_center_mode.png")

        # Schedule next mode test
        mcrfpy.Timer("test_stretch", test_stretch_mode, 1000, once=True)

    def test_stretch_mode(t, r):
        t.stop()
        from mcrfpy import automation

        window.scaling_mode = "stretch"
        print(f"Set to stretch mode: {window.scaling_mode}")
        mode_text.text = f"Mode: stretch (fill window)"
        automation.screenshot("viewport_stretch_mode.png")

        # Schedule next mode test
        mcrfpy.Timer("test_fit", test_fit_mode, 1000, once=True)

    def test_fit_mode(t, r):
        t.stop()
        from mcrfpy import automation

        window.scaling_mode = "fit"
        print(f"Set to fit mode: {window.scaling_mode}")
        mode_text.text = f"Mode: fit (aspect ratio maintained)"
        automation.screenshot("viewport_fit_mode.png")

        # Test different window sizes
        mcrfpy.Timer("test_resize", test_window_resize, 1000, once=True)

    def test_window_resize(t, r):
        t.stop()
        from mcrfpy import automation

        print("\nTesting window resize with fit mode:")

        # Make window wider (skip in headless mode)
        try:
            window.resolution = (1280, 720)
            print(f"Window resized to: {window.resolution}")
            automation.screenshot("viewport_fit_wide.png")
            # Make window taller
            mcrfpy.Timer("test_tall", test_tall_window, 1000, once=True)
        except RuntimeError as e:
            print(f"  Skipping window resize tests (headless mode): {e}")
            mcrfpy.Timer("test_game_res", test_game_resolution, 100, once=True)

    def test_tall_window(t, r):
        t.stop()
        from mcrfpy import automation

        try:
            window.resolution = (800, 1000)
            print(f"Window resized to: {window.resolution}")
            automation.screenshot("viewport_fit_tall.png")
        except RuntimeError as e:
            print(f"  Skipping tall window test (headless mode): {e}")

        # Test game resolution change
        mcrfpy.Timer("test_game_res", test_game_resolution, 1000, once=True)

    def test_game_resolution(t, r):
        t.stop()
        
        print("\nTesting game resolution change:")
        window.game_resolution = (800, 600)
        print(f"Game resolution changed to: {window.game_resolution}")
        
        # Note: UI elements won't automatically reposition, but viewport will adjust
        
        print("\nTest completed!")
        print("Screenshots saved:")
        print("  - viewport_center_mode.png")
        print("  - viewport_stretch_mode.png")
        print("  - viewport_fit_mode.png")
        print("  - viewport_fit_wide.png")
        print("  - viewport_fit_tall.png")
        
        # Restore original settings (skip resolution in headless mode)
        try:
            window.resolution = (1024, 768)
        except RuntimeError:
            pass  # Headless mode - can't change resolution
        window.game_resolution = (1024, 768)
        window.scaling_mode = "fit"

        sys.exit(0)

    # Start test sequence
    mcrfpy.Timer("test_modes", test_mode_changes, 500, once=True)

# Set up keyboard handler for manual testing
def handle_keypress(key, state):
    if state != "start":
        return
        
    window = Window.get()
    scene = test.children
    mode_text = None
    for elem in scene:
        if hasattr(elem, 'name') and elem.name == "mode_text":
            mode_text = elem
            break
    
    if key == "1":
        window.scaling_mode = "center"
        if mode_text:
            mode_text.text = f"Mode: center (1:1 pixels)"
        print(f"Switched to center mode")
    elif key == "2":
        window.scaling_mode = "stretch"
        if mode_text:
            mode_text.text = f"Mode: stretch (fill window)"
        print(f"Switched to stretch mode")
    elif key == "3":
        window.scaling_mode = "fit"
        if mode_text:
            mode_text.text = f"Mode: fit (aspect ratio maintained)"
        print(f"Switched to fit mode")
    elif key == "r":
        # Cycle through some resolutions
        current = window.resolution
        if current == (1024, 768):
            window.resolution = (1280, 720)
        elif current == (1280, 720):
            window.resolution = (800, 600)
        else:
            window.resolution = (1024, 768)
        print(f"Window resolution: {window.resolution}")
    elif key == "g":
        # Cycle game resolutions
        current = window.game_resolution
        if current == (1024, 768):
            window.game_resolution = (800, 600)
        elif current == (800, 600):
            window.game_resolution = (640, 480)
        else:
            window.game_resolution = (1024, 768)
        print(f"Game resolution: {window.game_resolution}")
    elif key == "escape":
        sys.exit(0)

# Main execution
print("Creating viewport test scene...")
test = mcrfpy.Scene("test")
test.activate()
test.on_key = handle_keypress

# Schedule the test
test_viewport_timer = mcrfpy.Timer("test_viewport", test_viewport_modes, 100, once=True)

print("Viewport test running...")
print("Use number keys to switch modes, R to resize window, G to change game resolution")