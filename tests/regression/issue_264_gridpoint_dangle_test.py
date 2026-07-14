"""Regression test: GridPoint/GridPointState coordinate-based access (#264, #265).

Bug: PyUIGridPointObject stored a raw UIGridPoint* pointer into the grid's
points vector. PyUIGridPointStateObject stored a raw UIGridPointState*
into the entity's gridstate vector. If either vector was resized, these
pointers would dangle.

Fix: Remove raw pointers. Store (grid, x, y) coordinates and compute
the data address on each property access.

API update (current contract): the per-entity GridPointState vector is gone.
Its successor is entity.perspective_map, a DiscreteMap of mcrfpy.Perspective
(UNKNOWN / DISCOVERED / VISIBLE), and entity.at(x, y) now returns the grid's
GridPoint only when that cell is VISIBLE to the entity (None otherwise).
The dangle scenario is preserved: the perspective map is reallocated when the
entity transfers to a differently-sized grid, and previously-obtained
GridPoint / DiscreteMap wrappers must remain safe to use afterward.
"""
import mcrfpy
import sys

def test_gridpoint_access():
    """grid.at(x,y) returns working GridPoint via coordinate lookup"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    gp = grid.at(3, 4)
    assert gp.walkable == False  # default
    gp.walkable = True
    assert gp.walkable == True
    gp.transparent = True
    assert gp.transparent == True
    print("  PASS: gridpoint_access")

def test_gridpoint_grid_pos():
    """GridPoint.grid_pos returns correct coordinates"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    gp = grid.at(7, 3)
    pos = gp.grid_pos
    assert pos == (7, 3), f"Expected (7, 3), got {pos}"
    print("  PASS: gridpoint_grid_pos")

def test_perspective_map_access():
    """entity.at(x,y) / entity.perspective_map use coordinate lookup"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)
    entity.update_visibility()

    pm = entity.perspective_map
    assert pm.size == (10, 10), f"Expected (10, 10), got {pm.size}"

    # The entity's own cell is VISIBLE; entity.at() hands back the GridPoint.
    assert pm.get((5, 5)) == mcrfpy.Perspective.VISIBLE
    gp = entity.at(5, 5)
    assert gp is not None
    assert gp.grid_pos == (5, 5), f"Expected (5, 5), got {gp.grid_pos}"

    # A cell outside the entity's FOV is UNKNOWN, and at() gates on visibility.
    assert pm.get((9, 0)) == mcrfpy.Perspective.UNKNOWN
    assert entity.at(9, 0) is None
    print("  PASS: perspective_map_access")

def test_perspective_map_after_grid_transfer():
    """Perspective/GridPoint access works after entity transfers to new grid"""
    small = mcrfpy.Grid(grid_size=(10, 10))
    large = mcrfpy.Grid(grid_size=(20, 20))
    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=small)
    entity.update_visibility()

    # Wrappers obtained while on the small grid
    gp_small = small.grid_data.at(3, 3)
    pm_small = entity.perspective_map
    assert pm_small.size == (10, 10)

    # Transfer to large grid: the entity's perspective map is reallocated.
    entity.grid = large
    entity.update_visibility()

    # entity.grid is the shared GridData, not the view (#313/#361)
    assert entity.grid is large.grid_data

    # The new map covers the larger grid, and coordinate lookup reaches cells
    # that did not exist on the small grid.
    pm_large = entity.perspective_map
    assert pm_large.size == (20, 20), f"Expected (20, 20), got {pm_large.size}"
    assert pm_large.get((15, 15)) == mcrfpy.Perspective.UNKNOWN
    assert pm_large.get((5, 5)) == mcrfpy.Perspective.VISIBLE
    assert entity.at(5, 5) is not None

    # The pre-transfer wrappers must not dangle: they still describe the small
    # grid / old map and remain safe to read and write.
    assert pm_small.size == (10, 10)
    assert pm_small.get((3, 3)) in (mcrfpy.Perspective.UNKNOWN,
                                    mcrfpy.Perspective.DISCOVERED,
                                    mcrfpy.Perspective.VISIBLE)
    assert gp_small.grid_pos == (3, 3)
    gp_small.walkable = True
    assert small.grid_data.at(3, 3).walkable == True
    print("  PASS: perspective_map_after_grid_transfer")

def test_gridpoint_subscript():
    """grid[x, y] returns working GridPoint"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    gp = grid[3, 4]
    gp.walkable = True
    assert grid.at(3, 4).walkable == True
    print("  PASS: gridpoint_subscript")

def test_perspective_map_all_cells():
    """entity.perspective_map covers every cell of the grid"""
    grid = mcrfpy.Grid(grid_size=(5, 5))
    entity = mcrfpy.Entity(grid_pos=(2, 2), grid=grid)
    entity.update_visibility()

    pm = entity.perspective_map
    assert pm.size == (5, 5), f"Expected (5, 5), got {pm.size}"

    # Every one of the 25 cells is addressable and holds a Perspective member
    valid = (mcrfpy.Perspective.UNKNOWN, mcrfpy.Perspective.DISCOVERED,
             mcrfpy.Perspective.VISIBLE)
    count = 0
    for y in range(5):
        for x in range(5):
            state = pm.get((x, y))
            assert state in valid, f"({x}, {y}) has bad state {state}"
            count += 1
    assert count == 25, f"Expected 25, got {count}"
    print("  PASS: perspective_map_all_cells")

print("Testing GridPoint/perspective_map coordinate-based access...")
test_gridpoint_access()
test_gridpoint_grid_pos()
test_perspective_map_access()
test_perspective_map_after_grid_transfer()
test_gridpoint_subscript()
test_perspective_map_all_cells()
print("PASS: all GridPoint/perspective_map tests passed")
sys.exit(0)
