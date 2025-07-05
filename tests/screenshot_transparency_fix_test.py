#!/usr/bin/env python3
"""Test and workaround for transparent screenshot issue"""
import mcrfpy
from mcrfpy import automation
from datetime import datetime
import sys

def test_transparency_workaround():
    """Create a full-window opaque background to fix transparency"""
    print("=== Screenshot Transparency Fix Test ===\n")
    
    # Create a scene
    mcrfpy.createScene("opaque_test")
    mcrfpy.setScene("opaque_test")
    ui = mcrfpy.sceneUI("opaque_test")
    
    # WORKAROUND: Create a full-window opaque frame as the first element
    # This acts as an opaque background since the scene clears with transparent
    print("Creating full-window opaque background...")
    background = mcrfpy.Frame(0, 0, 1024, 768,
                             fill_color=mcrfpy.Color(50, 50, 50),  # Dark gray
                             outline_color=None,
                             outline=0.0)
    ui.append(background)
    print("✓ Added opaque background frame")
    
    # Now add normal content on top
    print("\nAdding test content...")
    
    # Red frame
    frame1 = mcrfpy.Frame(100, 100, 200, 150,
                         fill_color=mcrfpy.Color(255, 0, 0),
                         outline_color=mcrfpy.Color(255, 255, 255),
                         outline=3.0)
    ui.append(frame1)
    
    # Green frame
    frame2 = mcrfpy.Frame(350, 100, 200, 150,
                         fill_color=mcrfpy.Color(0, 255, 0),
                         outline_color=mcrfpy.Color(0, 0, 0),
                         outline=3.0)
    ui.append(frame2)
    
    # Blue frame
    frame3 = mcrfpy.Frame(100, 300, 200, 150,
                         fill_color=mcrfpy.Color(0, 0, 255),
                         outline_color=mcrfpy.Color(255, 255, 0),
                         outline=3.0)
    ui.append(frame3)
    
    # Add text
    caption = mcrfpy.Caption(mcrfpy.Vector(250, 50),
                            text="OPAQUE BACKGROUND TEST",
                            fill_color=mcrfpy.Color(255, 255, 255))
    caption.size = 32
    ui.append(caption)
    
    # Take screenshot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_opaque_fix_{timestamp}.png"
    result = automation.screenshot(filename)
    
    print(f"\nScreenshot taken: {filename}")
    print(f"Result: {result}")
    
    print("\n=== Analysis ===")
    print("The issue is that PyScene::render() calls clear() without a color parameter.")
    print("SFML's default clear color is transparent black (0,0,0,0).")
    print("In windowed mode, the window provides an opaque background.")
    print("In headless mode, the RenderTexture preserves the transparency.")
    print("\nWORKAROUND: Always add a full-window opaque Frame as the first UI element.")
    print("FIX: Modify PyScene.cpp and UITestScene.cpp to use clear(sf::Color::Black)")
    
    sys.exit(0)

# Run immediately
test_transparency_workaround()