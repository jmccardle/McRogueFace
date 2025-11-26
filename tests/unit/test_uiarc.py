#!/usr/bin/env python3
"""Test UIArc class implementation - Issue #128 completion"""
import mcrfpy
from mcrfpy import automation
import sys

def take_screenshot(runtime):
    """Take screenshot after render completes"""
    mcrfpy.delTimer("screenshot")
    automation.screenshot("test_uiarc_result.png")

    print("Screenshot saved to test_uiarc_result.png")
    print("PASS - UIArc test completed")
    sys.exit(0)

def run_test(runtime):
    """Main test - runs after scene is set up"""
    mcrfpy.delTimer("test")

    # Get the scene UI
    ui = mcrfpy.sceneUI("test")

    # Test 1: Create arcs with different parameters
    print("Test 1: Creating arcs...")

    # Simple arc - 90 degree quarter circle
    a1 = mcrfpy.Arc(center=(100, 100), radius=50, start_angle=0, end_angle=90,
                    color=mcrfpy.Color(255, 0, 0), thickness=5)
    ui.append(a1)
    print(f"  Arc 1: {a1}")

    # Half circle
    a2 = mcrfpy.Arc(center=(250, 100), radius=40, start_angle=0, end_angle=180,
                    color=mcrfpy.Color(0, 255, 0), thickness=3)
    ui.append(a2)
    print(f"  Arc 2: {a2}")

    # Three-quarter arc
    a3 = mcrfpy.Arc(center=(400, 100), radius=45, start_angle=45, end_angle=315,
                    color=mcrfpy.Color(0, 0, 255), thickness=4)
    ui.append(a3)
    print(f"  Arc 3: {a3}")

    # Full circle (360 degrees)
    a4 = mcrfpy.Arc(center=(550, 100), radius=35, start_angle=0, end_angle=360,
                    color=mcrfpy.Color(255, 255, 0), thickness=2)
    ui.append(a4)
    print(f"  Arc 4: {a4}")

    # Test 2: Verify properties
    print("\nTest 2: Verifying properties...")
    assert a1.radius == 50, f"Expected radius 50, got {a1.radius}"
    print(f"  a1.radius = {a1.radius}")

    assert a1.start_angle == 0, f"Expected start_angle 0, got {a1.start_angle}"
    assert a1.end_angle == 90, f"Expected end_angle 90, got {a1.end_angle}"
    print(f"  a1.start_angle = {a1.start_angle}, a1.end_angle = {a1.end_angle}")

    assert a1.thickness == 5, f"Expected thickness 5, got {a1.thickness}"
    print(f"  a1.thickness = {a1.thickness}")

    # Test 3: Modify properties
    print("\nTest 3: Modifying properties...")
    a1.radius = 60
    assert a1.radius == 60, f"Expected radius 60, got {a1.radius}"
    print(f"  Modified a1.radius = {a1.radius}")

    a1.start_angle = 30
    a1.end_angle = 120
    print(f"  Modified a1 angles: {a1.start_angle} to {a1.end_angle}")

    a2.color = mcrfpy.Color(255, 0, 255)  # Magenta
    print(f"  Modified a2.color")

    # Test 4: Test visibility and opacity
    print("\nTest 4: Testing visibility and opacity...")
    a5 = mcrfpy.Arc(center=(100, 250), radius=30, start_angle=0, end_angle=180,
                    color=mcrfpy.Color(255, 128, 0), thickness=3)
    a5.opacity = 0.5
    ui.append(a5)
    print(f"  a5.opacity = {a5.opacity}")

    a6 = mcrfpy.Arc(center=(200, 250), radius=30, start_angle=0, end_angle=180,
                    color=mcrfpy.Color(255, 128, 0), thickness=3)
    a6.visible = False
    ui.append(a6)
    print(f"  a6.visible = {a6.visible}")

    # Test 5: Test z_index
    print("\nTest 5: Testing z_index...")
    a7 = mcrfpy.Arc(center=(350, 250), radius=50, start_angle=0, end_angle=270,
                    color=mcrfpy.Color(0, 255, 255), thickness=10)
    a7.z_index = 100
    ui.append(a7)

    a8 = mcrfpy.Arc(center=(370, 250), radius=40, start_angle=0, end_angle=270,
                    color=mcrfpy.Color(255, 0, 255), thickness=8)
    a8.z_index = 50
    ui.append(a8)
    print(f"  a7.z_index = {a7.z_index}, a8.z_index = {a8.z_index}")

    # Test 6: Test name property
    print("\nTest 6: Testing name property...")
    a9 = mcrfpy.Arc(center=(500, 250), radius=25, start_angle=45, end_angle=135,
                    color=mcrfpy.Color(128, 128, 128), thickness=5, name="test_arc")
    ui.append(a9)
    assert a9.name == "test_arc", f"Expected name 'test_arc', got '{a9.name}'"
    print(f"  a9.name = '{a9.name}'")

    # Test 7: Test get_bounds
    print("\nTest 7: Testing get_bounds...")
    bounds = a1.get_bounds()
    print(f"  a1.get_bounds() = {bounds}")

    # Test 8: Test move method
    print("\nTest 8: Testing move method...")
    old_center = (a1.center.x, a1.center.y)
    a1.move(10, 10)
    new_center = (a1.center.x, a1.center.y)
    print(f"  a1 moved from {old_center} to {new_center}")

    # Test 9: Negative angle span (draws in reverse)
    print("\nTest 9: Testing negative angle span...")
    a10 = mcrfpy.Arc(center=(100, 350), radius=40, start_angle=90, end_angle=0,
                     color=mcrfpy.Color(128, 255, 128), thickness=4)
    ui.append(a10)
    print(f"  Arc 10 (reverse): {a10}")

    # Schedule screenshot for next frame
    mcrfpy.setTimer("screenshot", take_screenshot, 50)

# Create a test scene
mcrfpy.createScene("test")
mcrfpy.setScene("test")

# Schedule test to run after game loop starts
mcrfpy.setTimer("test", run_test, 50)
