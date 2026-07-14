#!/usr/bin/env python3
"""Simple test for Color setter fix

Original intent: assigning a cell color from a plain (r, g, b) tuple must work
just as well as assigning a mcrfpy.Color object.

API update: per-cell color no longer lives on GridPoint (grid.at(x, y).color is
gone). The successor API is a ColorLayer attached to the grid:
    cl = mcrfpy.ColorLayer(name="bg"); grid.add_layer(cl)
    cl.set((x, y), color)
So the same tuple-vs-Color coercion is exercised through ColorLayer.set.
"""

import mcrfpy
import sys

print("Testing Color fix...")

failures = 0

# Test 1: Create grid + color layer
try:
    test = mcrfpy.Scene("test")
    grid = mcrfpy.Grid(grid_size=(5, 5))
    color_layer = mcrfpy.ColorLayer(name="bg")
    grid.add_layer(color_layer)
    print("+ Grid created")
except Exception as e:
    print(f"x Grid creation failed: {e}")
    sys.exit(1)

# Test 2: Set color with tuple
try:
    color_layer.set((0, 0), (100, 100, 100))
    c = color_layer.at((0, 0))
    assert (c.r, c.g, c.b) == (100, 100, 100), f"expected (100,100,100), got {(c.r, c.g, c.b)}"
    print("+ Tuple color assignment works")
except Exception as e:
    print(f"x Tuple assignment failed: {e}")
    failures += 1

# Test 3: Set color with Color object
try:
    color_layer.set((0, 0), mcrfpy.Color(200, 200, 200))
    c = color_layer.at((0, 0))
    assert (c.r, c.g, c.b) == (200, 200, 200), f"expected (200,200,200), got {(c.r, c.g, c.b)}"
    print("+ Color object assignment works!")
except Exception as e:
    print(f"x Color assignment failed: {e}")
    failures += 1

# Test 4: RGBA tuple (4-component) also coerces
try:
    color_layer.set((1, 1), (10, 20, 30, 40))
    c = color_layer.at((1, 1))
    assert (c.r, c.g, c.b, c.a) == (10, 20, 30, 40), f"expected (10,20,30,40), got {(c.r, c.g, c.b, c.a)}"
    print("+ RGBA tuple assignment works")
except Exception as e:
    print(f"x RGBA tuple assignment failed: {e}")
    failures += 1

# Test 5: bad input must raise, not silently succeed
try:
    color_layer.set((2, 2), "not a color")
    print("x Bad color value was accepted")
    failures += 1
except (TypeError, ValueError):
    print("+ Invalid color rejected")

if failures:
    print(f"FAIL ({failures} check(s) failed)")
    sys.exit(1)

print("Done.")
print("PASS")
sys.exit(0)
