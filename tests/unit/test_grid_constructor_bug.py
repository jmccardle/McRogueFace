#!/usr/bin/env python3
"""Test Grid constructor to isolate the PyArg bug

Original intent: the Grid constructor used to set a Python exception without
returning NULL, leaving a stale exception on the interpreter stack. The next
Python operation (e.g. range(1)) then blew up with a cryptic
"new style getargs format" error. This test constructs Grids of many sizes and
verifies that (a) construction succeeds, (b) the resulting Grid is actually the
size that was asked for, and (c) no stale exception is left behind.

API notes (current, post-#313/#361): the Grid constructor takes
grid_size=(w, h); grid_w=/grid_h= are the legacy spelling and still work.
"""

import mcrfpy
import sys

failures = []

def check(cond, msg):
    if cond:
        print(f"  PASS: {msg}")
    else:
        print(f"  FAIL: {msg}")
        failures.append(msg)

def no_stale_exception(label):
    """Any pending-but-unraised exception trips the next Python operation."""
    try:
        list(range(1))
    except Exception as e:
        check(False, f"{label}: stale exception after Grid creation: {type(e).__name__}: {e}")
        return False
    check(True, f"{label}: no stale exception after Grid creation")
    return True

print("Testing Grid constructor PyArg bug...")
print("=" * 50)

# Test 1: Check exception state after Grid creation
print("Test 1: Check exception state after Grid creation")
try:
    print("  Creating Grid(grid_size=(25, 15))...")
    grid = mcrfpy.Grid(grid_size=(25, 15))
    check(True, "Grid(grid_size=(25, 15)) constructed")
    check((grid.grid_size.x, grid.grid_size.y) == (25, 15),
          f"grid_size is (25, 15), got ({grid.grid_size.x}, {grid.grid_size.y})")
    no_stale_exception("Test 1")
except Exception as e:
    check(False, f"Grid(grid_size=(25, 15)) raised {type(e).__name__}: {e}")

print()

# Test 2: legacy grid_w/grid_h spelling still constructs the same grid
print("Test 2: Legacy grid_w=/grid_h= keywords")
for w, h in [(24, 15), (25, 15), (26, 15)]:
    try:
        g = mcrfpy.Grid(grid_w=w, grid_h=h)
        ok = (g.grid_size.x, g.grid_size.y) == (w, h)
        check(ok, f"Grid(grid_w={w}, grid_h={h}) -> grid_size ({g.grid_size.x}, {g.grid_size.y})")
        no_stale_exception(f"Grid({w}, {h})")
    except Exception as e:
        check(False, f"Grid(grid_w={w}, grid_h={h}) raised {type(e).__name__}: {e}")

print()

# Test 3: Isolate the exact problem -- a sweep of sizes, each followed by a
# plain Python operation that would explode if an exception were left pending.
print("Test 3: Size sweep (construct, then immediately use the interpreter)")

def test_grid_creation(x, y):
    """Test creating a grid and immediately using range()"""
    try:
        g = mcrfpy.Grid(grid_size=(x, y))
        # Immediately test if an exception is pending
        list(range(1))
        if (g.grid_size.x, g.grid_size.y) != (x, y):
            return False, f"wrong grid_size ({g.grid_size.x}, {g.grid_size.y})"
        return True, "Success"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

test_sizes = [(10, 10), (20, 20), (24, 15), (25, 14), (25, 15), (25, 16), (30, 30)]
for x, y in test_sizes:
    success, msg = test_grid_creation(x, y)
    check(success, f"Grid({x}, {y}): {msg}")

print()

# Test 4: bad arguments must raise properly (and not corrupt interpreter state)
print("Test 4: Invalid arguments raise instead of leaving a pending exception")
try:
    bad = mcrfpy.Grid(grid_size="not a size")
    check(False, "Grid(grid_size='not a size') should have raised")
except (TypeError, ValueError) as e:
    check(True, f"Grid(grid_size='not a size') raised {type(e).__name__} as expected")
except Exception as e:
    check(False, f"Grid(grid_size='not a size') raised unexpected {type(e).__name__}: {e}")
no_stale_exception("Test 4")

print()
print("=" * 50)
if failures:
    print(f"FAIL: {len(failures)} check(s) failed")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("PASS")
sys.exit(0)
