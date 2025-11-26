#!/usr/bin/env python3
"""Demonstrate the range(25) bug precisely"""

import mcrfpy

print("Demonstrating range(25) bug...")
print("=" * 50)

# Test 1: range(25) works fine normally
print("Test 1: range(25) before any mcrfpy operations")
try:
    for i in range(25):
        pass
    print("  ✓ range(25) works fine initially")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 2: range(25) after creating scene/grid
print("\nTest 2: range(25) after creating 25x15 grid")
try:
    mcrfpy.createScene("test")
    grid = mcrfpy.Grid(grid_x=25, grid_y=15)
    
    for i in range(25):
        pass
    print("  ✓ range(25) still works after grid creation")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 3: The killer combination
print("\nTest 3: range(25) after 15x25 grid.at() operations")
try:
    mcrfpy.createScene("test3")
    grid = mcrfpy.Grid(grid_x=25, grid_y=15)
    
    # Do the nested loop that triggers the bug
    count = 0
    for y in range(15):
        for x in range(25):
            grid.at(x, y).walkable = True
            count += 1
    
    print(f"  ✓ Completed {count} grid.at() calls")
    
    # This should fail
    print("  Testing range(25) now...")
    for i in range(25):
        pass
    print("  ✓ range(25) works (unexpected!)")
    
except Exception as e:
    print(f"  ✗ range(25) failed as expected: {type(e).__name__}")

# Test 4: Does range(24) still work?
print("\nTest 4: range(24) after same operations")
try:
    mcrfpy.createScene("test4")
    grid = mcrfpy.Grid(grid_x=25, grid_y=15)
    
    for y in range(15):
        for x in range(24):  # One less
            grid.at(x, y).walkable = True
    
    for i in range(24):
        pass
    print("  ✓ range(24) works")
    
    # What about range(25)?
    for i in range(25):
        pass
    print("  ✓ range(25) also works when grid ops used range(24)")
    
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 5: Is it about the specific combination of 15 and 25?
print("\nTest 5: Different grid dimensions")
try:
    mcrfpy.createScene("test5")
    grid = mcrfpy.Grid(grid_x=30, grid_y=20)
    
    for y in range(20):
        for x in range(30):
            grid.at(x, y).walkable = True
    
    # Test various ranges
    for i in range(25):
        pass
    print("  ✓ range(25) works with 30x20 grid")
    
    for i in range(30):
        pass
    print("  ✓ range(30) works with 30x20 grid")
    
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\nConclusion: There's a specific bug triggered by:")
print("1. Creating a grid with grid_x=25")
print("2. Using range(25) in a nested loop with grid.at() calls")
print("3. Then trying to use range(25) again")
print("\nThis appears to be a memory corruption or reference counting issue in the C++ code.")