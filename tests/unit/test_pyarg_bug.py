#!/usr/bin/env python3
"""Regression test for the PyArg bug in the Grid constructor.

Original bug theory: UIGrid::init called PyArg_ParseTupleAndKeywords without
checking its return value, so a failed parse left an exception pending on the
stack. The grid was built anyway (with defaults), and the stale exception then
surfaced at some unrelated later call.

This test pins the constructor's argument parsing down for real:
  - every accepted spelling of "make a 25x15 grid" produces a 25x15 grid,
  - no successful construction leaves a pending exception behind,
  - every rejected spelling raises a clean exception AND leaves the interpreter
    usable (no residue that poisons the next call).

API note (#361): the Grid constructor's POSITIONAL order is
(pos, size, grid_size, texture) -- not (grid_w, grid_h). Grid dimensions are
given by grid_size=(w, h) or by the grid_w=/grid_h= keywords. The old
`Grid(25, 15)` positional spelling now means pos=25, size=15 and is not a way
to size a grid; that check is updated to the current contract below.
"""

import sys

import mcrfpy

failures = []


def check(condition, label):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}")
        failures.append(label)


def dims(grid):
    return (int(grid.grid_size.x), int(grid.grid_size.y))


def no_pending_exception(label):
    """A pending-but-unreturned C exception surfaces at the next Python call."""
    try:
        _ = list(range(1))
    except BaseException as e:  # pragma: no cover - this is the bug being tested
        check(False, f"{label}: stale exception leaked: {type(e).__name__}: {e}")
        return
    check(sys.exc_info() == (None, None, None), f"{label}: no exception pending")


print("Testing Grid constructor argument parsing...")
print("=" * 50)

print("Test 1: grid_size tuple")
grid1 = mcrfpy.Grid(grid_size=(25, 15))
check(dims(grid1) == (25, 15), f"Grid(grid_size=(25,15)) -> {dims(grid1)}")
no_pending_exception("Grid(grid_size=(25,15))")

print()
print("Test 2: grid_w/grid_h keyword args (the historically failing case)")
grid2 = mcrfpy.Grid(grid_w=25, grid_h=15)
check(dims(grid2) == (25, 15), f"Grid(grid_w=25, grid_h=15) -> {dims(grid2)}")
no_pending_exception("Grid(grid_w=25, grid_h=15)")

print()
print("Test 3: Check if it's specific to the values 25, 15")
for x, y in [(24, 15), (25, 14), (25, 15), (26, 15), (25, 16)]:
    grid = mcrfpy.Grid(grid_w=x, grid_h=y)
    check(dims(grid) == (x, y), f"Grid(grid_w={x}, grid_h={y}) -> {dims(grid)}")
    no_pending_exception(f"Grid(grid_w={x}, grid_h={y})")

print()
print("Test 4: Mix positional and keyword args")
# Positional slot 0 is pos (#361), so this is "a 25x15 grid drawn at (10, 20)".
grid3 = mcrfpy.Grid((10, 20), grid_w=25, grid_h=15)
check(dims(grid3) == (25, 15), f"Grid((10,20), grid_w=25, grid_h=15) -> {dims(grid3)}")
check((grid3.pos.x, grid3.pos.y) == (10, 20), f"positional pos honored -> {grid3.pos}")
no_pending_exception("Grid((10,20), grid_w=25, grid_h=15)")

print()
print("Test 5: Additional arguments alongside the grid dimensions")
grid4 = mcrfpy.Grid(grid_w=25, grid_h=15, pos=(0, 0))
check(dims(grid4) == (25, 15), f"Grid(..., pos=(0,0)) -> {dims(grid4)}")
no_pending_exception("Grid(..., pos=(0,0))")

grid5 = mcrfpy.Grid(grid_w=25, grid_h=15, texture=None)
check(dims(grid5) == (25, 15), f"Grid(..., texture=None) -> {dims(grid5)}")
no_pending_exception("Grid(..., texture=None)")

print()
print("Test 6: Bad arguments raise cleanly and leave no residue")
bad_calls = [
    ("grid_size not a tuple", lambda: mcrfpy.Grid(grid_size="nope"), TypeError),
    ("unknown keyword", lambda: mcrfpy.Grid(grid_size=(4, 4), bogus=3), TypeError),
    ("grid= with grid_size=", lambda: mcrfpy.Grid(grid=mcrfpy.Grid(grid_size=(4, 4)),
                                                  grid_size=(5, 5)), TypeError),
]
for label, call, expected in bad_calls:
    try:
        call()
    except expected as e:
        check(True, f"{label} -> {type(e).__name__}: {e}")
    except BaseException as e:
        check(False, f"{label} -> wrong exception {type(e).__name__}: {e}")
    else:
        check(False, f"{label} -> no exception raised")
    # The failed parse must not poison the interpreter for the next caller.
    survivor = mcrfpy.Grid(grid_w=7, grid_h=3)
    check(dims(survivor) == (7, 3), f"{label}: next Grid() still correct")
    no_pending_exception(f"{label}: after failure")

print()
print("=" * 50)
if failures:
    print(f"FAIL: {len(failures)} check(s) failed")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("PASS")
sys.exit(0)
