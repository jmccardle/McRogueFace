#!/usr/bin/env python3
"""
Regression test for issue #147: Dynamic Layer System for Grid

Tests:
1. ColorLayer creation and manipulation
2. TileLayer creation and manipulation
3. Layer z_index ordering relative to entities
4. Layer management (add_layer, remove_layer, layers property)
"""
import mcrfpy
import sys

def run_test(runtime):
    print("=" * 60)
    print("Issue #147 Regression Test: Dynamic Layer System for Grid")
    print("=" * 60)

    # Create test scene
    mcrfpy.createScene("test")
    ui = mcrfpy.sceneUI("test")
    texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)

    # Create grid
    grid = mcrfpy.Grid(pos=(50, 50), size=(400, 300), grid_size=(20, 15), texture=texture)
    ui.append(grid)

    print("\n--- Test 1: Initial state (no layers) ---")
    if len(grid.layers) == 0:
        print("  PASS: Grid starts with no layers")
    else:
        print(f"  FAIL: Expected 0 layers, got {len(grid.layers)}")
        sys.exit(1)

    print("\n--- Test 2: Add ColorLayer ---")
    color_layer = grid.add_layer("color", z_index=-1)
    print(f"  Created: {color_layer}")
    if color_layer is not None:
        print("  PASS: ColorLayer created")
    else:
        print("  FAIL: ColorLayer creation returned None")
        sys.exit(1)

    # Test ColorLayer properties
    if color_layer.z_index == -1:
        print("  PASS: ColorLayer z_index is -1")
    else:
        print(f"  FAIL: Expected z_index -1, got {color_layer.z_index}")
        sys.exit(1)

    if color_layer.visible:
        print("  PASS: ColorLayer is visible by default")
    else:
        print("  FAIL: ColorLayer should be visible by default")
        sys.exit(1)

    grid_size = color_layer.grid_size
    if grid_size == (20, 15):
        print(f"  PASS: ColorLayer grid_size is {grid_size}")
    else:
        print(f"  FAIL: Expected (20, 15), got {grid_size}")
        sys.exit(1)

    print("\n--- Test 3: ColorLayer cell access ---")
    # Set a color
    color_layer.set(5, 5, mcrfpy.Color(255, 0, 0, 128))
    color = color_layer.at(5, 5)
    if color.r == 255 and color.g == 0 and color.b == 0 and color.a == 128:
        print(f"  PASS: Color at (5,5) is {color.r}, {color.g}, {color.b}, {color.a}")
    else:
        print(f"  FAIL: Color mismatch")
        sys.exit(1)

    # Fill entire layer
    color_layer.fill(mcrfpy.Color(0, 0, 255, 64))
    color = color_layer.at(0, 0)
    if color.b == 255 and color.a == 64:
        print("  PASS: ColorLayer fill works")
    else:
        print("  FAIL: ColorLayer fill did not work")
        sys.exit(1)

    print("\n--- Test 4: Add TileLayer ---")
    tile_layer = grid.add_layer("tile", z_index=-2, texture=texture)
    print(f"  Created: {tile_layer}")
    if tile_layer is not None:
        print("  PASS: TileLayer created")
    else:
        print("  FAIL: TileLayer creation returned None")
        sys.exit(1)

    if tile_layer.z_index == -2:
        print("  PASS: TileLayer z_index is -2")
    else:
        print(f"  FAIL: Expected z_index -2, got {tile_layer.z_index}")
        sys.exit(1)

    print("\n--- Test 5: TileLayer cell access ---")
    # Set a tile
    tile_layer.set(3, 3, 42)
    tile = tile_layer.at(3, 3)
    if tile == 42:
        print(f"  PASS: Tile at (3,3) is {tile}")
    else:
        print(f"  FAIL: Expected 42, got {tile}")
        sys.exit(1)

    # Fill entire layer
    tile_layer.fill(10)
    tile = tile_layer.at(0, 0)
    if tile == 10:
        print("  PASS: TileLayer fill works")
    else:
        print("  FAIL: TileLayer fill did not work")
        sys.exit(1)

    print("\n--- Test 6: Layer ordering ---")
    layers = grid.layers
    if len(layers) == 2:
        print(f"  PASS: Grid has 2 layers")
    else:
        print(f"  FAIL: Expected 2 layers, got {len(layers)}")
        sys.exit(1)

    # Layers should be sorted by z_index
    if layers[0].z_index <= layers[1].z_index:
        print(f"  PASS: Layers sorted by z_index ({layers[0].z_index}, {layers[1].z_index})")
    else:
        print(f"  FAIL: Layers not sorted")
        sys.exit(1)

    print("\n--- Test 7: Get layer by z_index ---")
    layer = grid.layer(-1)
    if layer is not None and layer.z_index == -1:
        print("  PASS: grid.layer(-1) returns ColorLayer")
    else:
        print("  FAIL: Could not get layer by z_index")
        sys.exit(1)

    layer = grid.layer(-2)
    if layer is not None and layer.z_index == -2:
        print("  PASS: grid.layer(-2) returns TileLayer")
    else:
        print("  FAIL: Could not get layer by z_index")
        sys.exit(1)

    layer = grid.layer(999)
    if layer is None:
        print("  PASS: grid.layer(999) returns None for non-existent layer")
    else:
        print("  FAIL: Should return None for non-existent layer")
        sys.exit(1)

    print("\n--- Test 8: Layer above entities (z_index >= 0) ---")
    fog_layer = grid.add_layer("color", z_index=1)
    if fog_layer.z_index == 1:
        print("  PASS: Created layer with z_index=1 (above entities)")
    else:
        print("  FAIL: Layer z_index incorrect")
        sys.exit(1)

    # Set fog
    fog_layer.fill(mcrfpy.Color(0, 0, 0, 128))
    print("  PASS: Fog layer filled")

    print("\n--- Test 9: Remove layer ---")
    initial_count = len(grid.layers)
    grid.remove_layer(fog_layer)
    final_count = len(grid.layers)
    if final_count == initial_count - 1:
        print(f"  PASS: Layer removed ({initial_count} -> {final_count})")
    else:
        print(f"  FAIL: Layer count didn't decrease ({initial_count} -> {final_count})")
        sys.exit(1)

    print("\n--- Test 10: Layer visibility toggle ---")
    color_layer.visible = False
    if not color_layer.visible:
        print("  PASS: Layer visibility can be toggled")
    else:
        print("  FAIL: Layer visibility toggle failed")
        sys.exit(1)
    color_layer.visible = True

    print("\n" + "=" * 60)
    print("All tests PASSED")
    print("=" * 60)
    sys.exit(0)

# Initialize and run
mcrfpy.createScene("init")
mcrfpy.setScene("init")
mcrfpy.setTimer("test", run_test, 100)
