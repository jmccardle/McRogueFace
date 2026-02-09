#!/usr/bin/env python3
"""Test if Color assignment is the trigger"""

import mcrfpy

print("Testing Color operations with range()...")
print("=" * 50)

# Test 1: Basic Color assignment
print("Test 1: Color assignment in grid")
try:
    test1 = mcrfpy.Scene("test1")
    grid = mcrfpy.Grid(grid_w=25, grid_h=15)
    
    # Assign color to a cell
    grid.at(0, 0).color = mcrfpy.Color(200, 200, 220)
    print("  ✓ Single color assignment works")
    
    # Test range
    for i in range(25):
        pass
    print("  ✓ range(25) works after single color assignment")
    
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")

# Test 2: Multiple color assignments
print("\nTest 2: Multiple color assignments")
try:
    test2 = mcrfpy.Scene("test2")
    grid = mcrfpy.Grid(grid_w=25, grid_h=15)
    
    # Multiple properties including color
    for y in range(15):
        for x in range(25):
            grid.at(x, y).walkable = True
            grid.at(x, y).transparent = True
            grid.at(x, y).color = mcrfpy.Color(200, 200, 220)
    
    print("  ✓ Completed all property assignments")
    
    # This is where it would fail
    for i in range(25):
        pass
    print("  ✓ range(25) still works!")
    
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Exact reproduction of failing pattern
print("\nTest 3: Exact pattern from dijkstra_demo_final.py")
try:
    # Recreate the exact function
    def create_demo():
        dijkstra_demo = mcrfpy.Scene("dijkstra_demo")
        
        # Create grid
        grid = mcrfpy.Grid(grid_w=25, grid_h=15)
        grid.fill_color = mcrfpy.Color(0, 0, 0)
        
        # Initialize all as floor
        for y in range(15):
            for x in range(25):
                grid.at(x, y).walkable = True
                grid.at(x, y).transparent = True
                grid.at(x, y).color = mcrfpy.Color(200, 200, 220)
        
        # Create an interesting dungeon layout
        walls = []
        
        # Room walls
        # Top-left room
        for x in range(1, 8): walls.append((x, 1))
        
        return grid, walls
    
    grid, walls = create_demo()
    print(f"  ✓ Function completed successfully, walls: {walls}")
    
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\nConclusion: The bug is inconsistent and may be related to:")
print("- Memory layout at the time of execution")
print("- Specific bytecode patterns in the Python code")
print("- C++ reference counting issues with Color objects")
print("- Stack/heap corruption in the grid.at() implementation")