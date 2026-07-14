#!/usr/bin/env python3
"""Test grid iteration patterns to find the exact cause"""

import mcrfpy
import sys

failures = []

def check(condition, label):
    """Record a failed check instead of silently printing a checkmark."""
    if condition:
        print(f"  [ok] {label}")
    else:
        print(f"  [FAIL] {label}")
        failures.append(label)

print("Testing grid iteration patterns...")
print("=" * 50)

# Test 1: Basic grid.at() calls
print("Test 1: Basic grid.at() calls")
try:
    test1 = mcrfpy.Scene("test1")
    grid = mcrfpy.Grid(grid_w=5, grid_h=5)

    # Single call
    grid.at(0, 0).walkable = True
    check(grid.at(0, 0).walkable is True, "Single grid.at() call works")

    # Multiple calls
    grid.at(1, 1).walkable = True
    grid.at(2, 2).walkable = True
    check(grid.at(1, 1).walkable and grid.at(2, 2).walkable,
          "Multiple grid.at() calls work")

    # Now try a print
    print("  [ok] Print after grid.at() works")

except Exception as e:
    print(f"  [FAIL] Error: {type(e).__name__}: {e}")
    failures.append(f"Test 1: {type(e).__name__}: {e}")

print()

# Test 2: Grid.at() in a loop
print("Test 2: Grid.at() in simple loop")
try:
    test2 = mcrfpy.Scene("test2")
    grid = mcrfpy.Grid(grid_w=5, grid_h=5)

    for i in range(3):
        grid.at(i, 0).walkable = True
    check(all(grid.at(i, 0).walkable for i in range(3)),
          "Single loop with grid.at() works")

    # Print after loop
    print("  [ok] Print after loop works")

except Exception as e:
    print(f"  [FAIL] Error: {type(e).__name__}: {e}")
    failures.append(f"Test 2: {type(e).__name__}: {e}")

print()

# Test 3: Nested loops with grid.at()
print("Test 3: Nested loops with grid.at()")
try:
    test3 = mcrfpy.Scene("test3")
    grid = mcrfpy.Grid(grid_w=5, grid_h=5)

    for y in range(3):
        for x in range(3):
            grid.at(x, y).walkable = True

    check(all(grid.at(x, y).walkable for y in range(3) for x in range(3)),
          "Nested loops with grid.at() work")
    print("  [ok] Print after nested loops works")

except Exception as e:
    print(f"  [FAIL] Error: {type(e).__name__}: {e}")
    failures.append(f"Test 3: {type(e).__name__}: {e}")

print()

# Test 4: Exact pattern from failing code
print("Test 4: Exact failing pattern")
try:
    test4 = mcrfpy.Scene("test4")
    grid = mcrfpy.Grid(grid_w=25, grid_h=15)
    grid.fill_color = mcrfpy.Color(0, 0, 0)

    # Per-cell color moved off GridPoint onto ColorLayer (Grid layer rework);
    # GridPoint now exposes only entities/grid_pos/transparent/walkable.
    colors = mcrfpy.ColorLayer(name="cell_color")
    grid.add_layer(colors)

    # This is the exact nested loop from the failing code
    for y in range(15):
        for x in range(25):
            grid.at(x, y).walkable = True
            grid.at(x, y).transparent = True
            colors.set((x, y), mcrfpy.Color(200, 200, 220))

    check(all(grid.at(x, y).walkable and grid.at(x, y).transparent
              for y in range(15) for x in range(25)),
          "Full nested loop completed (375 cells set)")

    # This is where it used to fail
    print("  About to test post-loop operations...")

    # Try different operations
    x = 5
    check(x == 5, f"Variable assignment works: x={x}")

    lst = []
    check(lst == [], f"List creation works: {lst}")

    # The failing line
    for i in range(3): pass
    print("  [ok] Empty for loop works")

    # With append
    for i in range(3): lst.append(i)
    check(lst == [0, 1, 2], f"For loop with append works: {lst}")

except Exception as e:
    print(f"  [FAIL] Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    failures.append(f"Test 4: {type(e).__name__}: {e}")

print()

# Test 5: Is it related to the number of grid.at() calls?
print("Test 5: Testing grid.at() call limits")
try:
    test5 = mcrfpy.Scene("test5")
    grid = mcrfpy.Grid(grid_w=10, grid_h=10)

    count = 0
    for y in range(10):
        for x in range(10):
            grid.at(x, y).walkable = True
            count += 1

            # Test print every 10 calls
            if count % 10 == 0:
                print(f"  Processed {count} cells...")

    check(count == 100, f"Processed all {count} cells")
    check(all(grid.at(x, y).walkable for y in range(10) for x in range(10)),
          "All 100 cells still readable after the loop")

    # Now test operations
    print("  Testing post-processing operations...")
    for i in range(3): pass
    print("  [ok] All operations work after 100 grid.at() calls")

except Exception as e:
    print(f"  [FAIL] Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    failures.append(f"Test 5: {type(e).__name__}: {e}")

print()
print("Tests complete.")

if failures:
    print(f"FAIL: {len(failures)} check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("PASS")
sys.exit(0)
