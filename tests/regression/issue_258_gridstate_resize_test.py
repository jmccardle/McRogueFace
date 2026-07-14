"""Regression test: entity perspective map must resize when moving between grids.

Issues #258-#263, #274, #276, #278: UIEntity gridstate heap overflows.

Bug: Gridstate was only initialized when empty (size == 0). When an entity
moved from a small grid to a larger grid via ANY transfer method, gridstate
kept the old size. Code then iterated using the new grid's dimensions,
writing past the vector's end.

Fix: the per-entity visibility buffer unconditionally checks its size against
the grid dimensions and reallocates if they don't match. Exercised here through
every transfer method: set_grid, append, extend, insert, setitem, slice assign.

Also tests #274: spatial_hash.remove() must be called when removing
entities from grids via set_grid(None) or set_grid(other_grid).

API NOTE (#294): entity.gridstate is now entity.perspective_map, a bounds-checked
DiscreteMap (UNKNOWN/DISCOVERED/VISIBLE) carrying its own .size, and it is *lazy* --
a transfer marks it stale and the next update_visibility() sizes it to the new grid
(see UIEntity::updateVisibility, src/UIEntity.cpp:51). So each case below transfers,
then calls update_visibility(), then asserts the buffer matches the new grid and that
cells only reachable in the NEW (larger) grid are addressable. Under the old bug those
reads/writes ran off the end of the old buffer.
"""
import mcrfpy
import sys

def open_grid(size):
    """Grid of `size` x `size` with all cells transparent/walkable, FOV enabled."""
    grid = mcrfpy.Grid(grid_size=(size, size))
    data = grid.grid_data
    for x in range(size):
        for y in range(size):
            point = data.at(x, y)
            point.transparent = True
            point.walkable = True
    data.fov_radius = 4
    return grid

def check_sized_to(entity, grid, label):
    """Buffer must match the grid, and the grid's far corner must be addressable."""
    entity.update_visibility()
    pmap = entity.perspective_map
    w, h = grid.grid_data.grid_w, grid.grid_data.grid_h
    assert pmap.size == (w, h), f"{label}: expected {(w, h)}, got {pmap.size}"
    # Under #258 this read walked off the end of the stale, smaller buffer.
    pmap.get(w - 1, h - 1)

def test_set_grid():
    """entity.grid = new_grid resizes the perspective map"""
    small = open_grid(10)
    large = open_grid(50)
    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=small)

    small.perspective = entity
    check_sized_to(entity, small, "set_grid/small")

    entity.grid = large
    large.perspective = entity
    check_sized_to(entity, large, "set_grid/large")
    print("  PASS: set_grid")

def test_append():
    """grid.entities.append(entity) resizes the perspective map"""
    small = open_grid(10)
    large = open_grid(40)
    entity = mcrfpy.Entity(grid_pos=(3, 3), grid=small)
    check_sized_to(entity, small, "append/small")

    large.entities.append(entity)
    check_sized_to(entity, large, "append/large")
    print("  PASS: append")

def test_extend():
    """grid.entities.extend([entity]) resizes the perspective map"""
    small = open_grid(10)
    large = open_grid(30)
    entity = mcrfpy.Entity(grid_pos=(3, 3), grid=small)
    check_sized_to(entity, small, "extend/small")

    large.entities.extend([entity])
    check_sized_to(entity, large, "extend/large")
    print("  PASS: extend")

def test_insert():
    """grid.entities.insert(0, entity) resizes the perspective map"""
    small = open_grid(10)
    large = open_grid(25)
    entity = mcrfpy.Entity(grid_pos=(3, 3), grid=small)
    check_sized_to(entity, small, "insert/small")

    large.entities.insert(0, entity)
    check_sized_to(entity, large, "insert/large")
    print("  PASS: insert")

def test_setitem():
    """grid.entities[0] = entity resizes the perspective map"""
    small = open_grid(10)
    large = open_grid(20)
    entity = mcrfpy.Entity(grid_pos=(3, 3), grid=small)
    check_sized_to(entity, small, "setitem/small")

    # Need a placeholder entity in large grid first
    placeholder = mcrfpy.Entity(grid_pos=(0, 0), grid=large)
    large.entities[0] = entity
    assert len(large.entities) == 1
    check_sized_to(entity, large, "setitem/large")
    print("  PASS: setitem")

def test_slice_assign():
    """grid.entities[0:1] = [entity] resizes the perspective map"""
    small = open_grid(10)
    large = open_grid(35)
    entity = mcrfpy.Entity(grid_pos=(3, 3), grid=small)
    check_sized_to(entity, small, "slice/small")

    placeholder = mcrfpy.Entity(grid_pos=(0, 0), grid=large)
    large.entities[0:1] = [entity]
    check_sized_to(entity, large, "slice/large")
    print("  PASS: slice_assign")

def test_update_visibility_after_transfer():
    """update_visibility works correctly after repeated grow/shrink transfers"""
    grids = [open_grid(s) for s in (5, 80, 3, 60, 10, 100)]
    entity = mcrfpy.Entity(grid_pos=(2, 2), grid=grids[0])

    for g in grids:
        entity.grid = g
        g.perspective = entity
        check_sized_to(entity, g, f"cycle/{g.grid_data.grid_w}")
    print("  PASS: update_visibility_after_transfer")

def test_at_after_transfer():
    """entity.at(x, y) works correctly after grid transfer"""
    small = open_grid(10)
    large = open_grid(50)
    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=small)
    entity.update_visibility()

    entity.grid = large
    large.perspective = entity
    # Stand on a cell that is out of bounds for the small grid entirely.
    entity.grid_pos = (30, 30)
    entity.update_visibility()

    # at() returns the GridPoint only when the cell is VISIBLE to this entity.
    state = entity.at(30, 30)
    assert state is not None, "entity's own cell must be visible after transfer"
    assert tuple(state.grid_pos) == (30, 30), f"got {tuple(state.grid_pos)}"
    # Far side of the new grid: addressable (not a heap read), just not visible.
    assert entity.at(5, 5) is None, "cell outside FOV must report as not visible"
    assert entity.perspective_map.get(49, 49) == mcrfpy.Perspective.UNKNOWN
    print("  PASS: at_after_transfer")

def test_set_grid_none():
    """entity.grid = None properly removes entity (tests #274)"""
    grid = open_grid(10)
    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)
    assert len(grid.entities) == 1
    entity.grid = None
    assert len(grid.entities) == 0
    assert entity.grid is None
    print("  PASS: set_grid_none")

def test_stress():
    """Stress test: rapid grid transfers with heap churn"""
    entity = mcrfpy.Entity(grid_pos=(2, 2))
    for i in range(20):
        small_g = mcrfpy.Grid(grid_size=(5, 5))
        entity.grid = small_g
        small_g.perspective = entity
        entity.update_visibility()
        assert entity.perspective_map.size == (5, 5)

        big_g = mcrfpy.Grid(grid_size=(80, 80))
        entity.grid = big_g
        big_g.perspective = entity
        entity.update_visibility()
        assert entity.perspective_map.size == (80, 80)

        frames = [mcrfpy.Frame() for _ in range(10)]
        del frames
    print("  PASS: stress")

print("Testing perspective map resize across transfer methods...")
try:
    test_set_grid()
    test_append()
    test_extend()
    test_insert()
    test_setitem()
    test_slice_assign()
    test_update_visibility_after_transfer()
    test_at_after_transfer()
    test_set_grid_none()
    test_stress()
except AssertionError as e:
    print(f"FAIL: {e}")
    sys.exit(1)
print("PASS: all perspective map resize tests passed")
sys.exit(0)
