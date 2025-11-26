#!/usr/bin/env python3
"""Minimal test to isolate crash."""

import mcrfpy
import sys

try:
    print("1. Module loaded")
    
    print("2. Creating scene...")
    mcrfpy.createScene("test")
    print("   Scene created")
    
    print("3. Creating grid with explicit parameters...")
    # Try with all explicit parameters
    grid = mcrfpy.Grid(grid_x=5, grid_y=5, texture=None, pos=(0, 0), size=(80, 80))
    print("   Grid created successfully")
    
    print("4. Testing grid.at()...")
    point = grid.at(0, 0)
    print(f"   Got point: {point}")
    
    print("5. Setting walkable...")
    point.walkable = True
    print("   Walkable set")
    
    print("PASS")
    
except Exception as e:
    print(f"FAIL at step: {e}")
    import traceback
    traceback.print_exc()

sys.exit(0)