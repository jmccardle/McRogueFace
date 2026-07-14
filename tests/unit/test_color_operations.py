#!/usr/bin/env python3
"""Test if Color assignment is the trigger

Originally a repro script for a crash/corruption suspected in per-cell Color
assignment (grid.at(x, y).color = Color(...)) followed by range() iteration.

API update: GridPoint no longer carries a .color -- per-cell color now lives on a
ColorLayer (grid.add_layer(mcrfpy.ColorLayer(...)); layer.set((x, y), Color)).
The original intent (bulk color writes must not corrupt the interpreter, and the
colors must actually stick) is preserved against the new API.
"""

import mcrfpy
import sys

failures = []

print("Testing Color operations with range()...")
print("=" * 50)

# Test 1: Basic Color assignment
print("Test 1: Color assignment in grid")
try:
    test1 = mcrfpy.Scene("test1")
    grid = mcrfpy.Grid(grid_size=(25, 15))
    colors = mcrfpy.ColorLayer(name="cell_color")
    grid.add_layer(colors)

    # Assign color to a cell
    colors.set((0, 0), mcrfpy.Color(200, 200, 220))
    c = colors.at((0, 0))
    assert (c.r, c.g, c.b) == (200, 200, 220), f"color readback wrong: {c}"
    print("  ✓ Single color assignment works")

    # Test range
    for i in range(25):
        pass
    print("  ✓ range(25) works after single color assignment")

except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")
    failures.append(f"Test 1: {type(e).__name__}: {e}")

# Test 2: Multiple color assignments
print("\nTest 2: Multiple color assignments")
try:
    test2 = mcrfpy.Scene("test2")
    grid = mcrfpy.Grid(grid_size=(25, 15))
    colors = mcrfpy.ColorLayer(name="cell_color")
    grid.add_layer(colors)

    # Multiple properties including color
    for y in range(15):
        for x in range(25):
            grid.at(x, y).walkable = True
            grid.at(x, y).transparent = True
            colors.set((x, y), mcrfpy.Color(200, 200, 220))

    print("  ✓ Completed all property assignments")

    # Every cell must have kept its value
    for y in range(15):
        for x in range(25):
            c = colors.at((x, y))
            assert (c.r, c.g, c.b) == (200, 200, 220), f"cell ({x},{y}) = {c}"
            assert grid.at(x, y).walkable is True, f"cell ({x},{y}) not walkable"
            assert grid.at(x, y).transparent is True, f"cell ({x},{y}) not transparent"
    print("  ✓ All 375 cells read back correctly")

    # This is where it would fail
    for i in range(25):
        pass
    print("  ✓ range(25) still works!")

except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    failures.append(f"Test 2: {type(e).__name__}: {e}")

# Test 3: Exact reproduction of failing pattern
print("\nTest 3: Exact pattern from dijkstra_demo_final.py")
try:
    # Recreate the exact function
    def create_demo():
        dijkstra_demo = mcrfpy.Scene("dijkstra_demo")

        # Create grid
        grid = mcrfpy.Grid(grid_size=(25, 15))
        grid.fill_color = mcrfpy.Color(0, 0, 0)
        colors = mcrfpy.ColorLayer(name="cell_color")
        grid.add_layer(colors)

        # Initialize all as floor
        for y in range(15):
            for x in range(25):
                grid.at(x, y).walkable = True
                grid.at(x, y).transparent = True
                colors.set((x, y), mcrfpy.Color(200, 200, 220))

        # Create an interesting dungeon layout
        walls = []

        # Room walls
        # Top-left room
        for x in range(1, 8): walls.append((x, 1))

        return grid, walls

    grid, walls = create_demo()
    assert walls == [(x, 1) for x in range(1, 8)], f"walls corrupted: {walls}"
    fc = grid.fill_color
    assert (fc.r, fc.g, fc.b) == (0, 0, 0), f"fill_color corrupted: {fc}"
    print(f"  ✓ Function completed successfully, walls: {walls}")

except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    failures.append(f"Test 3: {type(e).__name__}: {e}")

print()
if failures:
    for f in failures:
        print(f"FAILED: {f}")
    sys.exit(1)

print("PASS")
sys.exit(0)
