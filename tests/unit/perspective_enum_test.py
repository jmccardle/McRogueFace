"""
Tests for mcrfpy.Perspective enum and entity.at() new semantics (#294).
"""
import mcrfpy
import sys


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    # Enum members
    p = mcrfpy.Perspective
    if int(p.UNKNOWN) != 0:
        fail("Perspective.UNKNOWN should be 0")
    if int(p.DISCOVERED) != 1:
        fail("Perspective.DISCOVERED should be 1")
    if int(p.VISIBLE) != 2:
        fail("Perspective.VISIBLE should be 2")

    # IntEnum: equality with ints both ways
    if p.VISIBLE != 2 or 2 != p.VISIBLE:
        fail("IntEnum equality failed")

    # Repr uses the enum name
    if repr(p.DISCOVERED) != "Perspective.DISCOVERED":
        fail(f"unexpected repr: {repr(p.DISCOVERED)}")

    # entity.at() semantics: VISIBLE -> GridPoint, else None.
    scene = mcrfpy.Scene("perspective_enum")
    mcrfpy.current_scene = scene
    grid = mcrfpy.Grid(grid_size=(7, 5))
    scene.children.append(grid)
    e = mcrfpy.Entity(grid_pos=(3, 2))
    grid.entities.append(e)

    # Without update_visibility, perspective_map is all-zero.
    if e.at(3, 2) is not None:
        fail("before update_visibility, at() should return None (cells are UNKNOWN)")

    e.update_visibility()
    p_here = e.at(3, 2)
    if p_here is None:
        fail("after update_visibility, at(own cell) should return a GridPoint")
    if not hasattr(p_here, "walkable"):
        fail("at() return should be a GridPoint (has .walkable)")

    # Manually promote a cell to DISCOVERED only, confirm at() still returns None.
    pm = e.perspective_map
    # Find a cell currently UNKNOWN, set to DISCOVERED, confirm at() -> None.
    for y in range(5):
        for x in range(7):
            if int(pm[x, y]) == 0:
                pm[x, y] = 1  # DISCOVERED
                if e.at(x, y) is not None:
                    fail(f"DISCOVERED-only cell ({x},{y}): at() should return None")
                pm[x, y] = 2  # VISIBLE
                if e.at(x, y) is None:
                    fail(f"VISIBLE cell ({x},{y}): at() should return a GridPoint")
                break
        else:
            continue
        break

    # Accept enum as Perspective value assignment via subscript
    pm[0, 0] = mcrfpy.Perspective.VISIBLE
    if int(pm[0, 0]) != 2:
        fail("DiscreteMap subscript should accept Perspective enum member")

    # Out-of-bounds at() raises IndexError
    try:
        e.at(100, 100)
        fail("out-of-bounds at() should raise IndexError")
    except IndexError:
        pass

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
