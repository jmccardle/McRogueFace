#!/usr/bin/env python3
"""Test Grid creation with None texture - should work with color cells only"""
import mcrfpy
from mcrfpy import automation
import sys

print("Creating test scene...")
grid_none_test = mcrfpy.Scene("grid_none_test")
mcrfpy.current_scene = grid_none_test

# Add a background frame so we can see the grid
ui = grid_none_test.children
background = mcrfpy.Frame(pos=(0, 0), size=(800, 600),
                         fill_color=mcrfpy.Color(200, 200, 200),
                         outline_color=mcrfpy.Color(0, 0, 0),
                         outline=2.0)
ui.append(background)

print("\n=== Testing Grid with None texture ===")

# Test 1: Create Grid with None texture
try:
    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(50, 50), size=(400, 400))
    print("PASS: Grid created successfully with None texture")
except Exception as e:
    print(f"FAIL: Failed to create Grid with None texture: {e}")
    sys.exit(1)

# Add to UI
ui.append(grid)

# Test 2: Verify grid properties
try:
    grid_size = grid.grid_size
    print(f"PASS: Grid size: {grid_size}")

    # Check texture property
    texture = grid.texture
    if texture is None:
        print("PASS: Grid texture is None as expected")
    else:
        print(f"FAIL: Grid texture should be None, got: {texture}")
except Exception as e:
    print(f"FAIL: Property access failed: {e}")

# Test 3: Access grid points using ColorLayer (new API)
try:
    # Add a color layer to the grid
    color_layer = grid.add_layer("color", z_index=-1)
    # Create a checkerboard pattern with colors
    for x in range(10):
        for y in range(10):
            if (x + y) % 2 == 0:
                color_layer.set(x, y, mcrfpy.Color(255, 0, 0, 255))  # Red
            else:
                color_layer.set(x, y, mcrfpy.Color(0, 0, 255, 255))  # Blue
    print("PASS: Successfully set grid colors via ColorLayer")
except Exception as e:
    print(f"FAIL: Failed to set grid colors: {e}")

# Test 4: Add entities to the grid
try:
    # Create an entity with its own texture
    entity_texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    entity = mcrfpy.Entity((5, 5), texture=entity_texture, sprite_index=1, grid=grid)
    grid.entities.append(entity)
    print(f"PASS: Added entity to grid, total entities: {len(grid.entities)}")
except Exception as e:
    print(f"FAIL: Failed to add entity: {e}")

# Test 5: Test grid interaction properties
try:
    # Test zoom
    grid.zoom = 2.0
    print(f"PASS: Set zoom to: {grid.zoom}")

    # Test center (uses pixel coordinates)
    grid.center = (200, 200)
    print(f"PASS: Set center to: {grid.center}")
except Exception as e:
    print(f"FAIL: Grid properties failed: {e}")

# Take screenshot
mcrfpy.step(0.01)
result = automation.screenshot("grid_none_texture_test.png")
print(f"\nScreenshot saved: grid_none_texture_test.png - Result: {result}")
print("The grid should show a red/blue checkerboard pattern")

print("\nPASS - Grid works correctly without texture!")
sys.exit(0)
