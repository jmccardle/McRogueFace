#!/usr/bin/env python3
"""Test single-line for loops which seem to be the issue"""

import mcrfpy

print("Testing single-line for loops...")
print("=" * 50)

# Test 1: Simple single-line for
print("Test 1: Simple single-line for")
try:
    result = []
    for x in range(3): result.append(x)
    print(f"  ✓ Success: {result}")
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 2: Single-line with tuple append (the failing case)
print("Test 2: Single-line with tuple append")
try:
    walls = []
    for x in range(1, 8): walls.append((x, 1))
    print(f"  ✓ Success: {walls}")
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 3: Same but multi-line
print("Test 3: Multi-line version of same code")
try:
    walls = []
    for x in range(1, 8):
        walls.append((x, 1))
    print(f"  ✓ Success: {walls}")
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")

print()

# Test 4: After creating mcrfpy objects
print("Test 4: After creating mcrfpy scene/grid")
try:
    test = mcrfpy.Scene("test")
    grid = mcrfpy.Grid(grid_w=10, grid_h=10)
    
    walls = []
    for x in range(1, 8): walls.append((x, 1))
    print(f"  ✓ Success with mcrfpy objects: {walls}")
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 5: Check line number in error
print("Test 5: Checking exact error location")
def test_exact_pattern():
    dijkstra_demo = mcrfpy.Scene("dijkstra_demo")
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
    print("  About to execute problem line...")
    for x in range(1, 8): walls.append((x, 1))  # Line 40 in original
    print("  ✓ Got past the problem line!")
    
    return grid, walls

try:
    grid, walls = test_exact_pattern()
    print(f"  Result: Created grid and {len(walls)} walls")
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print()
print("Tests complete.")