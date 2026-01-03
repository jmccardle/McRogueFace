#!/usr/bin/env python3
"""Find the exact threshold where range() starts failing"""

import mcrfpy

print("Finding range() failure threshold...")
print("=" * 50)

def test_range_size(n):
    """Test if range(n) works after grid operations"""
    try:
        mcrfpy.createScene(f"test_{n}")
        grid = mcrfpy.Grid(grid_x=n, grid_y=n)
        
        # Do grid operations
        for y in range(min(n, 10)):  # Limit outer loop
            for x in range(n):
                if x < n and y < n:
                    grid.at(x, y).walkable = True
        
        # Now test if range(n) still works
        test_list = []
        for i in range(n):
            test_list.append(i)
        
        return True, len(test_list)
    except SystemError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Other error: {type(e).__name__}: {e}"

# Binary search for the threshold
print("Testing different range sizes...")

# Test powers of 2 first
for n in [2, 4, 8, 16, 32]:
    success, result = test_range_size(n)
    if success:
        print(f"  range({n:2d}): ✓ Success - created list of {result} items")
    else:
        print(f"  range({n:2d}): ✗ Failed - {result}")

print()

# Narrow down between working and failing values
print("Narrowing down exact threshold...")

# From our tests: 10 works, 25 fails
low = 10
high = 25

while low < high - 1:
    mid = (low + high) // 2
    success, result = test_range_size(mid)
    
    if success:
        print(f"  range({mid}): ✓ Works")
        low = mid
    else:
        print(f"  range({mid}): ✗ Fails")
        high = mid

print()
print(f"Threshold found: range({low}) works, range({high}) fails")

# Test if it's specifically about range or about the grid size
print()
print("Testing if it's about grid size vs range size...")

try:
    # Small grid, large range
    test_small_grid = mcrfpy.Scene("test_small_grid")
    grid = mcrfpy.Grid(grid_x=5, grid_y=5)
    
    # Do minimal grid operations
    grid.at(0, 0).walkable = True
    
    # Test large range
    for i in range(25):
        pass
    print("  ✓ range(25) works with small grid (5x5)")
    
except Exception as e:
    print(f"  ✗ range(25) fails with small grid: {e}")

try:
    # Large grid, see what happens
    test_large_grid = mcrfpy.Scene("test_large_grid")
    grid = mcrfpy.Grid(grid_x=20, grid_y=20)
    
    # Do operations on large grid
    for y in range(20):
        for x in range(20):
            grid.at(x, y).walkable = True
    
    print("  ✓ Completed 20x20 grid operations")
    
    # Now test range
    for i in range(20):
        pass
    print("  ✓ range(20) works after 20x20 grid operations")
    
except Exception as e:
    print(f"  ✗ Error with 20x20 grid: {e}")

print()
print("Analysis complete.")