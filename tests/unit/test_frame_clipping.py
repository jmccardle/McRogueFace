#!/usr/bin/env python3
"""Test UIFrame clipping functionality"""

import mcrfpy
from mcrfpy import Color, Frame, Caption, Vector
import sys

def test_clipping(runtime):
    """Test that clip_children property works correctly"""
    mcrfpy.delTimer("test_clipping")
    
    print("Testing UIFrame clipping functionality...")
    
    # Create test scene
    scene = mcrfpy.sceneUI("test")
    
    # Create parent frame with clipping disabled (default)
    parent1 = Frame(50, 50, 200, 150, 
                   fill_color=Color(100, 100, 200),
                   outline_color=Color(255, 255, 255),
                   outline=2)
    parent1.name = "parent1"
    scene.append(parent1)
    
    # Create parent frame with clipping enabled
    parent2 = Frame(300, 50, 200, 150,
                   fill_color=Color(200, 100, 100),
                   outline_color=Color(255, 255, 255),
                   outline=2)
    parent2.name = "parent2"
    parent2.clip_children = True
    scene.append(parent2)
    
    # Add captions to both frames
    caption1 = Caption(10, 10, "This text should overflow the frame bounds")
    caption1.font_size = 16
    caption1.fill_color = Color(255, 255, 255)
    parent1.children.append(caption1)
    
    caption2 = Caption(10, 10, "This text should be clipped to frame bounds")
    caption2.font_size = 16
    caption2.fill_color = Color(255, 255, 255)
    parent2.children.append(caption2)
    
    # Add child frames that extend beyond parent bounds
    child1 = Frame(150, 100, 100, 100,
                   fill_color=Color(50, 255, 50),
                   outline_color=Color(0, 0, 0),
                   outline=1)
    parent1.children.append(child1)
    
    child2 = Frame(150, 100, 100, 100,
                   fill_color=Color(50, 255, 50),
                   outline_color=Color(0, 0, 0),
                   outline=1)
    parent2.children.append(child2)
    
    # Add caption to show clip state
    status = Caption(50, 250, 
                     f"Left frame: clip_children={parent1.clip_children}\n"
                     f"Right frame: clip_children={parent2.clip_children}")
    status.font_size = 14
    status.fill_color = Color(255, 255, 255)
    scene.append(status)
    
    # Add instructions
    instructions = Caption(50, 300,
                          "Left: Children should overflow (no clipping)\n"
                          "Right: Children should be clipped to frame bounds\n"
                          "Press 'c' to toggle clipping on left frame")
    instructions.font_size = 12
    instructions.fill_color = Color(200, 200, 200)
    scene.append(instructions)
    
    # Take screenshot
    from mcrfpy import Window, automation
    automation.screenshot("frame_clipping_test.png")
    
    print(f"Parent1 clip_children: {parent1.clip_children}")
    print(f"Parent2 clip_children: {parent2.clip_children}")
    
    # Test toggling clip_children
    parent1.clip_children = True
    print(f"After toggle - Parent1 clip_children: {parent1.clip_children}")
    
    # Verify the property setter works
    try:
        parent1.clip_children = "not a bool"  # Should raise TypeError
        print("ERROR: clip_children accepted non-boolean value")
    except TypeError as e:
        print(f"PASS: clip_children correctly rejected non-boolean: {e}")
    
    # Test with animations
    def animate_frames(runtime):
        mcrfpy.delTimer("animate")
        # Animate child frames to show clipping in action
        # Note: For now, just move the frames manually to demonstrate clipping
        parent1.children[1].x = 50  # Move child frame
        parent2.children[1].x = 50  # Move child frame
        
        # Take another screenshot after starting animation
        mcrfpy.setTimer("screenshot2", take_second_screenshot, 500)
    
    def take_second_screenshot(runtime):
        mcrfpy.delTimer("screenshot2")
        automation.screenshot("frame_clipping_animated.png")
        print("\nTest completed successfully!")
        print("Screenshots saved:")
        print("  - frame_clipping_test.png (initial state)")
        print("  - frame_clipping_animated.png (with animation)")
        sys.exit(0)
    
    # Start animation after a short delay
    mcrfpy.setTimer("animate", animate_frames, 100)

# Main execution
print("Creating test scene...")
mcrfpy.createScene("test")
mcrfpy.setScene("test")

# Set up keyboard handler to toggle clipping
def handle_keypress(key, modifiers):
    if key == "c":
        scene = mcrfpy.sceneUI("test")
        parent1 = scene[0]  # First frame
        parent1.clip_children = not parent1.clip_children
        print(f"Toggled parent1 clip_children to: {parent1.clip_children}")

mcrfpy.keypressScene(handle_keypress)

# Schedule the test
mcrfpy.setTimer("test_clipping", test_clipping, 100)

print("Test scheduled, running...")