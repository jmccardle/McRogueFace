#!/usr/bin/env python3
"""Test for issue #177: GridPoint.grid_pos property

Verifies that GridPoint objects have a grid_pos property that returns
the (grid_x, grid_y) coordinates as a tuple.
"""
import mcrfpy
import sys

print("Starting test...")

# Create a simple grid without texture (should work in headless mode)
grid = mcrfpy.Grid(grid_x=10, grid_y=8)
print(f"Created grid: {grid}")

# Test various grid positions
test_cases = [
    (0, 0),
    (5, 3),
    (9, 7),
    (0, 7),
    (9, 0),
]

all_passed = True
for x, y in test_cases:
    point = grid.at(x, y)
    print(f"Got point at ({x}, {y}): {point}")

    # Check that grid_pos property exists and returns correct value
    if not hasattr(point, 'grid_pos'):
        print(f"FAIL: GridPoint at ({x}, {y}) has no 'grid_pos' attribute")
        all_passed = False
        continue

    grid_pos = point.grid_pos

    # Verify it's a tuple
    if not isinstance(grid_pos, tuple):
        print(f"FAIL: grid_pos is {type(grid_pos).__name__}, expected tuple")
        all_passed = False
        continue

    # Verify it has correct length
    if len(grid_pos) != 2:
        print(f"FAIL: grid_pos has length {len(grid_pos)}, expected 2")
        all_passed = False
        continue

    # Verify correct values
    if grid_pos != (x, y):
        print(f"FAIL: grid_pos = {grid_pos}, expected ({x}, {y})")
        all_passed = False
        continue

    print(f"OK: GridPoint at ({x}, {y}) has grid_pos = {grid_pos}")

# Test that grid_pos is read-only (should raise AttributeError)
point = grid.at(2, 3)
try:
    point.grid_pos = (5, 5)
    print("FAIL: grid_pos should be read-only but allowed assignment")
    all_passed = False
except AttributeError:
    print("OK: grid_pos is read-only (raises AttributeError on assignment)")
except Exception as e:
    print(f"FAIL: Unexpected exception on assignment: {type(e).__name__}: {e}")
    all_passed = False

# Verify the repr includes the coordinates
point = grid.at(4, 6)
repr_str = repr(point)
if "(4, 6)" in repr_str:
    print(f"OK: repr includes coordinates: {repr_str}")
else:
    print(f"Note: repr format: {repr_str}")

if all_passed:
    print("PASS")
    sys.exit(0)
else:
    print("FAIL")
    sys.exit(1)
