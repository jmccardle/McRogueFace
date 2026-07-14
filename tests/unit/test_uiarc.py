#!/usr/bin/env python3
"""Test UIArc class implementation - Issue #128 completion"""
import mcrfpy
from mcrfpy import automation
import sys

# Create a test scene
test = mcrfpy.Scene("test")
mcrfpy.current_scene = test

# Get the scene UI
ui = test.children

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
assert a1.start_angle == 30, f"Expected start_angle 30, got {a1.start_angle}"
assert a1.end_angle == 120, f"Expected end_angle 120, got {a1.end_angle}"
print(f"  Modified a1 angles: {a1.start_angle} to {a1.end_angle}")

a2.color = mcrfpy.Color(255, 0, 255)  # Magenta
assert (a2.color.r, a2.color.g, a2.color.b) == (255, 0, 255), \
    f"Expected magenta, got {a2.color}"
print(f"  Modified a2.color")

# Test 4: Test visibility and opacity
print("\nTest 4: Testing visibility and opacity...")
a5 = mcrfpy.Arc(center=(100, 250), radius=30, start_angle=0, end_angle=180,
                color=mcrfpy.Color(255, 128, 0), thickness=3)
a5.opacity = 0.5
ui.append(a5)
assert a5.opacity == 0.5, f"Expected opacity 0.5, got {a5.opacity}"
print(f"  a5.opacity = {a5.opacity}")

a6 = mcrfpy.Arc(center=(200, 250), radius=30, start_angle=0, end_angle=180,
                color=mcrfpy.Color(255, 128, 0), thickness=3)
a6.visible = False
ui.append(a6)
assert a6.visible is False, f"Expected visible False, got {a6.visible}"
print(f"  a6.visible = {a6.visible}")

# Test 5: Test z_index
# NOTE: UICollection.append() auto-assigns z_index (last + 10), so z_index must be
# set AFTER appending or the assignment is overwritten by the collection.
print("\nTest 5: Testing z_index...")
a7 = mcrfpy.Arc(center=(350, 250), radius=50, start_angle=0, end_angle=270,
                color=mcrfpy.Color(0, 255, 255), thickness=10)
ui.append(a7)
a7.z_index = 100

a8 = mcrfpy.Arc(center=(370, 250), radius=40, start_angle=0, end_angle=270,
                color=mcrfpy.Color(255, 0, 255), thickness=8)
ui.append(a8)
a8.z_index = 50
assert a7.z_index == 100, f"Expected z_index 100, got {a7.z_index}"
assert a8.z_index == 50, f"Expected z_index 50, got {a8.z_index}"
print(f"  a7.z_index = {a7.z_index}, a8.z_index = {a8.z_index}")

# Test 6: Test name property
print("\nTest 6: Testing name property...")
a9 = mcrfpy.Arc(center=(500, 250), radius=25, start_angle=45, end_angle=135,
                color=mcrfpy.Color(128, 128, 128), thickness=5, name="test_arc")
ui.append(a9)
assert a9.name == "test_arc", f"Expected name 'test_arc', got '{a9.name}'"
print(f"  a9.name = '{a9.name}'")

# Test 7: Test bounds
# NOTE: get_bounds() was replaced by the .bounds / .global_bounds properties.
# Each returns (offset: Vector, size: Vector); an arc's extent is the circle that
# contains it, so size == 2 * (radius + thickness/2) on both axes.
print("\nTest 7: Testing bounds...")
offset, size = a1.bounds
expected_extent = 2 * (a1.radius + a1.thickness / 2)
assert size.x == expected_extent, f"Expected bounds width {expected_extent}, got {size.x}"
assert size.y == expected_extent, f"Expected bounds height {expected_extent}, got {size.y}"
print(f"  a1.bounds = ({offset}, {size})")

g_offset, g_size = a1.global_bounds
assert (g_size.x, g_size.y) == (size.x, size.y), \
    f"global_bounds size {g_size} should match bounds size {size}"
print(f"  a1.global_bounds = ({g_offset}, {g_size})")

# Test 8: Test move method
print("\nTest 8: Testing move method...")
old_center = (a1.center.x, a1.center.y)
a1.move(10, 10)
new_center = (a1.center.x, a1.center.y)
assert new_center == (old_center[0] + 10, old_center[1] + 10), \
    f"Expected move to offset center by (10, 10): {old_center} -> {new_center}"
# global_bounds tracks the moved arc; local bounds size is unchanged by a move
assert a1.global_bounds[0].x == new_center[0], \
    f"global_bounds should follow center x {new_center[0]}, got {a1.global_bounds[0].x}"
print(f"  a1 moved from {old_center} to {new_center}")

# Test 9: Negative angle span (draws in reverse)
print("\nTest 9: Testing negative angle span...")
a10 = mcrfpy.Arc(center=(100, 350), radius=40, start_angle=90, end_angle=0,
                 color=mcrfpy.Color(128, 255, 128), thickness=4)
ui.append(a10)
assert a10.start_angle == 90 and a10.end_angle == 0, \
    f"Reverse span should be preserved verbatim, got {a10.start_angle} to {a10.end_angle}"
print(f"  Arc 10 (reverse): {a10}")

# All 10 arcs should be in the scene
assert len(ui) == 10, f"Expected 10 arcs in the scene, got {len(ui)}"

# Render a frame and take screenshot
mcrfpy.step(0.01)
automation.screenshot("test_uiarc_result.png")

print("Screenshot saved to test_uiarc_result.png")
print("PASS - UIArc test completed")
sys.exit(0)
