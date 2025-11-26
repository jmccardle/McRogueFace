#!/usr/bin/env python3
"""Test Python builtins to diagnose the SystemError"""

import sys

print("Python version:", sys.version)
print("=" * 50)

# Test 1: Simple range
print("Test 1: Simple range(5)")
try:
    r = range(5)
    print("  Created range:", r)
    print("  Type:", type(r))
    for i in r:
        print("  ", i)
    print("  ✓ Success")
except Exception as e:
    print("  ✗ Error:", type(e).__name__, "-", e)

print()

# Test 2: Range with start/stop
print("Test 2: range(1, 5)")
try:
    r = range(1, 5)
    print("  Created range:", r)
    for i in r:
        print("  ", i)
    print("  ✓ Success")
except Exception as e:
    print("  ✗ Error:", type(e).__name__, "-", e)

print()

# Test 3: Range in list comprehension
print("Test 3: List comprehension with range")
try:
    lst = [x for x in range(3)]
    print("  Result:", lst)
    print("  ✓ Success")
except Exception as e:
    print("  ✗ Error:", type(e).__name__, "-", e)

print()

# Test 4: Range in for loop (the failing case)
print("Test 4: for x in range(3):")
try:
    for x in range(3):
        print("  ", x)
    print("  ✓ Success")
except Exception as e:
    print("  ✗ Error:", type(e).__name__, "-", e)

print()

# Test 5: len() on list
print("Test 5: len() on list")
try:
    lst = [1, 2, 3]
    print("  List:", lst)
    print("  Length:", len(lst))
    print("  ✓ Success")
except Exception as e:
    print("  ✗ Error:", type(e).__name__, "-", e)

print()

# Test 6: len() on tuple
print("Test 6: len() on tuple")
try:
    tup = (1, 2, 3)
    print("  Tuple:", tup)
    print("  Length:", len(tup))
    print("  ✓ Success")
except Exception as e:
    print("  ✗ Error:", type(e).__name__, "-", e)

print()

# Test 7: Nested function calls (reproducing the error context)
print("Test 7: Nested context like in the failing code")
try:
    walls = []
    for x in range(1, 8):
        walls.append((x, 1))
    print("  Walls:", walls)
    print("  ✓ Success")
except Exception as e:
    print("  ✗ Error:", type(e).__name__, "-", e)
    import traceback
    traceback.print_exc()

print()

# Test 8: Check if builtins are intact
print("Test 8: Builtin integrity check")
print("  range is:", range)
print("  len is:", len)
print("  type(range):", type(range))
print("  type(len):", type(len))

print()
print("Tests complete.")