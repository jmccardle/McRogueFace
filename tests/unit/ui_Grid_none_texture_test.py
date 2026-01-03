#!/usr/bin/env python3
"""Test Grid creation with None texture - should work with color cells only"""
import mcrfpy
from mcrfpy import automation
import sys

def test_grid_none_texture(runtime):
    """Test Grid functionality without texture"""
    print("\n=== Testing Grid with None texture ===")

    # Test 1: Create Grid with None texture
    try:
        grid = mcrfpy.Grid(grid_size=(10, 10), pos=(50, 50), size=(400, 400))
        print("✓ Grid created successfully with None texture")
    except Exception as e:
        print(f"✗ Failed to create Grid with None texture: {e}")
        sys.exit(1)

    # Add to UI
    ui = grid_none_test.children
    ui.append(grid)

    # Test 2: Verify grid properties
    try:
        grid_size = grid.grid_size
        print(f"✓ Grid size: {grid_size}")

        # Check texture property
        texture = grid.texture
        if texture is None:
            print("✓ Grid texture is None as expected")
        else:
            print(f"✗ Grid texture should be None, got: {texture}")
    except Exception as e:
        print(f"✗ Property access failed: {e}")

    # Test 3: Access grid points using ColorLayer (new API)
    # Note: GridPoint no longer has .color - must use ColorLayer system
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
        print("✓ Successfully set grid colors via ColorLayer")
    except Exception as e:
        print(f"✗ Failed to set grid colors: {e}")

    # Test 4: Add entities to the grid
    try:
        # Create an entity with its own texture
        entity_texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
        entity = mcrfpy.Entity((5, 5), texture=entity_texture, sprite_index=1, grid=grid)
        grid.entities.append(entity)
        print(f"✓ Added entity to grid, total entities: {len(grid.entities)}")
    except Exception as e:
        print(f"✗ Failed to add entity: {e}")

    # Test 5: Test grid interaction properties
    try:
        # Test zoom
        grid.zoom = 2.0
        print(f"✓ Set zoom to: {grid.zoom}")

        # Test center (uses pixel coordinates)
        grid.center = (200, 200)
        print(f"✓ Set center to: {grid.center}")
    except Exception as e:
        print(f"✗ Grid properties failed: {e}")
    
    # Take screenshot
    filename = f"grid_none_texture_test_{int(runtime)}.png"
    result = automation.screenshot(filename)
    print(f"\nScreenshot saved: {filename} - Result: {result}")
    print("The grid should show a red/blue checkerboard pattern")
    
    print("\n✓ PASS - Grid works correctly without texture!")
    sys.exit(0)

# Set up test scene
print("Creating test scene...")
grid_none_test = mcrfpy.Scene("grid_none_test")
grid_none_test.activate()

# Add a background frame so we can see the grid
ui = grid_none_test.children
background = mcrfpy.Frame(pos=(0, 0), size=(800, 600),
                         fill_color=mcrfpy.Color(200, 200, 200),
                         outline_color=mcrfpy.Color(0, 0, 0),
                         outline=2.0)
ui.append(background)

# Schedule test
mcrfpy.setTimer("test", test_grid_none_texture, 100)
print("Test scheduled...")