#!/usr/bin/env python3
"""Regression: range() (and general interpreter state) must survive grid operations.

Historically, iterating a grid with grid.at(x, y) at certain sizes corrupted the
Python interpreter state and a subsequent range() raised SystemError. This test
sweeps grid/range sizes and asserts that never happens again.
"""

import mcrfpy
import sys

print("Finding range() failure threshold...")
print("=" * 50)

failures = []

def test_range_size(n):
    """Test if range(n) works after grid operations on an n x n grid"""
    try:
        mcrfpy.Scene(f"test_{n}")
        grid = mcrfpy.Grid(grid_size=(n, n))

        # Do grid operations
        for y in range(min(n, 10)):  # Limit outer loop
            for x in range(n):
                if x < n and y < n:
                    grid.at(x, y).walkable = True

        # Now test if range(n) still works
        test_list = []
        for i in range(n):
            test_list.append(i)

        return True, len(test_list)
    except SystemError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Other error: {type(e).__name__}: {e}"

# Sweep a range of sizes; every one of them must work.
print("Testing different range sizes...")

for n in [2, 4, 8, 16, 32]:
    success, result = test_range_size(n)
    if success:
        print(f"  range({n:2d}): OK - created list of {result} items")
        if result != n:
            failures.append(f"range({n}) produced {result} items, expected {n}")
    else:
        print(f"  range({n:2d}): FAIL - {result}")
        failures.append(f"range({n}) after {n}x{n} grid ops: {result}")

print()

# The original bug was reported as "10 works, 25 fails" -- walk the whole span
# and require that every size in it works.
print("Sweeping the historically suspect span (10..25)...")

for n in range(10, 26):
    success, result = test_range_size(n)
    if success:
        print(f"  range({n}): OK")
        if result != n:
            failures.append(f"range({n}) produced {result} items, expected {n}")
    else:
        print(f"  range({n}): FAIL - {result}")
        failures.append(f"range({n}) after {n}x{n} grid ops: {result}")

print()
print("Testing if it's about grid size vs range size...")

try:
    # Small grid, large range
    mcrfpy.Scene("test_small_grid")
    grid = mcrfpy.Grid(grid_size=(5, 5))

    # Do minimal grid operations
    grid.at(0, 0).walkable = True

    # Test large range
    count = 0
    for i in range(25):
        count += 1
    assert count == 25, f"range(25) yielded {count} items"
    print("  OK: range(25) works with small grid (5x5)")

except Exception as e:
    print(f"  FAIL: range(25) fails with small grid: {type(e).__name__}: {e}")
    failures.append(f"small grid / large range: {type(e).__name__}: {e}")

try:
    # Large grid, see what happens
    mcrfpy.Scene("test_large_grid")
    grid = mcrfpy.Grid(grid_size=(20, 20))

    # Do operations on large grid
    touched = 0
    for y in range(20):
        for x in range(20):
            grid.at(x, y).walkable = True
            touched += 1
    assert touched == 400, f"touched {touched} cells, expected 400"
    print("  OK: Completed 20x20 grid operations")

    # Now test range
    count = 0
    for i in range(20):
        count += 1
    assert count == 20, f"range(20) yielded {count} items"
    print("  OK: range(20) works after 20x20 grid operations")

    # And the values written are readable back
    assert grid.at(19, 19).walkable is True, "walkable did not persist at (19,19)"

except Exception as e:
    print(f"  FAIL: Error with 20x20 grid: {type(e).__name__}: {e}")
    failures.append(f"20x20 grid: {type(e).__name__}: {e}")

print()
if failures:
    print("Analysis complete: FAILURES")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("Analysis complete.")
print("PASS")
sys.exit(0)
