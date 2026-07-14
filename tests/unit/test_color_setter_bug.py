#!/usr/bin/env python3
"""Test that the grid cell Color setter does not leave a pending exception.

Original bug: PyObject_to_sfColor in UIGridPoint.cpp called PyArg_ParseTuple to
parse the assigned color. When handed an mcrfpy.Color object (rather than a
tuple) the parse failed, the setter swallowed the failure without clearing the
error indicator, and the *pending* exception then erupted out of the next,
totally unrelated Python operation (e.g. `range(25)`).

GridPoint.color no longer exists; per-cell color now lives on a ColorLayer
(grid.add_layer(mcrfpy.ColorLayer(...)); layer.set((x, y), color)). This test is
retargeted onto that successor API, preserving the original intent:
  - a tuple is accepted
  - an mcrfpy.Color object is accepted (the case that used to fail)
  - neither leaves a stray pending exception that surfaces later
  - the assigned color actually round-trips
"""

import mcrfpy
import sys

failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  PASS: {label}")
    else:
        print(f"  FAIL: {label} {detail}")
        failures.append(label)


def make_color_layer(w, h):
    scene = mcrfpy.Scene(f"colorsetter_{w}x{h}")
    grid = mcrfpy.Grid(grid_size=(w, h))
    layer = mcrfpy.ColorLayer(name="bg")
    grid.add_layer(layer)
    return grid, layer


print("Testing grid cell color setter (pending-exception bug)...")
print("=" * 50)

# Test 1: Setting color with a tuple (the path that always worked)
print("Test 1: Setting color with tuple")
try:
    grid, layer = make_color_layer(5, 5)
    layer.set((0, 0), (200, 200, 220))

    # The original bug surfaced here: an unrelated op raising the pending error.
    _ = list(range(1))

    c = layer.at((0, 0))
    check("tuple assignment raises nothing", True)
    check(
        "tuple color round-trips",
        (c.r, c.g, c.b) == (200, 200, 220),
        f"got ({c.r}, {c.g}, {c.b})",
    )
except Exception as e:
    check("tuple assignment", False, f"{type(e).__name__}: {e}")

print()

# Test 2: Setting color with a Color object (this is what used to set the
# pending exception). It must now work outright -- no exception, pending or not.
print("Test 2: Setting color with Color object")
try:
    grid, layer = make_color_layer(5, 5)
    layer.set((0, 0), mcrfpy.Color(200, 200, 220))

    # If a stale error indicator were left behind, this innocent call would
    # raise it instead.
    _ = list(range(1))

    c = layer.at((0, 0))
    check("Color object assignment raises nothing", True)
    check(
        "Color object round-trips",
        (c.r, c.g, c.b) == (200, 200, 220),
        f"got ({c.r}, {c.g}, {c.b})",
    )
except Exception as e:
    check("Color object assignment", False, f"{type(e).__name__}: {e}")

print()

# Test 3: Many Color assignments in a row (reproduces the original failure
# shape: the error only became visible on a later, unrelated operation).
print("Test 3: Multiple Color assignments (reproducing original bug)")
try:
    grid, layer = make_color_layer(25, 15)

    for y in range(2):
        for x in range(25):
            layer.set((x, y), mcrfpy.Color(200, 200, 220))

    # The canary from the original bug report.
    for i in range(25):
        pass

    c = layer.at((24, 1))
    check("50 Color assignments leave no pending exception", True)
    check(
        "last assigned cell round-trips",
        (c.r, c.g, c.b) == (200, 200, 220),
        f"got ({c.r}, {c.g}, {c.b})",
    )
except Exception as e:
    check("multiple Color assignments", False, f"{type(e).__name__}: {e}")

print()

# Test 4: A genuinely bad color must raise a REAL exception, immediately -- the
# other half of the bug was errors being set but never raised.
print("Test 4: Invalid color raises immediately")
try:
    grid, layer = make_color_layer(5, 5)
    try:
        layer.set((0, 0), "not a color")
        check("invalid color raises", False, "no exception raised")
    except TypeError:
        check("invalid color raises TypeError at the call site", True)

    # And the failed call must not have left an error indicator behind.
    _ = list(range(1))
    check("failed set leaves no pending exception", True)
except Exception as e:
    check("invalid color handling", False, f"{type(e).__name__}: {e}")

print()
print("=" * 50)
if failures:
    print(f"FAILED ({len(failures)}): {', '.join(failures)}")
    sys.exit(1)

print("PASS")
sys.exit(0)
