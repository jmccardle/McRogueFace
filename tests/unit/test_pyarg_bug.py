#!/usr/bin/env python3
"""Test to confirm the PyArg bug in Grid constructor"""

import mcrfpy

print("Testing PyArg bug hypothesis...")
print("=" * 50)

# The bug theory: When Grid is created with keyword args grid_w=25, grid_h=15
# and the code takes the tuple parsing path, PyArg_ParseTupleAndKeywords
# at line 520 fails but doesn't check return value, leaving exception on stack

# Test 1: Create Grid with different argument patterns
print("Test 1: Grid with positional args")
try:
    grid1 = mcrfpy.Grid(25, 15)
    # Force Python to check for pending exceptions
    _ = list(range(1))
    print("  ✓ Grid(25, 15) works")
except Exception as e:
    print(f"  ✗ Grid(25, 15) failed: {type(e).__name__}: {e}")

print()
print("Test 2: Grid with keyword args (the failing case)")
try:
    grid2 = mcrfpy.Grid(grid_w=25, grid_h=15)
    # This should fail if exception is pending
    _ = list(range(1))
    print("  ✓ Grid(grid_w=25, grid_h=15) works")
except Exception as e:
    print(f"  ✗ Grid(grid_w=25, grid_h=15) failed: {type(e).__name__}: {e}")

print()
print("Test 3: Check if it's specific to the values 25, 15")
for x, y in [(24, 15), (25, 14), (25, 15), (26, 15), (25, 16)]:
    try:
        grid = mcrfpy.Grid(grid_w=x, grid_h=y)
        _ = list(range(1))
        print(f"  ✓ Grid(grid_w={x}, grid_h={y}) works")
    except Exception as e:
        print(f"  ✗ Grid(grid_w={x}, grid_h={y}) failed: {type(e).__name__}")

print()
print("Test 4: Mix positional and keyword args")
try:
    # This might trigger different code path
    grid3 = mcrfpy.Grid(25, grid_h=15)
    _ = list(range(1))
    print("  ✓ Grid(25, grid_h=15) works")
except Exception as e:
    print(f"  ✗ Grid(25, grid_h=15) failed: {type(e).__name__}: {e}")

print()
print("Test 5: Test with additional arguments")
try:
    # This might help identify which PyArg call fails
    grid4 = mcrfpy.Grid(grid_w=25, grid_h=15, pos=(0, 0))
    _ = list(range(1))
    print("  ✓ Grid with pos argument works")
except Exception as e:
    print(f"  ✗ Grid with pos failed: {type(e).__name__}: {e}")

try:
    grid5 = mcrfpy.Grid(grid_w=25, grid_h=15, texture=None)
    _ = list(range(1))
    print("  ✓ Grid with texture=None works")
except Exception as e:
    print(f"  ✗ Grid with texture=None failed: {type(e).__name__}: {e}")

print()
print("Hypothesis: The bug is in UIGrid::init line 520-523")
print("PyArg_ParseTupleAndKeywords is called but return value not checked")
print("when parsing remaining arguments in tuple-based initialization path")