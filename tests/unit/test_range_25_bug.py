#!/usr/bin/env python3
"""Regression test for the historical range(25) bug.

A nested grid.at()/walkable loop over a 25x15 grid used to corrupt the
interpreter (refcount / memory corruption in the C++ binding), so that a
plain `range(25)` afterwards raised. This test drives the exact scenario and
asserts that (a) the interpreter survives intact and (b) the grid.at() writes
actually stick.
"""

import mcrfpy
import sys

failures = []


def check(condition, label):
    if condition:
        print("  PASS: %s" % label)
    else:
        print("  FAIL: %s" % label)
        failures.append(label)


def exercise_grid(w, h):
    """Nested grid.at() loop -- the operation that used to corrupt memory."""
    grid = mcrfpy.Grid(grid_size=(w, h))
    count = 0
    for y in range(h):
        for x in range(w):
            grid.at(x, y).walkable = True
            count += 1
    return grid, count


print("Testing the range(25) bug scenario...")
print("=" * 50)

# Test 1: range(25) works fine normally (baseline sanity)
print("Test 1: range(25) before any mcrfpy operations")
check(list(range(25)) == list(range(25)), "range(25) works initially")

# Test 2: range(25) after creating a 25x15 grid
print("\nTest 2: range(25) after creating 25x15 grid")
mcrfpy.Scene("test2")
grid = mcrfpy.Grid(grid_size=(25, 15))
check(len(list(range(25))) == 25, "range(25) still works after grid creation")
check(tuple(grid.grid_size) == (25, 15), "grid is 25x15")

# Test 3: The killer combination -- 15x25 nested grid.at() loop, then range(25)
print("\nTest 3: range(25) after 15x25 grid.at() operations")
mcrfpy.Scene("test3")
grid, count = exercise_grid(25, 15)
check(count == 375, "completed %d grid.at() calls (expected 375)" % count)
check(list(range(25)) == list(range(25)), "range(25) works after grid.at() loop")
check(sum(range(25)) == 300, "range(25) still produces correct values")
check(all(grid.at(x, y).walkable for y in range(15) for x in range(25)),
      "every cell readback is walkable (writes stuck)")

# Test 4: range(24) after the same operations
print("\nTest 4: range(24) after same operations")
mcrfpy.Scene("test4")
grid = mcrfpy.Grid(grid_size=(25, 15))
for y in range(15):
    for x in range(24):  # One less
        grid.at(x, y).walkable = True
check(len(list(range(24))) == 24, "range(24) works")
check(len(list(range(25))) == 25, "range(25) also works when grid ops used range(24)")
check(not grid.at(24, 0).walkable, "untouched column 24 stayed unwalkable")

# Test 5: Different grid dimensions -- not specific to 15/25
print("\nTest 5: Different grid dimensions")
mcrfpy.Scene("test5")
grid, count = exercise_grid(30, 20)
check(count == 600, "completed %d grid.at() calls on 30x20 grid" % count)
check(len(list(range(25))) == 25, "range(25) works with 30x20 grid")
check(len(list(range(30))) == 30, "range(30) works with 30x20 grid")

print("\n" + "=" * 50)
if failures:
    print("FAIL: %d check(s) failed:" % len(failures))
    for f in failures:
        print("  - %s" % f)
    sys.exit(1)

print("PASS: the range(25) bug is fixed; grid.at() loops do not corrupt the interpreter")
sys.exit(0)
