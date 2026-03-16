"""Regression test for #253: GridPoint.entities uses spatial hash for O(1) lookup."""
import mcrfpy
import sys

def test_gridpoint_entities_basic():
    """Entities at known positions are returned correctly."""
    scene = mcrfpy.Scene("test253")
    mcrfpy.current_scene = scene

    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(20, 20), texture=tex, pos=(0, 0), size=(320, 320))
    scene.children.append(grid)

    # Place entities at specific cells
    e1 = mcrfpy.Entity((5, 5), grid=grid)
    e2 = mcrfpy.Entity((5, 5), grid=grid)
    e3 = mcrfpy.Entity((10, 10), grid=grid)

    # Query cell (5, 5) - should have 2 entities
    cell_5_5 = grid.at(5, 5)
    ents = cell_5_5.entities
    assert len(ents) == 2, f"Expected 2 entities at (5,5), got {len(ents)}"
    print("PASS: 2 entities at (5,5)")

    # Query cell (10, 10) - should have 1 entity
    cell_10_10 = grid.at(10, 10)
    ents = cell_10_10.entities
    assert len(ents) == 1, f"Expected 1 entity at (10,10), got {len(ents)}"
    print("PASS: 1 entity at (10,10)")

def test_gridpoint_entities_empty():
    """Empty cells return empty list."""
    scene = mcrfpy.Scene("test253b")
    mcrfpy.current_scene = scene

    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(20, 20), texture=tex, pos=(0, 0), size=(320, 320))
    scene.children.append(grid)

    # No entities placed - empty cell should return empty list
    cell = grid.at(0, 0)
    ents = cell.entities
    assert len(ents) == 0, f"Expected 0 entities, got {len(ents)}"
    print("PASS: empty cell returns empty list")

def test_gridpoint_entities_after_move():
    """Moving an entity updates spatial hash so GridPoint.entities reflects new position."""
    scene = mcrfpy.Scene("test253c")
    mcrfpy.current_scene = scene

    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(20, 20), texture=tex, pos=(0, 0), size=(320, 320))
    scene.children.append(grid)

    e = mcrfpy.Entity((3, 3), grid=grid)

    # Verify entity is at (3, 3)
    assert len(grid.at(3, 3).entities) == 1, "Entity should be at (3,3)"

    # Move entity to (7, 7)
    e.grid_pos = (7, 7)

    # Old cell should be empty, new cell should have the entity
    assert len(grid.at(3, 3).entities) == 0, "Old cell should be empty after move"
    assert len(grid.at(7, 7).entities) == 1, "New cell should have entity after move"
    print("PASS: entity move updates spatial hash correctly")

if __name__ == "__main__":
    test_gridpoint_entities_basic()
    test_gridpoint_entities_empty()
    test_gridpoint_entities_after_move()
    print("All #253 tests passed")
    sys.exit(0)
