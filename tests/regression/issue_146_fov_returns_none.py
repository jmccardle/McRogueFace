#!/usr/bin/env python3
"""
Regression test for issue #146: compute_fov() returns None

The compute_fov() method had O(n²) performance because it built a Python list
of all visible cells by iterating the entire grid. The fix removes this
list-building and returns None instead. Users should use is_in_fov() to query
visibility.

Bug: 15.76ms for compute_fov() on 1000x1000 grid (iterating 1M cells)
Fix: Return None, actual FOV check via is_in_fov() takes 0.21ms
"""
import mcrfpy
import sys
import time

def run_test(timer, runtime):
    print("=" * 60)
    print("Issue #146 Regression Test: compute_fov() returns None")
    print("=" * 60)

    # Create a test grid
    test = mcrfpy.Scene("test")
    ui = test.children
    texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)

    grid = mcrfpy.Grid(pos=(0,0), size=(400,300), grid_size=(50, 50), texture=texture)
    ui.append(grid)

    # Set walkability for center area
    for y in range(50):
        for x in range(50):
            cell = grid.at(x, y)
            cell.walkable = True
            cell.transparent = True

    # Add some walls to test blocking
    for i in range(10, 20):
        grid.at(i, 25).transparent = False
        grid.at(i, 25).walkable = False

    print("\n--- Test 1: compute_fov() returns None ---")
    result = grid.compute_fov(25, 25, radius=10)
    if result is None:
        print("  PASS: compute_fov() returned None")
    else:
        print(f"  FAIL: compute_fov() returned {type(result).__name__} instead of None")
        sys.exit(1)

    print("\n--- Test 2: is_in_fov() works after compute_fov() ---")
    # Center should be visible
    if grid.is_in_fov(25, 25):
        print("  PASS: Center (25,25) is in FOV")
    else:
        print("  FAIL: Center should be in FOV")
        sys.exit(1)

    # Cell within radius should be visible
    if grid.is_in_fov(20, 25):
        print("  PASS: Cell (20,25) within radius is in FOV")
    else:
        print("  FAIL: Cell (20,25) should be in FOV")
        sys.exit(1)

    # Cell behind wall should NOT be visible
    if not grid.is_in_fov(15, 30):
        print("  PASS: Cell (15,30) behind wall is NOT in FOV")
    else:
        print("  FAIL: Cell behind wall should not be in FOV")
        sys.exit(1)

    # Cell outside radius should NOT be visible
    if not grid.is_in_fov(0, 0):
        print("  PASS: Cell (0,0) outside radius is NOT in FOV")
    else:
        print("  FAIL: Cell outside radius should not be in FOV")
        sys.exit(1)

    print("\n--- Test 3: Performance sanity check ---")
    # Create larger grid for timing
    grid_large = mcrfpy.Grid(pos=(0,0), size=(400,300), grid_size=(200, 200), texture=texture)
    for y in range(0, 200, 5):  # Sample for speed
        for x in range(200):
            cell = grid_large.at(x, y)
            cell.walkable = True
            cell.transparent = True

    # Time compute_fov (should be fast now - no list building)
    times = []
    for i in range(5):
        t0 = time.perf_counter()
        grid_large.compute_fov(100, 100, radius=15)
        elapsed = (time.perf_counter() - t0) * 1000
        times.append(elapsed)

    avg_time = sum(times) / len(times)
    print(f"  compute_fov() on 200x200 grid: {avg_time:.3f}ms avg")

    # Should be under 1ms without list building (was ~4ms with list on 200x200)
    if avg_time < 2.0:
        print(f"  PASS: compute_fov() is fast (<2ms)")
    else:
        print(f"  WARNING: compute_fov() took {avg_time:.3f}ms (expected <2ms)")
        # Not a hard failure, just a warning

    print("\n" + "=" * 60)
    print("All tests PASSED")
    print("=" * 60)
    sys.exit(0)

# Initialize and run
init = mcrfpy.Scene("init")
init.activate()
test_timer = mcrfpy.Timer("test", run_test, 100, once=True)
