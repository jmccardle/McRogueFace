#!/usr/bin/env python3
"""Test for features/scenes.md examples.

Tests both modern and procedural APIs from the docs.
"""
import mcrfpy
from mcrfpy import automation
import sys

# Test 1: Modern Scene API (lines 28-42)
print("Test 1: Modern Scene API")
scene = mcrfpy.Scene("test_modern")
scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(800, 600)))

def my_handler(key, action):
    if action == "start":
        print(f"  Key handler received: {key}")

scene.on_key = my_handler
scene.activate()
mcrfpy.step(0.1)
print("  PASS - modern Scene API works")

# Test 2: Check Scene properties
print("Test 2: Scene properties")
print(f"  scene.name = {scene.name}")
print(f"  scene.active = {scene.active}")
print(f"  len(scene.children) = {len(scene.children)}")

# Test 3: Check if default_texture exists
print("Test 3: default_texture")
try:
    dt = mcrfpy.default_texture
    print(f"  mcrfpy.default_texture = {dt}")
except AttributeError:
    print("  default_texture NOT FOUND - docs bug!")

# Test 4: Check if currentScene exists
print("Test 4: currentScene()")
try:
    current = mcrfpy.currentScene()
    print(f"  mcrfpy.currentScene() = {current}")
except AttributeError:
    print("  currentScene() NOT FOUND - docs bug!")

# Test 5: Check Grid.at() signature
print("Test 5: Grid.at() signature")
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
grid = mcrfpy.Grid(grid_size=(10, 10), texture=texture, pos=(0, 0), size=(200, 200))

# Try both signatures
try:
    point_tuple = grid.at((5, 5))
    print("  grid.at((x, y)) - tuple WORKS")
except Exception as e:
    print(f"  grid.at((x, y)) FAILS: {e}")

try:
    point_sep = grid.at(5, 5)
    print("  grid.at(x, y) - separate args WORKS")
except Exception as e:
    print(f"  grid.at(x, y) FAILS: {e}")

# Test 6: Scene transitions (setScene)
print("Test 6: setScene()")
scene2 = mcrfpy.Scene("test_transitions")
scene2.activate()
mcrfpy.step(0.1)

# Check if setScene exists
try:
    mcrfpy.setScene("test_modern")
    print("  mcrfpy.setScene() WORKS")
except AttributeError:
    print("  mcrfpy.setScene() NOT FOUND - use scene.activate() instead")
except Exception as e:
    print(f"  mcrfpy.setScene() error: {e}")

# Take screenshot
mcrfpy.step(0.1)
automation.screenshot("/opt/goblincorps/repos/McRogueFace/tests/docs/screenshots/features_scenes.png")

print("\nAll scene tests complete")
sys.exit(0)
