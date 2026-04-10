"""Test multi-tile entity rendering and positioning (#236).

Verifies that entities can span multiple grid cells using tile_width
and tile_height properties, with correct frustum culling and spatial
hash queries.
"""
import mcrfpy
import sys

def test_default_tile_size():
    """New entities default to 1x1 tile size."""
    entity = mcrfpy.Entity()
    assert entity.tile_width == 1, f"Expected 1, got {entity.tile_width}"
    assert entity.tile_height == 1, f"Expected 1, got {entity.tile_height}"
    ts = entity.tile_size
    assert ts.x == 1.0 and ts.y == 1.0, f"tile_size wrong: ({ts.x}, {ts.y})"
    print("  PASS: default tile size")

def test_set_tile_size_individual():
    """tile_width and tile_height can be set individually."""
    entity = mcrfpy.Entity()
    entity.tile_width = 2
    entity.tile_height = 3
    assert entity.tile_width == 2, f"Expected 2, got {entity.tile_width}"
    assert entity.tile_height == 3, f"Expected 3, got {entity.tile_height}"
    print("  PASS: individual tile size setters")

def test_set_tile_size_tuple():
    """tile_size can be set as a tuple."""
    entity = mcrfpy.Entity()
    entity.tile_size = (4, 2)
    assert entity.tile_width == 4, f"Expected 4, got {entity.tile_width}"
    assert entity.tile_height == 2, f"Expected 2, got {entity.tile_height}"
    print("  PASS: tile_size tuple setter")

def test_tile_size_validation():
    """tile_width/height must be >= 1."""
    entity = mcrfpy.Entity()
    try:
        entity.tile_width = 0
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    try:
        entity.tile_height = -1
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    try:
        entity.tile_size = (0, 1)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    print("  PASS: tile size validation")

def test_multi_tile_in_grid():
    """Multi-tile entities work correctly in grids."""
    grid = mcrfpy.Grid(grid_size=(20, 20))
    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)
    entity.tile_width = 2
    entity.tile_height = 2

    assert entity.tile_width == 2
    assert entity.tile_height == 2
    assert entity.cell_pos.x == 5
    assert entity.cell_pos.y == 5
    print("  PASS: multi-tile entity in grid")

def test_spatial_hash_multi_tile():
    """Spatial hash queries find multi-tile entities at covered cells."""
    grid = mcrfpy.Grid(grid_size=(20, 20))
    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)
    entity.tile_width = 2
    entity.tile_height = 2

    at_origin = grid.at(5, 5).entities
    assert len(at_origin) >= 1, f"Entity not found at origin (5,5): {len(at_origin)}"

    at_right = grid.at(6, 5).entities
    assert len(at_right) >= 1, f"Entity not found at covered cell (6,5): {len(at_right)}"

    at_below = grid.at(5, 6).entities
    assert len(at_below) >= 1, f"Entity not found at covered cell (5,6): {len(at_below)}"

    at_corner = grid.at(6, 6).entities
    assert len(at_corner) >= 1, f"Entity not found at covered cell (6,6): {len(at_corner)}"

    at_outside = grid.at(7, 5).entities
    assert len(at_outside) == 0, f"Entity found outside footprint (7,5): {len(at_outside)}"

    print("  PASS: spatial hash multi-tile queries")

print("Testing #236: Multi-tile entities...")
test_default_tile_size()
test_set_tile_size_individual()
test_set_tile_size_tuple()
test_tile_size_validation()
test_multi_tile_in_grid()
test_spatial_hash_multi_tile()
print("All #236 tests passed.")
sys.exit(0)
