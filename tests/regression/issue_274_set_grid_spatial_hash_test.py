"""Regression test: set_grid() missing spatial hash insert (#274).

Bug: When transferring an entity to a new grid via entity.grid = new_grid,
the entity was removed from the old grid's spatial hash but NOT inserted
into the new grid's spatial hash. This made the entity invisible to
spatial queries on the new grid.

Fix: Added spatial_hash.insert() call after adding entity to new grid.
"""
import mcrfpy
import sys

def test_grid_transfer_spatial_hash():
    """Entity transferred between grids appears in new grid's spatial hash"""
    grid1 = mcrfpy.Grid(grid_size=(20, 20))
    grid2 = mcrfpy.Grid(grid_size=(20, 20))
    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=grid1)

    # Verify found on grid1
    found1 = grid1.entities_in_radius((5.0, 5.0), 1.0)
    assert len(found1) == 1, f"Expected 1 on grid1, found {len(found1)}"

    # Transfer to grid2
    entity.grid = grid2

    # Should NOT be on grid1 anymore
    found1_after = grid1.entities_in_radius((5.0, 5.0), 1.0)
    assert len(found1_after) == 0, f"Expected 0 on grid1 after transfer, found {len(found1_after)}"

    # Should be on grid2
    found2 = grid2.entities_in_radius((5.0, 5.0), 1.0)
    assert len(found2) == 1, f"Expected 1 on grid2 after transfer, found {len(found2)}"

    print("  PASS: grid_transfer_spatial_hash")

def test_set_grid_none_removes_from_hash():
    """Setting entity.grid = None removes from spatial hash"""
    grid = mcrfpy.Grid(grid_size=(20, 20))
    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)

    found = grid.entities_in_radius((5.0, 5.0), 1.0)
    assert len(found) == 1

    entity.grid = None

    found = grid.entities_in_radius((5.0, 5.0), 1.0)
    assert len(found) == 0, f"Expected 0 after grid=None, found {len(found)}"
    print("  PASS: set_grid_none_removes_from_hash")

def test_multiple_transfers():
    """Entity survives multiple grid transfers with correct spatial hash"""
    grids = [mcrfpy.Grid(grid_size=(20, 20)) for _ in range(4)]
    entity = mcrfpy.Entity(grid_pos=(3, 3), grid=grids[0])

    for i in range(1, 4):
        entity.grid = grids[i]

        # Should be on new grid
        found = grids[i].entities_in_radius((3.0, 3.0), 1.0)
        assert len(found) == 1, f"Expected 1 on grid[{i}], found {len(found)}"

        # Should NOT be on previous grid
        found_prev = grids[i-1].entities_in_radius((3.0, 3.0), 1.0)
        assert len(found_prev) == 0, f"Expected 0 on grid[{i-1}], found {len(found_prev)}"

    print("  PASS: multiple_transfers")


print("Testing set_grid() spatial hash operations (#274)...")
test_grid_transfer_spatial_hash()
test_set_grid_none_removes_from_hash()
test_multiple_transfers()
print("PASS: all set_grid spatial hash tests passed")
sys.exit(0)
