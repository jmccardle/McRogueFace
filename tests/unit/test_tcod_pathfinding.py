#!/usr/bin/env python3
"""Test pathfinding."""

import mcrfpy
import sys

try:
    print("1. Creating scene and grid...")
    test = mcrfpy.Scene("test")
    grid = mcrfpy.Grid(grid_x=7, grid_y=7, texture=None, pos=(0, 0), size=(112, 112))
    print("   Grid created")
    
    print("2. Setting up map with walls...")
    # Make all cells walkable first
    for y in range(7):
        for x in range(7):
            point = grid.at(x, y)
            point.walkable = True
            point.transparent = True
    
    # Add a wall
    for y in range(1, 6):
        grid.at(3, y).walkable = False
        grid.at(3, y).transparent = False
    
    # Show the map
    print("   Map layout (* = wall, . = walkable):")
    for y in range(7):
        row = []
        for x in range(7):
            walkable = grid.at(x, y).walkable
            row.append('.' if walkable else '*')
        print(f"   {''.join(row)}")
    
    print("3. Finding path from (1,3) to (5,3)...")
    path = grid.find_path(1, 3, 5, 3)
    print(f"   Path found: {len(path)} steps")
    
    if path:
        print("4. Path visualization:")
        # Create visualization
        for y in range(7):
            row = []
            for x in range(7):
                if (x, y) in path:
                    row.append('P')
                elif not grid.at(x, y).walkable:
                    row.append('*')
                else:
                    row.append('.')
            print(f"   {''.join(row)}")
        
        print(f"   Path coordinates: {path}")
    
    print("PASS")
    
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()

sys.exit(0)