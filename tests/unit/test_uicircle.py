#!/usr/bin/env python3
"""Test UICircle class implementation - Issue #129"""
import mcrfpy
from mcrfpy import automation
import sys

def take_screenshot(timer, runtime):
    """Take screenshot after render completes"""
    timer.stop()
    automation.screenshot("test_uicircle_result.png")

    print("Screenshot saved to test_uicircle_result.png")
    print("PASS - UICircle test completed")
    sys.exit(0)

def run_test(timer, runtime):
    """Main test - runs after scene is set up"""
    timer.stop()

    # Get the scene UI
    ui = test.children

    # Test 1: Create circles with different parameters
    print("Test 1: Creating circles...")

    # Simple circle - just radius
    c1 = mcrfpy.Circle(radius=50)
    c1.center = (100, 100)
    c1.fill_color = mcrfpy.Color(255, 0, 0)  # Red
    ui.append(c1)
    print(f"  Circle 1: {c1}")

    # Circle with center specified
    c2 = mcrfpy.Circle(radius=30, center=(250, 100), fill_color=mcrfpy.Color(0, 255, 0))
    ui.append(c2)
    print(f"  Circle 2: {c2}")

    # Circle with outline
    c3 = mcrfpy.Circle(
        radius=40,
        center=(400, 100),
        fill_color=mcrfpy.Color(0, 0, 255),
        outline_color=mcrfpy.Color(255, 255, 0),
        outline=5.0
    )
    ui.append(c3)
    print(f"  Circle 3: {c3}")

    # Transparent fill with outline only
    c4 = mcrfpy.Circle(
        radius=35,
        center=(550, 100),
        fill_color=mcrfpy.Color(0, 0, 0, 0),
        outline_color=mcrfpy.Color(255, 255, 255),
        outline=3.0
    )
    ui.append(c4)
    print(f"  Circle 4: {c4}")

    # Test 2: Verify properties
    print("\nTest 2: Verifying properties...")
    assert c1.radius == 50, f"Expected radius 50, got {c1.radius}"
    print(f"  c1.radius = {c1.radius}")

    # Check center
    center = c2.center
    print(f"  c2.center = ({center.x}, {center.y})")

    # Test 3: Modify properties
    print("\nTest 3: Modifying properties...")
    c1.radius = 60
    assert c1.radius == 60, f"Expected radius 60, got {c1.radius}"
    print(f"  Modified c1.radius = {c1.radius}")

    c2.fill_color = mcrfpy.Color(128, 0, 128)  # Purple
    print(f"  Modified c2.fill_color")

    # Test 4: Test visibility and opacity
    print("\nTest 4: Testing visibility and opacity...")
    c5 = mcrfpy.Circle(radius=25, center=(100, 200), fill_color=mcrfpy.Color(255, 128, 0))
    c5.opacity = 0.5
    ui.append(c5)
    print(f"  c5.opacity = {c5.opacity}")

    c6 = mcrfpy.Circle(radius=25, center=(175, 200), fill_color=mcrfpy.Color(255, 128, 0))
    c6.visible = False
    ui.append(c6)
    print(f"  c6.visible = {c6.visible}")

    # Test 5: Test z_index
    print("\nTest 5: Testing z_index...")
    c7 = mcrfpy.Circle(radius=40, center=(300, 200), fill_color=mcrfpy.Color(0, 255, 255))
    c7.z_index = 100
    ui.append(c7)

    c8 = mcrfpy.Circle(radius=30, center=(320, 200), fill_color=mcrfpy.Color(255, 0, 255))
    c8.z_index = 50
    ui.append(c8)
    print(f"  c7.z_index = {c7.z_index}, c8.z_index = {c8.z_index}")

    # Test 6: Test name property
    print("\nTest 6: Testing name property...")
    c9 = mcrfpy.Circle(radius=20, center=(450, 200), fill_color=mcrfpy.Color(128, 128, 128), name="test_circle")
    ui.append(c9)
    assert c9.name == "test_circle", f"Expected name 'test_circle', got '{c9.name}'"
    print(f"  c9.name = '{c9.name}'")

    # Test 7: Test get_bounds
    print("\nTest 7: Testing get_bounds...")
    bounds = c1.get_bounds()
    print(f"  c1.get_bounds() = {bounds}")

    # Test 8: Test move method
    print("\nTest 8: Testing move method...")
    old_center = (c1.center.x, c1.center.y)
    c1.move(10, 10)
    new_center = (c1.center.x, c1.center.y)
    print(f"  c1 moved from {old_center} to {new_center}")

    # Schedule screenshot for next frame
    global screenshot_timer
    screenshot_timer = mcrfpy.Timer("screenshot", take_screenshot, 50, once=True)

# Create a test scene
test = mcrfpy.Scene("test")
test.activate()

# Schedule test to run after game loop starts
test_timer = mcrfpy.Timer("test", run_test, 50, once=True)
