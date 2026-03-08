"""Regression test: entity gridstate must resize when moving between grids.

Issues #258-#263, #274, #276, #278: UIEntity gridstate heap overflows.

Bug: Gridstate was only initialized when empty (size == 0). When an entity
moved from a small grid to a larger grid via ANY transfer method, gridstate
kept the old size. Code then iterated using the new grid's dimensions,
writing past the vector's end.

Fix: ensureGridstate() unconditionally checks gridstate.size() against
grid dimensions and resizes if they don't match. Applied to all transfer
methods: set_grid, append, extend, insert, setitem, slice assignment.

Also tests #274: spatial_hash.remove() must be called when removing
entities from grids via set_grid(None) or set_grid(other_grid).
"""
import mcrfpy
import sys

def test_set_grid():
    """entity.grid = new_grid resizes gridstate"""
    small = mcrfpy.Grid(grid_size=(10, 10))
    large = mcrfpy.Grid(grid_size=(50, 50))
    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=small)

    small.perspective = entity
    small.fov_radius = 4
    entity.update_visibility()

    gs = entity.gridstate
    assert len(gs) == 100, f"Expected 100, got {len(gs)}"

    entity.grid = large
    gs = entity.gridstate
    assert len(gs) == 2500, f"Expected 2500, got {len(gs)}"

    large.perspective = entity
    large.fov_radius = 8
    entity.update_visibility()
    print("  PASS: set_grid")

def test_append():
    """grid.entities.append(entity) resizes gridstate"""
    small = mcrfpy.Grid(grid_size=(10, 10))
    large = mcrfpy.Grid(grid_size=(40, 40))
    entity = mcrfpy.Entity(grid_pos=(3, 3), grid=small)
    entity.update_visibility()

    gs = entity.gridstate
    assert len(gs) == 100, f"Expected 100, got {len(gs)}"

    large.entities.append(entity)
    gs = entity.gridstate
    assert len(gs) == 1600, f"Expected 1600, got {len(gs)}"
    print("  PASS: append")

def test_extend():
    """grid.entities.extend([entity]) resizes gridstate"""
    small = mcrfpy.Grid(grid_size=(10, 10))
    large = mcrfpy.Grid(grid_size=(30, 30))
    entity = mcrfpy.Entity(grid_pos=(3, 3), grid=small)
    entity.update_visibility()

    large.entities.extend([entity])
    gs = entity.gridstate
    assert len(gs) == 900, f"Expected 900, got {len(gs)}"
    print("  PASS: extend")

def test_insert():
    """grid.entities.insert(0, entity) resizes gridstate"""
    small = mcrfpy.Grid(grid_size=(10, 10))
    large = mcrfpy.Grid(grid_size=(25, 25))
    entity = mcrfpy.Entity(grid_pos=(3, 3), grid=small)
    entity.update_visibility()

    large.entities.insert(0, entity)
    gs = entity.gridstate
    assert len(gs) == 625, f"Expected 625, got {len(gs)}"
    print("  PASS: insert")

def test_setitem():
    """grid.entities[0] = entity resizes gridstate"""
    small = mcrfpy.Grid(grid_size=(10, 10))
    large = mcrfpy.Grid(grid_size=(20, 20))
    entity = mcrfpy.Entity(grid_pos=(3, 3), grid=small)
    entity.update_visibility()

    # Need a placeholder entity in large grid first
    placeholder = mcrfpy.Entity(grid_pos=(0, 0), grid=large)
    large.entities[0] = entity
    gs = entity.gridstate
    assert len(gs) == 400, f"Expected 400, got {len(gs)}"
    print("  PASS: setitem")

def test_slice_assign():
    """grid.entities[0:1] = [entity] resizes gridstate"""
    small = mcrfpy.Grid(grid_size=(10, 10))
    large = mcrfpy.Grid(grid_size=(35, 35))
    entity = mcrfpy.Entity(grid_pos=(3, 3), grid=small)
    entity.update_visibility()

    placeholder = mcrfpy.Entity(grid_pos=(0, 0), grid=large)
    large.entities[0:1] = [entity]
    gs = entity.gridstate
    assert len(gs) == 1225, f"Expected 1225, got {len(gs)}"
    print("  PASS: slice_assign")

def test_update_visibility_after_transfer():
    """update_visibility works correctly after all transfer methods"""
    grids = [mcrfpy.Grid(grid_size=(s, s)) for s in (5, 80, 3, 60, 10, 100)]
    entity = mcrfpy.Entity(grid_pos=(2, 2), grid=grids[0])

    for g in grids:
        entity.grid = g
        g.perspective = entity
        g.fov_radius = 4
        entity.update_visibility()
        gs = entity.gridstate
        expected = g.grid_w * g.grid_h
        assert len(gs) == expected, f"Expected {expected}, got {len(gs)}"
    print("  PASS: update_visibility_after_transfer")

def test_at_after_transfer():
    """entity.at(x, y) works correctly after grid transfer"""
    small = mcrfpy.Grid(grid_size=(10, 10))
    large = mcrfpy.Grid(grid_size=(50, 50))
    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=small)
    entity.update_visibility()

    entity.grid = large
    # Access a cell that would be out of bounds for the small grid
    state = entity.at(30, 30)
    assert state is not None
    print("  PASS: at_after_transfer")

def test_set_grid_none():
    """entity.grid = None properly removes entity (tests #274)"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)
    assert len(grid.entities) == 1
    entity.grid = None
    assert len(grid.entities) == 0
    print("  PASS: set_grid_none")

def test_stress():
    """Stress test: rapid grid transfers with heap churn"""
    entity = mcrfpy.Entity(grid_pos=(2, 2))
    for i in range(20):
        small_g = mcrfpy.Grid(grid_size=(5, 5))
        entity.grid = small_g
        small_g.perspective = entity
        entity.update_visibility()

        big_g = mcrfpy.Grid(grid_size=(80, 80))
        entity.grid = big_g
        big_g.perspective = entity
        entity.update_visibility()

        frames = [mcrfpy.Frame() for _ in range(10)]
        del frames
    print("  PASS: stress")

print("Testing gridstate resize across transfer methods...")
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
print("PASS: all gridstate resize tests passed")
sys.exit(0)
