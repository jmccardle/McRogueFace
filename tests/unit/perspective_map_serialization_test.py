"""
Tests for entity.perspective_map serialization round-trip and size validation (#294).

Covers:
- to_bytes() / from_bytes() preserves all three perspective states
- Assigning a size-mismatched DiscreteMap raises ValueError
- Assigning None clears (and getter lazy-reallocates fresh)
- Assigning a matching DiscreteMap replaces the entity's memory
"""
import mcrfpy
import sys


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    scene = mcrfpy.Scene("serialization_test")
    mcrfpy.current_scene = scene

    grid = mcrfpy.Grid(grid_size=(8, 6))
    scene.children.append(grid)
    e = mcrfpy.Entity(grid_pos=(2, 2))
    grid.entities.append(e)

    pm = e.perspective_map

    # Place each of the three states at known positions.
    pm[0, 0] = 0  # UNKNOWN
    pm[1, 1] = 1  # DISCOVERED
    pm[2, 2] = 2  # VISIBLE

    # Round-trip via bytes.
    raw = pm.to_bytes()
    if len(raw) != 8 * 6:
        fail(f"to_bytes length should be {8*6}, got {len(raw)}")

    restored = mcrfpy.DiscreteMap.from_bytes(raw, (8, 6))
    if int(restored[0, 0]) != 0:
        fail(f"restored[0,0] should be 0, got {restored[0, 0]}")
    if int(restored[1, 1]) != 1:
        fail(f"restored[1,1] should be 1, got {restored[1, 1]}")
    if int(restored[2, 2]) != 2:
        fail(f"restored[2,2] should be 2, got {restored[2, 2]}")

    # Assign restored back to the entity.
    e.perspective_map = restored
    after = e.perspective_map
    if int(after[1, 1]) != 1 or int(after[2, 2]) != 2:
        fail("entity.perspective_map = restored should replace memory")

    # Size mismatch raises ValueError.
    wrong = mcrfpy.DiscreteMap((4, 4))
    try:
        e.perspective_map = wrong
        fail("size-mismatched assignment should raise ValueError")
    except ValueError as err:
        # message should mention size/grid/match
        msg = str(err).lower()
        if "size" not in msg and "match" not in msg:
            fail(f"ValueError message should mention size mismatch, got: {err}")

    # None clears.
    e.perspective_map = None
    fresh = e.perspective_map  # lazy-reallocates
    if fresh is None:
        fail("perspective_map should be lazy-reallocated after = None")
    for y in range(6):
        for x in range(8):
            if int(fresh[x, y]) != 0:
                fail(f"after clear, fresh[{x},{y}] should be 0, got {fresh[x, y]}")

    # Type check: non-DiscreteMap raises TypeError.
    try:
        e.perspective_map = [0, 1, 2]
        fail("non-DiscreteMap assignment should raise TypeError")
    except TypeError:
        pass

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
