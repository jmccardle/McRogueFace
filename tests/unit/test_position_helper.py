#!/usr/bin/env python3
"""Test script for PyPositionHelper - validates Grid.at() position parsing.

This tests the standardized position argument parsing that supports:
- Two separate args: func(x, y)
- A tuple: func((x, y))
- A list: func([x, y])
- A Vector object: func(Vector(x, y))
- Keyword args: func(x=x, y=y) or func(pos=(x,y))
"""

import sys
import mcrfpy

def test_grid_at_position_parsing():
    """Test all the different ways to call Grid.at() with positions."""

    # Create a test scene and grid
    scene = mcrfpy.Scene("test_position")

    # Create a grid with enough cells to test indexing
    grid = mcrfpy.Grid(grid_x=10, grid_y=10)

    errors = []

    # Test 1: Two separate integer arguments
    try:
        point1 = grid.at(3, 4)
        if point1 is None:
            errors.append("Test 1 FAIL: grid.at(3, 4) returned None")
        else:
            print("Test 1 PASS: grid.at(3, 4) works")
    except Exception as e:
        errors.append(f"Test 1 FAIL: grid.at(3, 4) raised {type(e).__name__}: {e}")

    # Test 2: Tuple argument
    try:
        point2 = grid.at((5, 6))
        if point2 is None:
            errors.append("Test 2 FAIL: grid.at((5, 6)) returned None")
        else:
            print("Test 2 PASS: grid.at((5, 6)) works")
    except Exception as e:
        errors.append(f"Test 2 FAIL: grid.at((5, 6)) raised {type(e).__name__}: {e}")

    # Test 3: List argument
    try:
        point3 = grid.at([7, 8])
        if point3 is None:
            errors.append("Test 3 FAIL: grid.at([7, 8]) returned None")
        else:
            print("Test 3 PASS: grid.at([7, 8]) works")
    except Exception as e:
        errors.append(f"Test 3 FAIL: grid.at([7, 8]) raised {type(e).__name__}: {e}")

    # Test 4: Vector argument
    try:
        vec = mcrfpy.Vector(2, 3)
        point4 = grid.at(vec)
        if point4 is None:
            errors.append("Test 4 FAIL: grid.at(Vector(2, 3)) returned None")
        else:
            print("Test 4 PASS: grid.at(Vector(2, 3)) works")
    except Exception as e:
        errors.append(f"Test 4 FAIL: grid.at(Vector(2, 3)) raised {type(e).__name__}: {e}")

    # Test 5: Keyword arguments x=, y=
    try:
        point5 = grid.at(x=1, y=2)
        if point5 is None:
            errors.append("Test 5 FAIL: grid.at(x=1, y=2) returned None")
        else:
            print("Test 5 PASS: grid.at(x=1, y=2) works")
    except Exception as e:
        errors.append(f"Test 5 FAIL: grid.at(x=1, y=2) raised {type(e).__name__}: {e}")

    # Test 6: pos= keyword with tuple
    try:
        point6 = grid.at(pos=(4, 5))
        if point6 is None:
            errors.append("Test 6 FAIL: grid.at(pos=(4, 5)) returned None")
        else:
            print("Test 6 PASS: grid.at(pos=(4, 5)) works")
    except Exception as e:
        errors.append(f"Test 6 FAIL: grid.at(pos=(4, 5)) raised {type(e).__name__}: {e}")

    # Test 7: pos= keyword with Vector
    try:
        vec2 = mcrfpy.Vector(6, 7)
        point7 = grid.at(pos=vec2)
        if point7 is None:
            errors.append("Test 7 FAIL: grid.at(pos=Vector(6, 7)) returned None")
        else:
            print("Test 7 PASS: grid.at(pos=Vector(6, 7)) works")
    except Exception as e:
        errors.append(f"Test 7 FAIL: grid.at(pos=Vector(6, 7)) raised {type(e).__name__}: {e}")

    # Test 8: pos= keyword with list
    try:
        point8 = grid.at(pos=[8, 9])
        if point8 is None:
            errors.append("Test 8 FAIL: grid.at(pos=[8, 9]) returned None")
        else:
            print("Test 8 PASS: grid.at(pos=[8, 9]) works")
    except Exception as e:
        errors.append(f"Test 8 FAIL: grid.at(pos=[8, 9]) raised {type(e).__name__}: {e}")

    # Test 9: Out of range should raise IndexError (not TypeError)
    try:
        grid.at(100, 100)
        errors.append("Test 9 FAIL: grid.at(100, 100) should have raised IndexError")
    except IndexError:
        print("Test 9 PASS: grid.at(100, 100) raises IndexError")
    except Exception as e:
        errors.append(f"Test 9 FAIL: grid.at(100, 100) raised {type(e).__name__} instead of IndexError: {e}")

    # Test 10: Invalid type should raise TypeError
    try:
        grid.at("invalid")
        errors.append("Test 10 FAIL: grid.at('invalid') should have raised TypeError")
    except TypeError:
        print("Test 10 PASS: grid.at('invalid') raises TypeError")
    except Exception as e:
        errors.append(f"Test 10 FAIL: grid.at('invalid') raised {type(e).__name__} instead of TypeError: {e}")

    # Test 11: Float integers should work (e.g., 3.0 is valid as int)
    try:
        point11 = grid.at(3.0, 4.0)
        if point11 is None:
            errors.append("Test 11 FAIL: grid.at(3.0, 4.0) returned None")
        else:
            print("Test 11 PASS: grid.at(3.0, 4.0) works (float integers)")
    except Exception as e:
        errors.append(f"Test 11 FAIL: grid.at(3.0, 4.0) raised {type(e).__name__}: {e}")

    # Test 12: Non-integer float should raise TypeError
    try:
        grid.at(3.5, 4.5)
        errors.append("Test 12 FAIL: grid.at(3.5, 4.5) should have raised TypeError")
    except TypeError:
        print("Test 12 PASS: grid.at(3.5, 4.5) raises TypeError for non-integer floats")
    except Exception as e:
        errors.append(f"Test 12 FAIL: grid.at(3.5, 4.5) raised {type(e).__name__} instead of TypeError: {e}")

    # Summary
    print()
    print("=" * 50)
    if errors:
        print(f"FAILED: {len(errors)} test(s) failed")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("SUCCESS: All 12 tests passed!")
        sys.exit(0)

# Run tests immediately (no game loop needed for this)
test_grid_at_position_parsing()
