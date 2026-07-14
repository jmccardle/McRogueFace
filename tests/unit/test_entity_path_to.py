#!/usr/bin/env python3
"""Test the Entity.path_to() method"""

import mcrfpy
import sys

print("Testing Entity.path_to() method...")
print("=" * 50)

failures = []

def check(label, condition, detail=""):
    if condition:
        print(f"  PASS {label}")
    else:
        print(f"  FAIL {label}: {detail}")
        failures.append(label)

# Create scene and grid
path_test = mcrfpy.Scene("path_test")
grid = mcrfpy.Grid(grid_size=(10, 10))

# Set up a simple map with some walls
for y in range(10):
    for x in range(10):
        grid.at(x, y).walkable = True
        grid.at(x, y).transparent = True

# Add some walls to create an interesting path
walls = [(3, 3), (3, 4), (3, 5), (4, 3), (5, 3)]
for x, y in walls:
    grid.at(x, y).walkable = False

# Create entity
entity = mcrfpy.Entity((2, 2), grid=grid)

# NOTE: entity.x/.y are pixel draw coords now; the logical cell is entity.cell_pos.
start = (int(entity.cell_pos.x), int(entity.cell_pos.y))
print(f"Entity at cell: {start}")
check("entity starts at (2, 2)", start == (2, 2), f"got {start}")


def validate_path(path, target):
    """A path must be a contiguous, wall-free walk ending on the target."""
    if not path:
        return "path is empty"
    if tuple(path[-1]) != target:
        return f"path does not end at {target}: {path[-1]}"
    prev = start
    for step in path:
        step = tuple(step)
        if step in walls:
            return f"path walks through wall {step}"
        dx, dy = abs(step[0] - prev[0]), abs(step[1] - prev[1])
        if max(dx, dy) != 1:
            return f"non-adjacent step {prev} -> {step}"
        prev = step
    return None


# Test 1: Simple path (positional x, y)
print("\nTest 1: Path to (6, 6)")
path = entity.path_to(6, 6)
print(f"  Path: {path}")
err = validate_path(path, (6, 6))
check("path_to(6, 6) returns a valid walk to (6, 6)", err is None, err or "")

# Test 2: Path using keyword arguments.
# API CHANGE: the old target_x=/target_y= keywords are gone; the position-spec
# parser now accepts pos=(x, y) (or a bare tuple/Vector).
print("\nTest 2: Path using keyword argument pos=(7, 7)")
path = entity.path_to(pos=(7, 7))
print(f"  Path: {path}")
err = validate_path(path, (7, 7))
check("path_to(pos=(7, 7)) returns a valid walk to (7, 7)", err is None, err or "")

# Test 3: Path to current position is empty (already there)
print("\nTest 3: Path to current position")
path = entity.path_to(2, 2)
print(f"  Path: {path}")
check("path_to(own position) is empty", path == [], f"got {path}")

# Test 4: Error cases
print("\nTest 4: Error handling")
try:
    entity.path_to(15, 15)
    check("out-of-bounds target raises ValueError", False, "no exception raised")
except ValueError as e:
    check("out-of-bounds target raises ValueError", True)
    print(f"    ({e})")
except Exception as e:
    check("out-of-bounds target raises ValueError", False,
          f"wrong exception type {type(e).__name__}: {e}")

# Test 5: Unreachable target -> empty path (wall off a cell completely)
print("\nTest 5: Unreachable target")
for x, y in [(8, 0), (8, 1), (9, 1)]:
    grid.at(x, y).walkable = False
path = entity.path_to(9, 0)
print(f"  Path: {path}")
check("walled-off target yields empty path", path == [], f"got {path}")

print("\n" + "=" * 50)
if failures:
    print(f"FAILED: {len(failures)} check(s): {failures}")
    sys.exit(1)
print("Entity.path_to() testing complete!")
print("PASS")
sys.exit(0)
