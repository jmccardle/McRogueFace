#!/usr/bin/env python3
"""Advanced test for UIFrame clipping with nested frames"""

import mcrfpy
from mcrfpy import Color, Frame, Caption, Vector
import sys

def test_nested_clipping(runtime):
    """Test nested frames with clipping"""
    mcrfpy.delTimer("test_nested_clipping")
    
    print("Testing advanced UIFrame clipping with nested frames...")
    
    # Create test scene
    scene = test.children
    
    # Create outer frame with clipping enabled
    outer = Frame(pos=(50, 50), size=(400, 300),
                  fill_color=Color(50, 50, 150),
                  outline_color=Color(255, 255, 255),
                  outline=3)
    outer.name = "outer"
    outer.clip_children = True
    scene.append(outer)

    # Create inner frame that extends beyond outer bounds
    inner = Frame(pos=(200, 150), size=(300, 200),
                  fill_color=Color(150, 50, 50),
                  outline_color=Color(255, 255, 0),
                  outline=2)
    inner.name = "inner"
    inner.clip_children = True  # Also enable clipping on inner frame
    outer.children.append(inner)
    
    # Add content to inner frame that extends beyond its bounds
    for i in range(5):
        caption = Caption(text=f"Line {i+1}: This text should be double-clipped", pos=(10, 30 * i))
        caption.font_size = 14
        caption.fill_color = Color(255, 255, 255)
        inner.children.append(caption)
    
    # Add a child frame to inner that extends way out
    deeply_nested = Frame(pos=(250, 100), size=(200, 150),
                         fill_color=Color(50, 150, 50),
                         outline_color=Color(255, 0, 255),
                         outline=2)
    deeply_nested.name = "deeply_nested"
    inner.children.append(deeply_nested)
    
    # Add status text
    status = Caption(text="Nested clipping test:\n"
                         "- Blue outer frame clips red inner frame\n"
                         "- Red inner frame clips green deeply nested frame\n"
                         "- All text should be clipped to frame bounds",
                    pos=(50, 380))
    status.font_size = 12
    status.fill_color = Color(200, 200, 200)
    scene.append(status)
    
    # Test render texture size handling
    print(f"Outer frame size: {outer.w}x{outer.h}")
    print(f"Inner frame size: {inner.w}x{inner.h}")
    
    # Dynamically resize frames to test RenderTexture recreation
    def resize_test(runtime):
        mcrfpy.delTimer("resize_test")
        print("Resizing frames to test RenderTexture recreation...")
        outer.w = 450
        outer.h = 350
        inner.w = 350
        inner.h = 250
        print(f"New outer frame size: {outer.w}x{outer.h}")
        print(f"New inner frame size: {inner.w}x{inner.h}")
        
        # Take screenshot after resize
        mcrfpy.setTimer("screenshot_resize", take_resize_screenshot, 500)
    
    def take_resize_screenshot(runtime):
        mcrfpy.delTimer("screenshot_resize")
        from mcrfpy import automation
        automation.screenshot("frame_clipping_resized.png")
        print("\nAdvanced test completed!")
        print("Screenshots saved:")
        print("  - frame_clipping_resized.png (after resize)")
        sys.exit(0)
    
    # Take initial screenshot
    from mcrfpy import automation
    automation.screenshot("frame_clipping_nested.png")
    print("Initial screenshot saved: frame_clipping_nested.png")
    
    # Schedule resize test
    mcrfpy.setTimer("resize_test", resize_test, 1000)

# Main execution
print("Creating advanced test scene...")
test = mcrfpy.Scene("test")
test.activate()

# Schedule the test
mcrfpy.setTimer("test_nested_clipping", test_nested_clipping, 100)

print("Advanced test scheduled, running...")