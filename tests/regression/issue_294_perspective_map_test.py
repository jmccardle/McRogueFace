"""
Regression for #294: entity.perspective_map replaces the old gridstate array.

Verifies:
- visible subset discovered invariant holds after every updateVisibility()
  (no cell is VISIBLE without also being, at minimum, DISCOVERED when the
   entity next looks away)
- Grid-transition round-trip: save perspective on grid A, restore on
  same-sized grid B, FOV continues correctly without wiping prior knowledge.
"""
import mcrfpy
import sys


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def check_invariant(pm):
    """Every value in the map is 0, 1, or 2 (structural visible<=discovered)."""
    for y in range(pm.size[1]):
        for x in range(pm.size[0]):
            v = int(pm[x, y])
            if v not in (0, 1, 2):
                fail(f"pm[{x},{y}] = {v}, must be 0/1/2 (structural invariant)")


def main():
    scene = mcrfpy.Scene("issue_294_regression")
    mcrfpy.current_scene = scene

    # Scenario 1: invariant after repeated movement + updateVisibility.
    grid_a = mcrfpy.Grid(grid_size=(15, 10))
    scene.children.append(grid_a)
    e = mcrfpy.Entity(grid_pos=(7, 5))
    grid_a.entities.append(e)

    for target in [(7, 5), (3, 3), (12, 8), (1, 1), (14, 9), (7, 5)]:
        e.grid_pos = target
        e.update_visibility()
        check_invariant(e.perspective_map)

    # Scenario 2: a previously-seen cell that moves out of FOV is DISCOVERED
    # (not UNKNOWN) — the hallmark of the 3-state model.
    e.grid_pos = (7, 5)
    e.update_visibility()
    pm = e.perspective_map
    # Collect cells VISIBLE at origin
    origin_visible = [(x, y) for y in range(10) for x in range(15)
                      if int(pm[x, y]) == 2]
    if not origin_visible:
        fail("expected at least one VISIBLE cell at origin position")

    # Move far away so fewer of the origin cells are in FOV
    e.grid_pos = (14, 9)
    e.update_visibility()
    for (x, y) in origin_visible:
        v = int(pm[x, y])
        if v == 0:
            fail(f"cell ({x},{y}) was VISIBLE then moved out of FOV — "
                 f"should be DISCOVERED (1), not UNKNOWN (0)")

    # Scenario 3: serialize on grid A, restore on grid B (same size), FOV continues.
    e.grid_pos = (7, 5)
    e.update_visibility()
    saved_bytes = e.perspective_map.to_bytes()

    grid_b = mcrfpy.Grid(grid_size=(15, 10))
    scene.children.append(grid_b)
    e.grid = grid_b  # remove from A, add to B
    e.grid_pos = (7, 5)

    # On the new grid, perspective_map lazy-allocates fresh (all zeros).
    # Assign the saved bytes to restore.
    restored = mcrfpy.DiscreteMap.from_bytes(saved_bytes, (15, 10))
    e.perspective_map = restored

    pm_b = e.perspective_map
    # Prior DISCOVERED/VISIBLE cells should still be there.
    seen_any = False
    for y in range(10):
        for x in range(15):
            if int(pm_b[x, y]) >= 1:
                seen_any = True
                break
        if seen_any:
            break
    if not seen_any:
        fail("after restore, at least one cell should be DISCOVERED (>=1)")

    # update_visibility on grid B should promote cells in new FOV to VISIBLE
    # but preserve DISCOVERED cells elsewhere.
    e.update_visibility()
    check_invariant(pm_b)
    if int(pm_b[7, 5]) != 2:
        fail("entity's cell on grid B should be VISIBLE after update_visibility")

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
