#!/usr/bin/env python3
"""Test UIFrame clipping functionality"""

import mcrfpy
from mcrfpy import Color, Frame, Caption
from mcrfpy import automation
import sys

def test_clipping(runtime):
    """Test that clip_children property works correctly"""
    mcrfpy.delTimer("test_clipping")

    print("Testing UIFrame clipping functionality...")

    # Create test scene
    scene = mcrfpy.sceneUI("test")

    # Create parent frame with clipping disabled (default)
    parent1 = Frame(x=50, y=50, w=200, h=150,
                   fill_color=Color(100, 100, 200),
                   outline_color=Color(255, 255, 255),
                   outline=2)
    parent1.name = "parent1"
    scene.append(parent1)

    # Create parent frame with clipping enabled
    parent2 = Frame(x=300, y=50, w=200, h=150,
                   fill_color=Color(200, 100, 100),
                   outline_color=Color(255, 255, 255),
                   outline=2)
    parent2.name = "parent2"
    parent2.clip_children = True
    scene.append(parent2)

    # Add captions to both frames
    caption1 = Caption(text="This text should overflow", x=10, y=10)
    caption1.font_size = 16
    caption1.fill_color = Color(255, 255, 255)
    parent1.children.append(caption1)

    caption2 = Caption(text="This text should be clipped", x=10, y=10)
    caption2.font_size = 16
    caption2.fill_color = Color(255, 255, 255)
    parent2.children.append(caption2)

    # Add child frames that extend beyond parent bounds
    child1 = Frame(x=150, y=100, w=100, h=100,
                   fill_color=Color(50, 255, 50),
                   outline_color=Color(0, 0, 0),
                   outline=1)
    parent1.children.append(child1)

    child2 = Frame(x=150, y=100, w=100, h=100,
                   fill_color=Color(50, 255, 50),
                   outline_color=Color(0, 0, 0),
                   outline=1)
    parent2.children.append(child2)

    # Take screenshot
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
        sys.exit(1)
    except TypeError as e:
        print(f"PASS: clip_children correctly rejected non-boolean: {e}")

    print("\nTest completed successfully!")
    sys.exit(0)

# Main execution
print("Creating test scene...")
mcrfpy.createScene("test")
mcrfpy.setScene("test")

# Schedule the test
mcrfpy.setTimer("test_clipping", test_clipping, 100)

print("Test scheduled, running...")
