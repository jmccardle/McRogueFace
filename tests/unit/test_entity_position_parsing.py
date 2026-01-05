"""Test Entity.at() and Entity.path_to() position argument parsing.

These methods should accept:
- Two separate integers: method(x, y)
- A tuple: method((x, y))
- Keyword arguments: method(x=x, y=y) or method(pos=(x, y))
- A Vector: method(Vector(x, y))
"""
import mcrfpy
import sys

def run_tests():
    # Create a grid with some walkable cells
    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(320, 320))

    # Make the grid walkable
    for x in range(10):
        for y in range(10):
            grid.at(x, y).walkable = True

    # Create an entity at (2, 2)
    entity = mcrfpy.Entity(grid_pos=(2, 2), grid=grid)

    print("Testing Entity.at() position parsing...")

    # Test 1: Two separate integers
    try:
        state1 = entity.at(3, 3)
        print("  PASS: entity.at(3, 3)")
    except Exception as e:
        print(f"  FAIL: entity.at(3, 3) - {e}")
        return False

    # Test 2: Tuple argument
    try:
        state2 = entity.at((4, 4))
        print("  PASS: entity.at((4, 4))")
    except Exception as e:
        print(f"  FAIL: entity.at((4, 4)) - {e}")
        return False

    # Test 3: Keyword arguments
    try:
        state3 = entity.at(x=5, y=5)
        print("  PASS: entity.at(x=5, y=5)")
    except Exception as e:
        print(f"  FAIL: entity.at(x=5, y=5) - {e}")
        return False

    # Test 4: pos= keyword argument
    try:
        state4 = entity.at(pos=(6, 6))
        print("  PASS: entity.at(pos=(6, 6))")
    except Exception as e:
        print(f"  FAIL: entity.at(pos=(6, 6)) - {e}")
        return False

    # Test 5: List argument
    try:
        state5 = entity.at([7, 7])
        print("  PASS: entity.at([7, 7])")
    except Exception as e:
        print(f"  FAIL: entity.at([7, 7]) - {e}")
        return False

    # Test 6: Vector argument
    try:
        vec = mcrfpy.Vector(8, 8)
        state6 = entity.at(vec)
        print("  PASS: entity.at(Vector(8, 8))")
    except Exception as e:
        print(f"  FAIL: entity.at(Vector(8, 8)) - {e}")
        return False

    print("\nTesting Entity.path_to() position parsing...")

    # Test 1: Two separate integers
    try:
        path1 = entity.path_to(5, 5)
        print("  PASS: entity.path_to(5, 5)")
    except Exception as e:
        print(f"  FAIL: entity.path_to(5, 5) - {e}")
        return False

    # Test 2: Tuple argument
    try:
        path2 = entity.path_to((6, 6))
        print("  PASS: entity.path_to((6, 6))")
    except Exception as e:
        print(f"  FAIL: entity.path_to((6, 6)) - {e}")
        return False

    # Test 3: Keyword arguments
    try:
        path3 = entity.path_to(x=7, y=7)
        print("  PASS: entity.path_to(x=7, y=7)")
    except Exception as e:
        print(f"  FAIL: entity.path_to(x=7, y=7) - {e}")
        return False

    # Test 4: pos= keyword argument
    try:
        path4 = entity.path_to(pos=(8, 8))
        print("  PASS: entity.path_to(pos=(8, 8))")
    except Exception as e:
        print(f"  FAIL: entity.path_to(pos=(8, 8)) - {e}")
        return False

    # Test 5: List argument
    try:
        path5 = entity.path_to([9, 9])
        print("  PASS: entity.path_to([9, 9])")
    except Exception as e:
        print(f"  FAIL: entity.path_to([9, 9]) - {e}")
        return False

    # Test 6: Vector argument
    try:
        vec = mcrfpy.Vector(4, 4)
        path6 = entity.path_to(vec)
        print("  PASS: entity.path_to(Vector(4, 4))")
    except Exception as e:
        print(f"  FAIL: entity.path_to(Vector(4, 4)) - {e}")
        return False

    print("\nAll tests passed!")
    return True

# Run tests immediately (no game loop needed for these)
if run_tests():
    print("PASS")
    sys.exit(0)
else:
    print("FAIL")
    sys.exit(1)
