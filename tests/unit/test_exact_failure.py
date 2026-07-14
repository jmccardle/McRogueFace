#!/usr/bin/env python3
"""Reproduce the exact failure from dijkstra_demo_final.py

Original intent: a bulk per-cell mutation loop (walkable/transparent/color over
every cell of a Grid) appeared to set a Python exception that was NOT raised at
its source, but instead surfaced later on an unrelated line (the `walls.append`
loop). This test drives that exact pattern and asserts that:
  1. the pattern completes without raising, and
  2. no *stale/pending* exception leaks out onto a later, unrelated statement.

API note: GridPoint no longer has `.color` -- per-cell color now lives on a
ColorLayer (grid.add_layer(mcrfpy.ColorLayer(...)); layer.set((x, y), color)).
"""

import mcrfpy
import sys

print("Reproducing exact failure pattern...")
print("=" * 50)

# Colors
WALL_COLOR = mcrfpy.Color(60, 30, 30)
FLOOR_COLOR = mcrfpy.Color(200, 200, 220)

GRID_W, GRID_H = 25, 15

failures = []

def test_exact_pattern():
    """Exact code from dijkstra_demo_final.py (ported to the current API)"""
    dijkstra_demo = mcrfpy.Scene("dijkstra_demo")

    # Create grid
    grid = mcrfpy.Grid(grid_size=(GRID_W, GRID_H))
    grid.fill_color = mcrfpy.Color(0, 0, 0)

    # Per-cell color now lives on a ColorLayer, not on GridPoint
    color_layer = mcrfpy.ColorLayer(name="floor")
    grid.add_layer(color_layer)

    # Initialize all as floor
    for y in range(GRID_H):
        for x in range(GRID_W):
            grid.at(x, y).walkable = True
            grid.at(x, y).transparent = True
            color_layer.set((x, y), FLOOR_COLOR)

    # Create an interesting dungeon layout
    walls = []

    # Room walls
    # Top-left room
    for x in range(1, 8): walls.append((x, 1))

    return grid, color_layer, walls

print("Test 1: Running exact pattern...")
try:
    grid, color_layer, walls = test_exact_pattern()
    print(f"  OK Success! Created {len(walls)} walls")
    if len(walls) != 7:
        failures.append(f"expected 7 walls, got {len(walls)}")
except Exception as e:
    failures.append(f"exact pattern raised {type(e).__name__}: {e}")
    print(f"  FAIL Failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print()
print("Test 2: Breaking it down step by step...")

def step(label, fn):
    """Run a step; a raise here is a real failure, not something to swallow."""
    try:
        result = fn()
        print(f"  OK {label}")
        return result
    except Exception as e:
        failures.append(f"{label} raised {type(e).__name__}: {e}")
        print(f"  FAIL {label}: {type(e).__name__}: {e}")
        return None

# Step 1: Scene and grid
def _step1():
    mcrfpy.Scene("test2")
    return mcrfpy.Grid(grid_size=(GRID_W, GRID_H))
grid = step("Step 1: Scene and grid created", _step1)

# Step 2: Set fill_color
def _step2():
    grid.fill_color = mcrfpy.Color(0, 0, 0)
    assert grid.fill_color == mcrfpy.Color(0, 0, 0)
step("Step 2: fill_color set", _step2)

# Step 3: Nested loops with grid.at + ColorLayer.set (the suspect loop)
layer = mcrfpy.ColorLayer(name="floor2")
grid.add_layer(layer)
def _step3():
    for y in range(GRID_H):
        for x in range(GRID_W):
            grid.at(x, y).walkable = True
            grid.at(x, y).transparent = True
            layer.set((x, y), FLOOR_COLOR)
step("Step 3: Nested loops completed", _step3)

# The mutations must have actually landed (not silently dropped)
if not (grid.at(0, 0).walkable and grid.at(GRID_W - 1, GRID_H - 1).walkable):
    failures.append("Step 3: walkable was not persisted by the nested loop")
if not grid.at(GRID_W - 1, GRID_H - 1).transparent:
    failures.append("Step 3: transparent was not persisted by the nested loop")
if layer.at((GRID_W - 1, GRID_H - 1)) != FLOOR_COLOR:
    failures.append("Step 3: ColorLayer color was not persisted by the nested loop")

# Step 4: Create walls list
def _step4():
    return []
walls = step("Step 4: walls list created", _step4)

# Step 5: The line that used to blow up with an exception raised by *step 3*.
# This is the heart of the regression: after the nested loops, plain Python must
# still work. A stale pending error would explode right here.
def _step5():
    for x in range(1, 8): walls.append((x, 1))
    return walls
step("Step 5: For loop worked", _step5)

if walls != [(x, 1) for x in range(1, 8)]:
    failures.append(f"Step 5: walls list wrong: {walls}")

# Explicitly confirm no exception is left pending after the nested loops.
if sys.exc_info()[0] is not None:
    failures.append(f"stale pending exception after loops: {sys.exc_info()}")

print()
if failures:
    print("FAIL: no exception may be deferred out of the nested cell-mutation loops")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("The nested cell-mutation loops raise nothing, persist their writes, and")
print("leave no pending exception to surface on a later line.")
print("PASS")
sys.exit(0)
