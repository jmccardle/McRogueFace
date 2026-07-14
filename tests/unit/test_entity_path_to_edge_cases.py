#!/usr/bin/env python3
"""Test edge cases for Entity.path_to() method"""

import mcrfpy
import sys

failures = []

def check(condition, message):
    """Record a pass/fail instead of just printing it."""
    if condition:
        print("  [ok] %s" % message)
    else:
        print("  [FAIL] %s" % message)
        failures.append(message)

print("Testing Entity.path_to() edge cases...")
print("=" * 50)

# Test 1: Entity without grid
print("Test 1: Entity not in grid")
entity = mcrfpy.Entity(grid_pos=(5, 5))
try:
    path = entity.path_to(8, 8)
    check(False, "path_to() on a grid-less entity should raise ValueError, got %r" % (path,))
except ValueError as e:
    check(True, "correctly raised ValueError with no grid: %s" % e)
except Exception as e:
    check(False, "wrong exception type: %s: %s" % (type(e).__name__, e))

# Test 2: Entity in grid with walls blocking path
print("\nTest 2: Completely blocked path")
blocked_test = mcrfpy.Scene("blocked_test")
grid = mcrfpy.Grid(grid_size=(5, 5))

# Make all tiles walkable first
for y in range(5):
    for x in range(5):
        grid.at(x, y).walkable = True

# Create a wall that completely blocks the path
for x in range(5):
    grid.at(x, 2).walkable = False

entity = mcrfpy.Entity(grid_pos=(1, 1), grid=grid)

path = entity.path_to(1, 4)
check(path == [], "no path across the full-width wall, got %r" % (path,))

# Test 3: Alternative parameter parsing (keyword x/y)
print("\nTest 3: Alternative parameter names")
path = entity.path_to(x=3, y=1)
check(path == [(2, 1), (3, 1)],
      "path_to(x=, y=) walked the open row: %r" % (path,))

# The same target via positional args must agree with the keyword form.
check(entity.path_to(3, 1) == path,
      "positional path_to(3, 1) matches the keyword form")

print("\n" + "=" * 50)
if failures:
    print("Edge case testing FAILED (%d):" % len(failures))
    for f in failures:
        print("  - %s" % f)
    sys.exit(1)

print("Edge case testing complete!")
print("PASS")
sys.exit(0)
