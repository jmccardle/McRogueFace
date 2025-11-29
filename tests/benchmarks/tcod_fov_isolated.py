#!/usr/bin/env python3
"""
Isolated FOV benchmark - test if the slowdown is TCOD or Python wrapper
"""
import mcrfpy
import sys
import time

def run_test(runtime):
    print("=" * 60)
    print("FOV Isolation Test - Is TCOD slow, or is it the Python wrapper?")
    print("=" * 60)

    # Create a 1000x1000 grid
    mcrfpy.createScene("test")
    ui = mcrfpy.sceneUI("test")
    texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)

    print("\nCreating 1000x1000 grid...")
    t0 = time.perf_counter()
    grid = mcrfpy.Grid(pos=(0,0), size=(800,600), grid_size=(1000, 1000), texture=texture)
    ui.append(grid)
    print(f"  Grid creation: {(time.perf_counter() - t0)*1000:.1f}ms")

    # Set walkability
    print("Setting walkability (this takes a while)...")
    t0 = time.perf_counter()
    for y in range(0, 1000, 10):  # Sample every 10th row for speed
        for x in range(1000):
            cell = grid.at(x, y)
            cell.walkable = True
            cell.transparent = True
    print(f"  Partial walkability: {(time.perf_counter() - t0)*1000:.1f}ms")

    # Test 1: compute_fov (now returns None - fast path after #146 fix)
    print("\n--- Test 1: grid.compute_fov() [returns None after #146 fix] ---")
    times = []
    for i in range(5):
        t0 = time.perf_counter()
        result = grid.compute_fov(500, 500, radius=15)
        elapsed = (time.perf_counter() - t0) * 1000
        times.append(elapsed)
        # Count visible cells using is_in_fov (the correct pattern)
        visible = sum(1 for dy in range(-15, 16) for dx in range(-15, 16)
                      if 0 <= 500+dx < 1000 and 0 <= 500+dy < 1000
                      and grid.is_in_fov(500+dx, 500+dy))
        print(f"  Run {i+1}: {elapsed:.3f}ms, result={result}, ~{visible} visible cells")
    print(f"  Average: {sum(times)/len(times):.3f}ms")

    # Test 2: Just check is_in_fov for cells in radius (what rendering would do)
    print("\n--- Test 2: Simulated render check (only radius cells) ---")
    times = []
    for i in range(5):
        # First compute FOV (we need to do this)
        grid.compute_fov(500, 500, radius=15)

        # Now simulate what rendering would do - check only nearby cells
        t0 = time.perf_counter()
        visible_count = 0
        for dy in range(-15, 16):
            for dx in range(-15, 16):
                x, y = 500 + dx, 500 + dy
                if 0 <= x < 1000 and 0 <= y < 1000:
                    if grid.is_in_fov(x, y):
                        visible_count += 1
        elapsed = (time.perf_counter() - t0) * 1000
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.2f}ms checking ~961 cells, {visible_count} visible")
    print(f"  Average: {sum(times)/len(times):.2f}ms")

    # Test 3: Time just the iteration overhead (no FOV, just grid access)
    print("\n--- Test 3: Grid iteration baseline (no FOV) ---")
    times = []
    for i in range(5):
        t0 = time.perf_counter()
        count = 0
        for dy in range(-15, 16):
            for dx in range(-15, 16):
                x, y = 500 + dx, 500 + dy
                if 0 <= x < 1000 and 0 <= y < 1000:
                    cell = grid.at(x, y)
                    if cell.walkable:
                        count += 1
        elapsed = (time.perf_counter() - t0) * 1000
        times.append(elapsed)
    print(f"  Average: {sum(times)/len(times):.2f}ms for ~961 grid.at() calls")

    print("\n" + "=" * 60)
    print("CONCLUSION:")
    print("After #146 fix, compute_fov() returns None instead of building")
    print("a list. Test 1 and Test 2 should now have similar performance.")
    print("The TCOD FOV algorithm is O(radius²) and fast.")
    print("=" * 60)

    sys.exit(0)

mcrfpy.createScene("init")
mcrfpy.setScene("init")
mcrfpy.setTimer("test", run_test, 100)
