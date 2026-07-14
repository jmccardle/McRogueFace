#!/usr/bin/env python3
"""Test Python builtins in function context like the failing demos

Regression guard: builtins (range, list.append, f-strings) must keep working at
module level, inside functions, and -- critically -- after mcrfpy objects have
been constructed. A broken embedded-interpreter builtins dict used to make
`range()` blow up in exactly those spots.

Failures are RECORDED, not just printed: the script exits 1 if any check fails.
"""

import mcrfpy
import sys
import traceback

failures = []

def fail(label, msg):
    failures.append(f"{label}: {msg}")
    print(f"  x FAIL {label}: {msg}")

print("Testing builtins in different contexts...")
print("=" * 50)

# Test 1: At module level
print("Test 1: Module level")
try:
    xs = []
    for x in range(3):
        xs.append(x)
    if xs != [0, 1, 2]:
        fail("module level range", f"expected [0, 1, 2], got {xs}")
    else:
        print("  ok Module level works")
except Exception as e:
    traceback.print_exc()
    fail("module level range", f"{type(e).__name__}: {e}")

print()

# Test 2: In a function
print("Test 2: Inside function")
def test_function():
    try:
        xs = [x for x in range(3)]
        xs2 = []
        for x in range(3):
            xs2.append(f"x={x}")
        if xs != [0, 1, 2] or xs2 != ["x=0", "x=1", "x=2"]:
            fail("function level builtins", f"got {xs}, {xs2}")
            return
        print("  ok Function level works")
    except Exception as e:
        traceback.print_exc()
        fail("function level builtins", f"{type(e).__name__}: {e}")

test_function()

print()

# Test 3: In a function that creates mcrfpy objects
print("Test 3: Function creating mcrfpy objects")
def create_scene():
    try:
        test = mcrfpy.Scene("test")
        print("  ok Created scene")

        # Now try range -- must still work after a Scene exists
        xs = [x for x in range(3)]
        if xs != [0, 1, 2]:
            fail("range after Scene()", f"expected [0, 1, 2], got {xs}")
            return None
        print("  ok Range after Scene creation works")

        # Create grid (current API: grid_size tuple)
        grid = mcrfpy.Grid(grid_size=(10, 10))
        print("  ok Created grid")

        # Try range again -- must still work after a Grid exists
        xs = [x for x in range(3)]
        if xs != [0, 1, 2]:
            fail("range after Grid()", f"expected [0, 1, 2], got {xs}")
            return None
        print("  ok Range after Grid creation works")

        return grid
    except Exception as e:
        traceback.print_exc()
        fail("mcrfpy object construction context", f"{type(e).__name__}: {e}")
        return None

grid = create_scene()
if grid is None:
    fail("create_scene", "returned None")

print()

# Test 4: The exact failing pattern
print("Test 4: Exact failing pattern")
def failing_pattern():
    try:
        failing_test = mcrfpy.Scene("failing_test")
        grid = mcrfpy.Grid(grid_size=(14, 10))

        # This is where it used to fail in the demos
        walls = []
        print("  About to enter range loop...")
        for x in range(1, 8):
            walls.append((x, 1))
        expected = [(x, 1) for x in range(1, 8)]
        if walls != expected:
            fail("demo wall pattern", f"expected {expected}, got {walls}")
            return
        print(f"  ok Created walls: {walls}")

    except Exception as e:
        traceback.print_exc()
        fail("demo wall pattern", f"{type(e).__name__}: {e}")

failing_pattern()

print()

# Test 5: Check if it's related to the append operation
print("Test 5: Testing append in loop")
def test_append():
    try:
        walls = []
        # Test 1: Simple append
        walls.append((1, 1))
        if walls != [(1, 1)]:
            fail("single append", f"got {walls}")
            return
        print("  ok Single append works")

        # Test 2: Manual loop
        i = 0
        while i < 3:
            walls.append((i, 1))
            i += 1
        if walls != [(1, 1), (0, 1), (1, 1), (2, 1)]:
            fail("while loop append", f"got {walls}")
            return
        print(f"  ok While loop append works: {walls}")

        # Test 3: Range with different operations
        walls2 = []
        for x in range(3):
            tup = (x, 2)
            walls2.append(tup)
        if walls2 != [(0, 2), (1, 2), (2, 2)]:
            fail("range with temp variable", f"got {walls2}")
            return
        print(f"  ok Range with temp variable works: {walls2}")

        # Test 4: Direct tuple creation in append
        walls3 = []
        for x in range(3):
            walls3.append((x, 3))
        if walls3 != [(0, 3), (1, 3), (2, 3)]:
            fail("direct tuple append", f"got {walls3}")
            return
        print(f"  ok Direct tuple append works: {walls3}")

    except Exception as e:
        traceback.print_exc()
        fail("append in loop", f"{type(e).__name__}: {e}")

test_append()

print()
if failures:
    print(f"FAIL ({len(failures)} check(s) failed)")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("All tests complete.")
print("PASS")
sys.exit(0)
