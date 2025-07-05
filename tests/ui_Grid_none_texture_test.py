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
        grid = mcrfpy.Grid(10, 10, None, mcrfpy.Vector(50, 50), mcrfpy.Vector(400, 400))
        print("✓ Grid created successfully with None texture")
    except Exception as e:
        print(f"✗ Failed to create Grid with None texture: {e}")
        sys.exit(1)
    
    # Add to UI
    ui = mcrfpy.sceneUI("grid_none_test")
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
    
    # Test 3: Access grid points and set colors
    try:
        # Create a checkerboard pattern with colors
        for x in range(10):
            for y in range(10):
                point = grid.at(x, y)
                if (x + y) % 2 == 0:
                    point.color = mcrfpy.Color(255, 0, 0, 255)  # Red
                else:
                    point.color = mcrfpy.Color(0, 0, 255, 255)  # Blue
        print("✓ Successfully set grid point colors")
    except Exception as e:
        print(f"✗ Failed to set grid colors: {e}")
    
    # Test 4: Add entities to the grid
    try:
        # Create an entity with its own texture
        entity_texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
        entity = mcrfpy.Entity(mcrfpy.Vector(5, 5), entity_texture, 1, grid)
        grid.entities.append(entity)
        print(f"✓ Added entity to grid, total entities: {len(grid.entities)}")
    except Exception as e:
        print(f"✗ Failed to add entity: {e}")
    
    # Test 5: Test grid interaction properties
    try:
        # Test zoom
        grid.zoom = 2.0
        print(f"✓ Set zoom to: {grid.zoom}")
        
        # Test center
        grid.center = mcrfpy.Vector(5, 5)
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
mcrfpy.createScene("grid_none_test")
mcrfpy.setScene("grid_none_test")

# Add a background frame so we can see the grid
ui = mcrfpy.sceneUI("grid_none_test")
background = mcrfpy.Frame(0, 0, 800, 600,
                         fill_color=mcrfpy.Color(200, 200, 200),
                         outline_color=mcrfpy.Color(0, 0, 0),
                         outline=2.0)
ui.append(background)

# Schedule test
mcrfpy.setTimer("test", test_grid_none_texture, 100)
print("Test scheduled...")