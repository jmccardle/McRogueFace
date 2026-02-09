#!/usr/bin/env python3
"""Test Grid constructor to isolate the PyArg bug"""

import mcrfpy
import sys

print("Testing Grid constructor PyArg bug...")
print("=" * 50)

# Test 1: Check if exception is set after Grid creation
print("Test 1: Check exception state after Grid creation")
try:
    # Clear any existing exception
    sys.exc_clear() if hasattr(sys, 'exc_clear') else None
    
    # Create grid with problematic dimensions
    print("  Creating Grid(grid_w=25, grid_h=15)...")
    grid = mcrfpy.Grid(grid_w=25, grid_h=15)
    print("  Grid created successfully")
    
    # Check if there's a pending exception
    exc = sys.exc_info()
    if exc[0] is not None:
        print(f"  ⚠️  Pending exception detected: {exc}")
    
    # Try to trigger the error
    print("  Calling range(1)...")
    for i in range(1):
        pass
    print("  ✓ range(1) worked")
    
except Exception as e:
    print(f"  ✗ Exception: {type(e).__name__}: {e}")

print()

# Test 2: Try different Grid constructor patterns
print("Test 2: Different Grid constructor calls")

# Pattern 1: Positional arguments
try:
    print("  Trying Grid(25, 15)...")
    grid1 = mcrfpy.Grid(25, 15)
    for i in range(1): pass
    print("  ✓ Positional args worked")
except Exception as e:
    print(f"  ✗ Positional args failed: {e}")

# Pattern 2: Different size
try:
    print("  Trying Grid(grid_w=24, grid_h=15)...")
    grid2 = mcrfpy.Grid(grid_w=24, grid_h=15)
    for i in range(1): pass
    print("  ✓ Size 24x15 worked")
except Exception as e:
    print(f"  ✗ Size 24x15 failed: {e}")

# Pattern 3: Check if it's specifically 25
try:
    print("  Trying Grid(grid_w=26, grid_h=15)...")
    grid3 = mcrfpy.Grid(grid_w=26, grid_h=15)
    for i in range(1): pass
    print("  ✓ Size 26x15 worked")
except Exception as e:
    print(f"  ✗ Size 26x15 failed: {e}")

print()

# Test 3: Isolate the exact problem
print("Test 3: Isolating the problem")

def test_grid_creation(x, y):
    """Test creating a grid and immediately using range()"""
    try:
        grid = mcrfpy.Grid(grid_w=x, grid_h=y)
        # Immediately test if exception is pending
        list(range(1))
        return True, "Success"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

# Test various sizes
test_sizes = [(10, 10), (20, 20), (24, 15), (25, 14), (25, 15), (25, 16), (30, 30)]
for x, y in test_sizes:
    success, msg = test_grid_creation(x, y)
    if success:
        print(f"  Grid({x}, {y}): ✓")
    else:
        print(f"  Grid({x}, {y}): ✗ {msg}")

print()

# Test 4: See if we can clear the exception
print("Test 4: Exception clearing")
try:
    # Create the problematic grid
    grid = mcrfpy.Grid(grid_w=25, grid_h=15)
    print("  Created Grid(25, 15)")
    
    # Try to clear any pending exception
    try:
        # This should fail if there's a pending exception
        list(range(1))
        print("  No pending exception!")
    except:
        print("  ⚠️  Pending exception detected")
        # Clear it
        sys.exc_clear() if hasattr(sys, 'exc_clear') else None
        
        # Try again
        try:
            list(range(1))
            print("  ✓ Exception cleared, range() works now")
        except:
            print("  ✗ Exception persists")
    
except Exception as e:
    print(f"  ✗ Failed: {e}")

print()
print("Conclusion: The Grid constructor is setting a Python exception")
print("but not properly returning NULL to propagate it. This leaves")
print("the exception on the stack, causing the next Python operation")
print("to fail with the cryptic 'new style getargs format' error.")