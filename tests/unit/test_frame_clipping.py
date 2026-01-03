#!/usr/bin/env python3
"""Test UIFrame clipping functionality"""

import mcrfpy
from mcrfpy import Color, Frame, Caption
import sys

# Module-level state to avoid closures
_test_state = {}

def take_second_screenshot(runtime):
    """Take final screenshot and exit"""
    mcrfpy.delTimer("screenshot2")
    from mcrfpy import automation
    automation.screenshot("frame_clipping_animated.png")
    print("\nTest completed successfully!")
    print("Screenshots saved:")
    print("  - frame_clipping_test.png (initial state)")
    print("  - frame_clipping_animated.png (with animation)")
    sys.exit(0)

def animate_frames(runtime):
    """Animate frames to demonstrate clipping"""
    mcrfpy.delTimer("animate")
    scene = test.children
    # Move child frames
    parent1 = scene[0]
    parent2 = scene[1]
    parent1.children[1].x = 50
    parent2.children[1].x = 50
    mcrfpy.setTimer("screenshot2", take_second_screenshot, 500)

def test_clipping(runtime):
    """Test that clip_children property works correctly"""
    mcrfpy.delTimer("test_clipping")

    print("Testing UIFrame clipping functionality...")

    scene = test.children

    # Create parent frame with clipping disabled (default)
    parent1 = Frame(pos=(50, 50), size=(200, 150),
                   fill_color=Color(100, 100, 200),
                   outline_color=Color(255, 255, 255),
                   outline=2)
    parent1.name = "parent1"
    scene.append(parent1)

    # Create parent frame with clipping enabled
    parent2 = Frame(pos=(300, 50), size=(200, 150),
                   fill_color=Color(200, 100, 100),
                   outline_color=Color(255, 255, 255),
                   outline=2)
    parent2.name = "parent2"
    parent2.clip_children = True
    scene.append(parent2)

    # Add captions to both frames
    caption1 = Caption(text="This text should overflow the frame bounds", pos=(10, 10))
    caption1.font_size = 16
    caption1.fill_color = Color(255, 255, 255)
    parent1.children.append(caption1)

    caption2 = Caption(text="This text should be clipped to frame bounds", pos=(10, 10))
    caption2.font_size = 16
    caption2.fill_color = Color(255, 255, 255)
    parent2.children.append(caption2)

    # Add child frames that extend beyond parent bounds
    child1 = Frame(pos=(150, 100), size=(100, 100),
                   fill_color=Color(50, 255, 50),
                   outline_color=Color(0, 0, 0),
                   outline=1)
    parent1.children.append(child1)

    child2 = Frame(pos=(150, 100), size=(100, 100),
                   fill_color=Color(50, 255, 50),
                   outline_color=Color(0, 0, 0),
                   outline=1)
    parent2.children.append(child2)

    # Add caption to show clip state
    status = Caption(text=f"Left frame: clip_children={parent1.clip_children}\n"
                          f"Right frame: clip_children={parent2.clip_children}",
                     pos=(50, 250))
    status.font_size = 14
    status.fill_color = Color(255, 255, 255)
    scene.append(status)

    # Add instructions
    instructions = Caption(text="Left: Children should overflow (no clipping)\n"
                               "Right: Children should be clipped to frame bounds\n"
                               "Press 'c' to toggle clipping on left frame",
                          pos=(50, 300))
    instructions.font_size = 12
    instructions.fill_color = Color(200, 200, 200)
    scene.append(instructions)

    # Take screenshot
    from mcrfpy import automation
    automation.screenshot("frame_clipping_test.png")

    print(f"Parent1 clip_children: {parent1.clip_children}")
    print(f"Parent2 clip_children: {parent2.clip_children}")

    # Test toggling clip_children
    parent1.clip_children = True
    print(f"After toggle - Parent1 clip_children: {parent1.clip_children}")

    # Verify the property setter works
    try:
        parent1.clip_children = "not a bool"
        print("ERROR: clip_children accepted non-boolean value")
    except TypeError as e:
        print(f"PASS: clip_children correctly rejected non-boolean: {e}")

    # Start animation after a short delay
    mcrfpy.setTimer("animate", animate_frames, 100)

def handle_keypress(key, modifiers):
    if key == "c":
        scene = test.children
        parent1 = scene[0]
        parent1.clip_children = not parent1.clip_children
        print(f"Toggled parent1 clip_children to: {parent1.clip_children}")

# Main execution
print("Creating test scene...")
test = mcrfpy.Scene("test")
test.activate()
test.on_key = handle_keypress
mcrfpy.setTimer("test_clipping", test_clipping, 100)
print("Test scheduled, running...")
