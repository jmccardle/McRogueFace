#!/usr/bin/env python3
"""Validate screenshot functionality and analyze pixel data"""
import mcrfpy
from mcrfpy import automation
from datetime import datetime
import sys

def test_screenshot_validation():
    """Create visible content and validate screenshot output"""
    print("=== Screenshot Validation Test ===\n")
    
    # Create a scene with bright, visible content
    mcrfpy.createScene("screenshot_validation")
    mcrfpy.setScene("screenshot_validation")
    ui = mcrfpy.sceneUI("screenshot_validation")
    
    # Create multiple colorful elements to ensure visibility
    print("Creating UI elements...")
    
    # Bright red frame with white outline
    frame1 = mcrfpy.Frame(50, 50, 300, 200,
                         fill_color=mcrfpy.Color(255, 0, 0),      # Bright red
                         outline_color=mcrfpy.Color(255, 255, 255), # White
                         outline=5.0)
    ui.append(frame1)
    print("Added red frame at (50, 50)")
    
    # Bright green frame
    frame2 = mcrfpy.Frame(400, 50, 300, 200,
                         fill_color=mcrfpy.Color(0, 255, 0),      # Bright green
                         outline_color=mcrfpy.Color(0, 0, 0),     # Black
                         outline=3.0)
    ui.append(frame2)
    print("Added green frame at (400, 50)")
    
    # Blue frame
    frame3 = mcrfpy.Frame(50, 300, 300, 200,
                         fill_color=mcrfpy.Color(0, 0, 255),      # Bright blue
                         outline_color=mcrfpy.Color(255, 255, 0), # Yellow
                         outline=4.0)
    ui.append(frame3)
    print("Added blue frame at (50, 300)")
    
    # Add text captions
    caption1 = mcrfpy.Caption(mcrfpy.Vector(60, 60),
                             text="RED FRAME TEST",
                             fill_color=mcrfpy.Color(255, 255, 255))
    caption1.size = 24
    frame1.children.append(caption1)
    
    caption2 = mcrfpy.Caption(mcrfpy.Vector(410, 60),
                             text="GREEN FRAME TEST",
                             fill_color=mcrfpy.Color(0, 0, 0))
    caption2.size = 24
    ui.append(caption2)
    
    caption3 = mcrfpy.Caption(mcrfpy.Vector(60, 310),
                             text="BLUE FRAME TEST",
                             fill_color=mcrfpy.Color(255, 255, 0))
    caption3.size = 24
    ui.append(caption3)
    
    # White background frame to ensure non-transparent background
    background = mcrfpy.Frame(0, 0, 1024, 768,
                             fill_color=mcrfpy.Color(200, 200, 200))  # Light gray
    # Insert at beginning so it's behind everything
    ui.remove(len(ui) - 1)  # Remove to re-add at start
    ui.append(background)
    # Re-add all other elements on top
    for frame in [frame1, frame2, frame3, caption2, caption3]:
        ui.append(frame)
    
    print(f"\nTotal UI elements: {len(ui)}")
    
    # Take multiple screenshots with different names
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    screenshots = [
        f"validate_screenshot_basic_{timestamp}.png",
        f"validate_screenshot_with_spaces {timestamp}.png",
        f"validate_screenshot_final_{timestamp}.png"
    ]
    
    print("\nTaking screenshots...")
    for i, filename in enumerate(screenshots):
        result = automation.screenshot(filename)
        print(f"Screenshot {i+1}: {filename} - Result: {result}")
    
    # Test invalid cases
    print("\nTesting edge cases...")
    
    # Empty filename
    result = automation.screenshot("")
    print(f"Empty filename result: {result}")
    
    # Very long filename
    long_name = "x" * 200 + ".png"
    result = automation.screenshot(long_name)
    print(f"Long filename result: {result}")
    
    print("\n=== Test Complete ===")
    print("Check the PNG files to see if they contain visible content.")
    print("If they're transparent, the headless renderer may not be working correctly.")
    
    # List what should be visible
    print("\nExpected content:")
    print("- Light gray background (200, 200, 200)")
    print("- Red frame with white outline at (50, 50)")
    print("- Green frame with black outline at (400, 50)")
    print("- Blue frame with yellow outline at (50, 300)")
    print("- White, black, and yellow text labels")
    
    sys.exit(0)

# Run the test immediately
test_screenshot_validation()