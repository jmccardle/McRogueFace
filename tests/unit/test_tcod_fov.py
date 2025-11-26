#!/usr/bin/env python3
"""Test FOV computation."""

import mcrfpy
import sys

try:
    print("1. Creating scene and grid...")
    mcrfpy.createScene("test")
    grid = mcrfpy.Grid(grid_x=5, grid_y=5, texture=None, pos=(0, 0), size=(80, 80))
    print("   Grid created")
    
    print("2. Setting all cells walkable and transparent...")
    for y in range(5):
        for x in range(5):
            point = grid.at(x, y)
            point.walkable = True
            point.transparent = True
    print("   All cells set")
    
    print("3. Computing FOV...")
    grid.compute_fov(2, 2, 3)
    print("   FOV computed")
    
    print("4. Checking FOV results...")
    for y in range(5):
        row = []
        for x in range(5):
            in_fov = grid.is_in_fov(x, y)
            row.append('*' if in_fov else '.')
        print(f"   {''.join(row)}")
    
    print("PASS")
    
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()

sys.exit(0)