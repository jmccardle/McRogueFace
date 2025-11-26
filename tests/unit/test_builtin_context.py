#!/usr/bin/env python3
"""Test Python builtins in function context like the failing demos"""

import mcrfpy

print("Testing builtins in different contexts...")
print("=" * 50)

# Test 1: At module level (working in our test)
print("Test 1: Module level")
try:
    for x in range(3):
        print(f"  x={x}")
    print("  ✓ Module level works")
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")

print()

# Test 2: In a function
print("Test 2: Inside function")
def test_function():
    try:
        for x in range(3):
            print(f"  x={x}")
        print("  ✓ Function level works")
    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

test_function()

print()

# Test 3: In a function that creates mcrfpy objects
print("Test 3: Function creating mcrfpy objects")
def create_scene():
    try:
        mcrfpy.createScene("test")
        print("  ✓ Created scene")
        
        # Now try range
        for x in range(3):
            print(f"  x={x}")
        print("  ✓ Range after createScene works")
        
        # Create grid
        grid = mcrfpy.Grid(grid_x=10, grid_y=10)
        print("  ✓ Created grid")
        
        # Try range again
        for x in range(3):
            print(f"  x={x}")
        print("  ✓ Range after Grid creation works")
        
        return grid
    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

grid = create_scene()

print()

# Test 4: The exact failing pattern
print("Test 4: Exact failing pattern")
def failing_pattern():
    try:
        mcrfpy.createScene("failing_test")
        grid = mcrfpy.Grid(grid_x=14, grid_y=10)
        
        # This is where it fails in the demos
        walls = []
        print("  About to enter range loop...")
        for x in range(1, 8):
            walls.append((x, 1))
        print(f"  ✓ Created walls: {walls}")
        
    except Exception as e:
        print(f"  ✗ Error at line: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

failing_pattern()

print()

# Test 5: Check if it's related to the append operation
print("Test 5: Testing append in loop")
def test_append():
    try:
        walls = []
        # Test 1: Simple append
        walls.append((1, 1))
        print("  ✓ Single append works")
        
        # Test 2: Manual loop
        i = 0
        while i < 3:
            walls.append((i, 1))
            i += 1
        print(f"  ✓ While loop append works: {walls}")
        
        # Test 3: Range with different operations
        walls2 = []
        for x in range(3):
            tup = (x, 2)
            walls2.append(tup)
        print(f"  ✓ Range with temp variable works: {walls2}")
        
        # Test 4: Direct tuple creation in append
        walls3 = []
        for x in range(3):
            walls3.append((x, 3))
        print(f"  ✓ Direct tuple append works: {walls3}")
        
    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

test_append()

print()
print("All tests complete.")