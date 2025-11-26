#!/usr/bin/env python3
"""Test grid iteration patterns to find the exact cause"""

import mcrfpy

print("Testing grid iteration patterns...")
print("=" * 50)

# Test 1: Basic grid.at() calls
print("Test 1: Basic grid.at() calls")
try:
    mcrfpy.createScene("test1")
    grid = mcrfpy.Grid(grid_x=5, grid_y=5)
    
    # Single call
    grid.at(0, 0).walkable = True
    print("  ✓ Single grid.at() call works")
    
    # Multiple calls
    grid.at(1, 1).walkable = True
    grid.at(2, 2).walkable = True
    print("  ✓ Multiple grid.at() calls work")
    
    # Now try a print
    print("  ✓ Print after grid.at() works")
    
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")

print()

# Test 2: Grid.at() in a loop
print("Test 2: Grid.at() in simple loop")
try:
    mcrfpy.createScene("test2")
    grid = mcrfpy.Grid(grid_x=5, grid_y=5)
    
    for i in range(3):
        grid.at(i, 0).walkable = True
    print("  ✓ Single loop with grid.at() works")
    
    # Print after loop
    print("  ✓ Print after loop works")
    
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")

print()

# Test 3: Nested loops with grid.at()
print("Test 3: Nested loops with grid.at()")
try:
    mcrfpy.createScene("test3")
    grid = mcrfpy.Grid(grid_x=5, grid_y=5)
    
    for y in range(3):
        for x in range(3):
            grid.at(x, y).walkable = True
    
    print("  ✓ Nested loops with grid.at() work")
    print("  ✓ Print after nested loops works")
    
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")

print()

# Test 4: Exact pattern from failing code
print("Test 4: Exact failing pattern")
try:
    mcrfpy.createScene("test4")
    grid = mcrfpy.Grid(grid_x=25, grid_y=15)
    grid.fill_color = mcrfpy.Color(0, 0, 0)
    
    # This is the exact nested loop from the failing code
    for y in range(15):
        for x in range(25):
            grid.at(x, y).walkable = True
            grid.at(x, y).transparent = True
            grid.at(x, y).color = mcrfpy.Color(200, 200, 220)
    
    print("  ✓ Full nested loop completed")
    
    # This is where it fails
    print("  About to test post-loop operations...")
    
    # Try different operations
    x = 5
    print(f"  ✓ Variable assignment works: x={x}")
    
    lst = []
    print(f"  ✓ List creation works: {lst}")
    
    # The failing line
    for i in range(3): pass
    print("  ✓ Empty for loop works")
    
    # With append
    for i in range(3): lst.append(i)
    print(f"  ✓ For loop with append works: {lst}")
    
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 5: Is it related to the number of grid.at() calls?
print("Test 5: Testing grid.at() call limits")
try:
    mcrfpy.createScene("test5")
    grid = mcrfpy.Grid(grid_x=10, grid_y=10)
    
    count = 0
    for y in range(10):
        for x in range(10):
            grid.at(x, y).walkable = True
            count += 1
            
            # Test print every 10 calls
            if count % 10 == 0:
                print(f"  Processed {count} cells...")
    
    print(f"  ✓ Processed all {count} cells")
    
    # Now test operations
    print("  Testing post-processing operations...")
    for i in range(3): pass
    print("  ✓ All operations work after 100 grid.at() calls")
    
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print()
print("Tests complete.")