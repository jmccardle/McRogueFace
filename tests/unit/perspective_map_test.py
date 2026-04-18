"""
Tests for Entity.perspective_map (#294).

Covers:
- Lazy allocation (None when no grid; allocated on first access with a grid)
- Identity: multiple accesses share the same underlying DiscreteMap
- Three-state values: 0=UNKNOWN, 1=DISCOVERED, 2=VISIBLE
- perspective_map[x, y] returns Perspective enum members
- visible subset discovered invariant after updateVisibility
- entity.at() returns GridPoint when VISIBLE, None otherwise
"""
import mcrfpy
import sys


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    scene = mcrfpy.Scene("perspective_map_test")
    mcrfpy.current_scene = scene

    # Entity without a grid -> perspective_map is None
    orphan = mcrfpy.Entity(grid_pos=(0, 0))
    if orphan.perspective_map is not None:
        fail("entity without grid should have perspective_map == None")

    # Attach to a grid; perspective_map lazy-allocates on first access
    grid = mcrfpy.Grid(grid_size=(12, 9))
    scene.children.append(grid)
    e = mcrfpy.Entity(grid_pos=(4, 3))
    grid.entities.append(e)

    pm = e.perspective_map
    if pm is None:
        fail("perspective_map should be allocated once entity has a grid")
    if pm.size != (12, 9):
        fail(f"perspective_map size should match grid size, got {pm.size}")

    # Initial state: all UNKNOWN
    for y in range(9):
        for x in range(12):
            if int(pm[x, y]) != 0:
                fail(f"initial pm[{x},{y}] should be 0, got {pm[x, y]}")

    # Identity: a second access wraps the same shared DiscreteMap.
    # Mutating through one is visible through the other.
    pm2 = e.perspective_map
    pm2[1, 1] = 2
    if int(pm[1, 1]) != 2:
        fail("perspective_map accesses should share underlying buffer")

    # Values returned as Perspective enum members (IntEnum).
    pm[2, 2] = 1
    val = pm[2, 2]
    if val != mcrfpy.Perspective.DISCOVERED:
        fail(f"pm[2,2] should equal Perspective.DISCOVERED, got {val!r}")
    if int(val) != 1:
        fail(f"IntEnum comparison failed: int(pm[2,2]) = {int(val)}")

    # updateVisibility yields VISIBLE at entity's cell, UNKNOWN far away
    # (beyond FOV radius). We first wipe whatever leaked in.
    pm.fill(0)
    e.update_visibility()
    at_entity = pm[4, 3]
    if at_entity != mcrfpy.Perspective.VISIBLE:
        fail(f"entity's cell should be VISIBLE after update_visibility, got {at_entity}")

    # Invariant: any VISIBLE cell remains at least DISCOVERED after the entity
    # moves away and we re-update.
    visible_before = set()
    for y in range(9):
        for x in range(12):
            if int(pm[x, y]) == 2:
                visible_before.add((x, y))

    e.grid_pos = (0, 0)  # move far corner
    e.update_visibility()

    for (x, y) in visible_before:
        v = int(pm[x, y])
        if v < 1:
            fail(f"cell ({x},{y}) was VISIBLE, should now be at least DISCOVERED (>=1), got {v}")

    # entity.at(): VISIBLE -> GridPoint; else None.
    p = e.at(0, 0)
    if p is None:
        fail("entity.at(own cell) should return GridPoint (VISIBLE)")
    if not hasattr(p, "walkable"):
        fail("entity.at(visible) should return GridPoint with .walkable")

    # Find an UNKNOWN cell and verify at() returns None.
    found = False
    for y in range(9):
        for x in range(12):
            if int(pm[x, y]) == 0:
                if e.at(x, y) is not None:
                    fail(f"entity.at({x},{y}) on UNKNOWN cell should return None")
                found = True
                break
        if found:
            break
    # (Not fatal if no UNKNOWN cell exists — small grid + large FOV radius.)

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
