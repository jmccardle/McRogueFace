#!/usr/bin/env python3
"""Reproduce the exact failure from dijkstra_demo_final.py"""

import mcrfpy

print("Reproducing exact failure pattern...")
print("=" * 50)

# Colors
WALL_COLOR = mcrfpy.Color(60, 30, 30)
FLOOR_COLOR = mcrfpy.Color(200, 200, 220)

def test_exact_pattern():
    """Exact code from dijkstra_demo_final.py"""
    mcrfpy.createScene("dijkstra_demo")
    
    # Create grid
    grid = mcrfpy.Grid(grid_x=25, grid_y=15)
    grid.fill_color = mcrfpy.Color(0, 0, 0)
    
    # Initialize all as floor
    for y in range(15):
        for x in range(25):
            grid.at(x, y).walkable = True
            grid.at(x, y).transparent = True
            grid.at(x, y).color = FLOOR_COLOR
    
    # Create an interesting dungeon layout
    walls = []
    
    # Room walls
    # Top-left room
    for x in range(1, 8): walls.append((x, 1))
    
    return grid, walls

print("Test 1: Running exact pattern...")
try:
    grid, walls = test_exact_pattern()
    print(f"  ✓ Success! Created {len(walls)} walls")
except Exception as e:
    print(f"  ✗ Failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print()
print("Test 2: Breaking it down step by step...")

# Step 1: Scene and grid
try:
    mcrfpy.createScene("test2")
    grid = mcrfpy.Grid(grid_x=25, grid_y=15)
    print("  ✓ Step 1: Scene and grid created")
except Exception as e:
    print(f"  ✗ Step 1 failed: {e}")

# Step 2: Set fill_color
try:
    grid.fill_color = mcrfpy.Color(0, 0, 0)
    print("  ✓ Step 2: fill_color set")
except Exception as e:
    print(f"  ✗ Step 2 failed: {e}")

# Step 3: Nested loops with grid.at
try:
    for y in range(15):
        for x in range(25):
            grid.at(x, y).walkable = True
            grid.at(x, y).transparent = True
            grid.at(x, y).color = FLOOR_COLOR
    print("  ✓ Step 3: Nested loops completed")
except Exception as e:
    print(f"  ✗ Step 3 failed: {e}")

# Step 4: Create walls list
try:
    walls = []
    print("  ✓ Step 4: walls list created")
except Exception as e:
    print(f"  ✗ Step 4 failed: {e}")

# Step 5: The failing line
try:
    for x in range(1, 8): walls.append((x, 1))
    print(f"  ✓ Step 5: For loop worked, walls = {walls}")
except Exception as e:
    print(f"  ✗ Step 5 failed: {type(e).__name__}: {e}")
    
    # Check if exception was already pending
    import sys
    exc_info = sys.exc_info()
    print(f"  Exception info: {exc_info}")

print()
print("The error occurs at step 5, suggesting an exception was")
print("set during the nested loops but not immediately raised.")