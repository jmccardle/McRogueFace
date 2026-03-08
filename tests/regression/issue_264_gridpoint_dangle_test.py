"""Regression test: GridPoint/GridPointState coordinate-based access (#264, #265).

Bug: PyUIGridPointObject stored a raw UIGridPoint* pointer into the grid's
points vector. PyUIGridPointStateObject stored a raw UIGridPointState*
into the entity's gridstate vector. If either vector was resized, these
pointers would dangle.

Fix: Remove raw pointers. Store (grid, x, y) coordinates and compute
the data address on each property access.
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

def test_gridpointstate_access():
    """entity.at(x,y) returns working GridPointState via coordinate lookup"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)
    entity.update_visibility()

    state = entity.at(5, 5)
    # Should be accessible
    assert state is not None
    # visible/discovered should be boolean
    assert isinstance(state.visible, bool)
    assert isinstance(state.discovered, bool)
    print("  PASS: gridpointstate_access")

def test_gridpointstate_after_grid_transfer():
    """GridPointState access works after entity transfers to new grid"""
    small = mcrfpy.Grid(grid_size=(10, 10))
    large = mcrfpy.Grid(grid_size=(20, 20))
    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=small)
    entity.update_visibility()

    # Get state on small grid
    state1 = entity.at(3, 3)
    assert state1 is not None

    # Transfer to large grid (gridstate resizes)
    entity.grid = large
    entity.update_visibility()

    # Access a cell that didn't exist on small grid
    state2 = entity.at(15, 15)
    assert state2 is not None
    print("  PASS: gridpointstate_after_grid_transfer")

def test_gridpoint_subscript():
    """grid[x, y] returns working GridPoint"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    gp = grid[3, 4]
    gp.walkable = True
    assert grid.at(3, 4).walkable == True
    print("  PASS: gridpoint_subscript")

def test_gridstate_list():
    """entity.gridstate returns list with visible/discovered attrs"""
    grid = mcrfpy.Grid(grid_size=(5, 5))
    entity = mcrfpy.Entity(grid_pos=(2, 2), grid=grid)
    entity.update_visibility()

    gs = entity.gridstate
    assert len(gs) == 25, f"Expected 25, got {len(gs)}"
    # Each element should have visible and discovered
    for state in gs:
        assert hasattr(state, 'visible')
        assert hasattr(state, 'discovered')
    print("  PASS: gridstate_list")

print("Testing GridPoint/GridPointState coordinate-based access...")
test_gridpoint_access()
test_gridpoint_grid_pos()
test_gridpointstate_access()
test_gridpointstate_after_grid_transfer()
test_gridpoint_subscript()
test_gridstate_list()
print("PASS: all GridPoint/GridPointState tests passed")
sys.exit(0)
