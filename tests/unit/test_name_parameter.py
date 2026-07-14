#!/usr/bin/env python3
"""Test the name parameter in constructors"""

import mcrfpy
import sys

failures = []

def check(label, fn, expected_name):
    """Construct an object, verify the name parameter round-trips."""
    try:
        obj = fn()
    except Exception as e:
        failures.append(f"{label}: construction failed: {e!r}")
        print(f"FAIL {label}: construction failed: {e!r}")
        return None
    if obj.name != expected_name:
        failures.append(f"{label}: name is {obj.name!r}, expected {expected_name!r}")
        print(f"FAIL {label}: name is {obj.name!r}, expected {expected_name!r}")
        return obj
    print(f"OK   {label}: name={obj.name!r}")
    return obj

# name= keyword accepted by every drawable/entity constructor
check("Frame", lambda: mcrfpy.Frame(name="test_frame"), "test_frame")
check("Grid", lambda: mcrfpy.Grid(name="test_grid"), "test_grid")
check("Sprite", lambda: mcrfpy.Sprite(name="test_sprite"), "test_sprite")
check("Caption", lambda: mcrfpy.Caption(name="test_caption"), "test_caption")
check("Entity", lambda: mcrfpy.Entity(name="test_entity"), "test_entity")

# Mixed positional args and name= keyword: the positional args must not be
# disturbed by the trailing keyword.
frame2 = check(
    "Frame(positional + name)",
    lambda: mcrfpy.Frame((10, 10), (100, 100), name="positioned_frame"),
    "positioned_frame",
)
if frame2 is not None:
    geometry = (frame2.x, frame2.y, frame2.w, frame2.h)
    if geometry != (10.0, 10.0, 100.0, 100.0):
        failures.append(f"Frame(positional + name): geometry is {geometry}, expected (10.0, 10.0, 100.0, 100.0)")
        print(f"FAIL Frame(positional + name): geometry is {geometry}")
    else:
        print(f"OK   Frame(positional + name): pos=({frame2.x}, {frame2.y}), size=({frame2.w}, {frame2.h})")

# A name given at construction must be findable by mcrfpy.find() once the
# object is in a scene -- that is what the name parameter is FOR.
scene = mcrfpy.Scene("name_param_test")
named = mcrfpy.Frame(pos=(5, 5), size=(20, 20), name="findable_frame")
scene.children.append(named)
found = mcrfpy.find("findable_frame", "name_param_test")
if found is None:
    failures.append("find(): could not find 'findable_frame' by its constructor-assigned name")
    print("FAIL find(): could not find 'findable_frame' by its constructor-assigned name")
elif found is not named:
    failures.append(f"find(): returned {found!r}, expected the same object appended to the scene")
    print(f"FAIL find(): returned {found!r}, not the original object")
else:
    print("OK   find(): constructor-assigned name is findable in the scene")

if failures:
    print(f"\nFAIL: {len(failures)} name parameter check(s) failed")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("\nPASS: all name parameter tests complete")
sys.exit(0)
