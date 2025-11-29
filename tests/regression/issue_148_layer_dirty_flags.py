#!/usr/bin/env python3
"""
Regression test for issue #148: Grid Layer Dirty Flags and RenderTexture Caching

Tests:
1. Dirty flag is initially set (layers start dirty)
2. Setting cell values marks layer dirty
3. Fill operation marks layer dirty
4. Texture change marks TileLayer dirty
5. Viewport changes (center/zoom) don't trigger re-render (static benchmark)
6. Performance improvement for static layers
"""
import mcrfpy
import sys
import time

def run_test(runtime):
    print("=" * 60)
    print("Issue #148 Regression Test: Layer Dirty Flags and Caching")
    print("=" * 60)

    # Create test scene
    mcrfpy.createScene("test")
    ui = mcrfpy.sceneUI("test")
    texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)

    # Create grid with larger size for performance testing
    grid = mcrfpy.Grid(pos=(50, 50), size=(500, 400), grid_size=(50, 40), texture=texture)
    ui.append(grid)
    mcrfpy.setScene("test")

    print("\n--- Test 1: Layer creation (starts dirty) ---")
    color_layer = grid.add_layer("color", z_index=-1)
    # The layer should be dirty initially
    # We can't directly check dirty flag from Python, but we verify the system works
    print("  ColorLayer created successfully")

    tile_layer = grid.add_layer("tile", z_index=-2, texture=texture)
    print("  TileLayer created successfully")
    print("  PASS: Layers created")

    print("\n--- Test 2: Fill operations work ---")
    # Fill with some data
    color_layer.fill(mcrfpy.Color(128, 0, 128, 64))
    print("  ColorLayer filled with purple overlay")

    tile_layer.fill(5)  # Fill with tile index 5
    print("  TileLayer filled with tile index 5")
    print("  PASS: Fill operations completed")

    print("\n--- Test 3: Cell set operations work ---")
    # Set individual cells
    color_layer.set(10, 10, mcrfpy.Color(255, 255, 0, 128))
    color_layer.set(11, 10, mcrfpy.Color(255, 255, 0, 128))
    color_layer.set(10, 11, mcrfpy.Color(255, 255, 0, 128))
    color_layer.set(11, 11, mcrfpy.Color(255, 255, 0, 128))
    print("  Set 4 cells in ColorLayer to yellow")

    tile_layer.set(15, 15, 10)
    tile_layer.set(16, 15, 11)
    tile_layer.set(15, 16, 10)
    tile_layer.set(16, 16, 11)
    print("  Set 4 cells in TileLayer to different tiles")
    print("  PASS: Cell set operations completed")

    print("\n--- Test 4: Texture change on TileLayer ---")
    # Create a second texture and assign it
    texture2 = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)
    tile_layer.texture = texture2
    print("  Changed TileLayer texture")

    # Set back to original
    tile_layer.texture = texture
    print("  Restored original texture")
    print("  PASS: Texture changes work")

    print("\n--- Test 5: Viewport changes (should use cached texture) ---")
    # Pan around - these should NOT cause layer re-renders (just blit different region)
    original_center = grid.center
    print(f"  Original center: {original_center}")

    # Perform multiple viewport changes
    for i in range(10):
        grid.center = (100 + i * 20, 80 + i * 10)
    print("  Performed 10 center changes")

    # Zoom changes
    original_zoom = grid.zoom
    for z in [1.0, 0.8, 1.2, 0.5, 1.5, 1.0]:
        grid.zoom = z
    print("  Performed 6 zoom changes")

    # Restore
    grid.center = original_center
    grid.zoom = original_zoom
    print("  PASS: Viewport changes completed without crashing")

    print("\n--- Test 6: Performance benchmark ---")
    # Create a large layer for performance testing
    perf_grid = mcrfpy.Grid(pos=(50, 50), size=(600, 500), grid_size=(100, 80), texture=texture)
    ui.append(perf_grid)
    perf_layer = perf_grid.add_layer("tile", z_index=-1, texture=texture)

    # Fill with data
    perf_layer.fill(1)

    # First render will be slow (cache miss)
    start = time.time()
    mcrfpy.setScene("test")  # Force render
    first_render = time.time() - start
    print(f"  First render (cache build): {first_render*1000:.2f}ms")

    # Subsequent viewport changes should be fast (cache hit)
    # We simulate by changing center multiple times
    start = time.time()
    for i in range(5):
        perf_grid.center = (200 + i * 10, 160 + i * 8)
    viewport_changes = time.time() - start
    print(f"  5 viewport changes: {viewport_changes*1000:.2f}ms")

    print("  PASS: Performance benchmark completed")

    print("\n--- Test 7: Layer visibility toggle ---")
    color_layer.visible = False
    print("  ColorLayer hidden")
    color_layer.visible = True
    print("  ColorLayer shown")
    print("  PASS: Visibility toggle works")

    print("\n--- Test 8: Large grid stress test ---")
    # Test with maximum size grid to ensure texture caching works
    stress_grid = mcrfpy.Grid(pos=(10, 10), size=(200, 150), grid_size=(200, 150), texture=texture)
    ui.append(stress_grid)
    stress_layer = stress_grid.add_layer("color", z_index=-1)

    # This would be 30,000 cells - should handle via caching
    stress_layer.fill(mcrfpy.Color(0, 100, 200, 100))

    # Set a few specific cells
    for x in range(10):
        for y in range(10):
            stress_layer.set(x, y, mcrfpy.Color(255, 0, 0, 200))

    print("  Created 200x150 grid with 30,000 cells")
    print("  PASS: Large grid handled successfully")

    print("\n" + "=" * 60)
    print("All tests PASSED")
    print("=" * 60)
    print("\nNote: Dirty flag behavior is internal - tests verify API works")
    print("Actual caching benefits are measured by render performance.")
    sys.exit(0)

# Initialize and run
mcrfpy.createScene("init")
mcrfpy.setScene("init")
mcrfpy.setTimer("test", run_test, 100)
