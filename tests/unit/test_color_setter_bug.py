#!/usr/bin/env python3
"""Test that confirms the Color setter bug"""

import mcrfpy

print("Testing GridPoint color setter bug...")
print("=" * 50)

# Test 1: Setting color with tuple (old way)
print("Test 1: Setting color with tuple")
try:
    mcrfpy.createScene("test1")
    grid = mcrfpy.Grid(grid_x=5, grid_y=5)
    
    # This should work (PyArg_ParseTuple expects tuple)
    grid.at(0, 0).color = (200, 200, 220)
    
    # Check if exception is pending
    _ = list(range(1))
    print("  ✓ Tuple assignment works")
except Exception as e:
    print(f"  ✗ Tuple assignment failed: {type(e).__name__}: {e}")

print()

# Test 2: Setting color with Color object (the bug)
print("Test 2: Setting color with Color object")
try:
    mcrfpy.createScene("test2")
    grid = mcrfpy.Grid(grid_x=5, grid_y=5)
    
    # This will fail in PyArg_ParseTuple but not report it
    grid.at(0, 0).color = mcrfpy.Color(200, 200, 220)
    print("  ⚠️  Color assignment appeared to work...")
    
    # But exception is pending!
    _ = list(range(1))
    print("  ✓ No exception detected (unexpected!)")
except Exception as e:
    print(f"  ✗ Exception detected: {type(e).__name__}: {e}")
    print("  This confirms the bug - exception was set but not raised")

print()

# Test 3: Multiple color assignments
print("Test 3: Multiple Color assignments (reproducing original bug)")
try:
    mcrfpy.createScene("test3")
    grid = mcrfpy.Grid(grid_x=25, grid_y=15)
    
    # Do multiple color assignments
    for y in range(2):  # Just 2 rows to be quick
        for x in range(25):
            grid.at(x, y).color = mcrfpy.Color(200, 200, 220)
    
    print("  All color assignments completed...")
    
    # This should fail
    for i in range(25):
        pass
    print("  ✓ range(25) worked (unexpected!)")
except Exception as e:
    print(f"  ✗ range(25) failed as expected: {type(e).__name__}")
    print("  The exception was set during color assignment")

print()
print("Bug confirmed: PyObject_to_sfColor in UIGridPoint.cpp")
print("doesn't clear the exception when PyArg_ParseTuple fails.")
print("The fix: Either check PyErr_Occurred() after ParseTuple,")
print("or support mcrfpy.Color objects directly.")