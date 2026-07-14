#!/usr/bin/env python3
"""Test UICircle class implementation - Issue #129"""
import mcrfpy
from mcrfpy import automation
import sys

def rgba(c):
    return (c.r, c.g, c.b, c.a)

# Create a test scene
test = mcrfpy.Scene("test")
mcrfpy.current_scene = test

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
assert (center.x, center.y) == (250, 100), f"Expected center (250, 100), got ({center.x}, {center.y})"
print(f"  c2.center = ({center.x}, {center.y})")

assert c3.outline == 5.0, f"Expected outline 5.0, got {c3.outline}"
assert rgba(c4.fill_color) == (0, 0, 0, 0), f"Expected transparent fill, got {rgba(c4.fill_color)}"
print(f"  c3.outline = {c3.outline}, c4.fill_color = {rgba(c4.fill_color)}")

# Test 3: Modify properties
print("\nTest 3: Modifying properties...")
c1.radius = 60
assert c1.radius == 60, f"Expected radius 60, got {c1.radius}"
print(f"  Modified c1.radius = {c1.radius}")

c2.fill_color = mcrfpy.Color(128, 0, 128)  # Purple
assert rgba(c2.fill_color) == (128, 0, 128, 255), f"Expected purple fill, got {rgba(c2.fill_color)}"
print(f"  Modified c2.fill_color = {rgba(c2.fill_color)}")

# Test 4: Test visibility and opacity
print("\nTest 4: Testing visibility and opacity...")
c5 = mcrfpy.Circle(radius=25, center=(100, 200), fill_color=mcrfpy.Color(255, 128, 0))
c5.opacity = 0.5
ui.append(c5)
assert abs(c5.opacity - 0.5) < 1e-6, f"Expected opacity 0.5, got {c5.opacity}"
print(f"  c5.opacity = {c5.opacity}")

c6 = mcrfpy.Circle(radius=25, center=(175, 200), fill_color=mcrfpy.Color(255, 128, 0))
c6.visible = False
ui.append(c6)
assert c6.visible is False, f"Expected visible False, got {c6.visible}"
print(f"  c6.visible = {c6.visible}")

# Test 5: Test z_index
# NOTE: UICollection.append() assigns z_index by insertion order, so z_index must be
# set AFTER appending (setting it before append is silently overwritten).
print("\nTest 5: Testing z_index...")
c7 = mcrfpy.Circle(radius=40, center=(300, 200), fill_color=mcrfpy.Color(0, 255, 255))
ui.append(c7)
c7.z_index = 100

c8 = mcrfpy.Circle(radius=30, center=(320, 200), fill_color=mcrfpy.Color(255, 0, 255))
ui.append(c8)
c8.z_index = 50
assert c7.z_index == 100, f"Expected z_index 100, got {c7.z_index}"
assert c8.z_index == 50, f"Expected z_index 50, got {c8.z_index}"
print(f"  c7.z_index = {c7.z_index}, c8.z_index = {c8.z_index}")

# Test 6: Test name property
print("\nTest 6: Testing name property...")
c9 = mcrfpy.Circle(radius=20, center=(450, 200), fill_color=mcrfpy.Color(128, 128, 128), name="test_circle")
ui.append(c9)
assert c9.name == "test_circle", f"Expected name 'test_circle', got '{c9.name}'"
print(f"  c9.name = '{c9.name}'")

# Test 7: Test bounds
# get_bounds() was replaced by the .bounds / .global_bounds properties.
print("\nTest 7: Testing bounds...")
pos, size = c1.bounds  # c1: radius 60, center (100, 100)
assert (pos.x, pos.y) == (40, 40), f"Expected bounds pos (40, 40), got ({pos.x}, {pos.y})"
assert (size.x, size.y) == (120, 120), f"Expected bounds size (120, 120), got ({size.x}, {size.y})"
print(f"  c1.bounds = (({pos.x}, {pos.y}), ({size.x}, {size.y}))")

# Test 8: Test move method
print("\nTest 8: Testing move method...")
old_center = (c1.center.x, c1.center.y)
c1.move(10, 10)
new_center = (c1.center.x, c1.center.y)
assert new_center == (old_center[0] + 10, old_center[1] + 10), \
    f"Expected move to offset center by (10, 10): {old_center} -> {new_center}"
print(f"  c1 moved from {old_center} to {new_center}")

# Render a frame and take screenshot
mcrfpy.step(0.01)
automation.screenshot("test_uicircle_result.png")

print("Screenshot saved to test_uicircle_result.png")
print("PASS - UICircle test completed")
sys.exit(0)
