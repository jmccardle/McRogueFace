"""Regression test for #295: Entity cell_pos integer logical position."""
import mcrfpy
import sys

def test_cell_pos_init():
    """cell_pos initialized from grid_pos on construction."""
    e = mcrfpy.Entity((5, 7))
    assert e.cell_x == 5, f"cell_x should be 5, got {e.cell_x}"
    assert e.cell_y == 7, f"cell_y should be 7, got {e.cell_y}"
    print("PASS: cell_pos initialized from constructor")

def test_cell_pos_grid_pos_alias():
    """grid_pos is an alias for cell_pos."""
    e = mcrfpy.Entity((3, 4))
    # grid_pos should match cell_pos
    assert e.grid_pos.x == e.cell_pos.x
    assert e.grid_pos.y == e.cell_pos.y

    # Setting grid_pos should update cell_pos
    e.grid_pos = (10, 20)
    assert e.cell_x == 10
    assert e.cell_y == 20
    print("PASS: grid_pos aliases cell_pos")

def test_cell_pos_independent_from_draw_pos():
    """cell_pos does not change when draw_pos (float position) changes."""
    e = mcrfpy.Entity((5, 5))

    # Change draw_pos (float position for rendering)
    e.draw_pos = (5.5, 5.5)

    # cell_pos should be unchanged
    assert e.cell_x == 5, f"cell_x should still be 5 after draw_pos change, got {e.cell_x}"
    assert e.cell_y == 5, f"cell_y should still be 5 after draw_pos change, got {e.cell_y}"
    print("PASS: cell_pos independent from draw_pos")

def test_cell_pos_spatial_hash():
    """GridPoint.entities uses cell_pos for matching."""
    scene = mcrfpy.Scene("test295")
    mcrfpy.current_scene = scene
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(20, 20), texture=tex, pos=(0, 0), size=(320, 320))
    scene.children.append(grid)

    e = mcrfpy.Entity((5, 5), grid=grid)

    # Entity should appear at cell (5, 5)
    assert len(grid.at(5, 5).entities) == 1

    # Move cell_pos to (10, 10)
    e.cell_pos = (10, 10)
    assert len(grid.at(5, 5).entities) == 0, "Old cell should be empty"
    assert len(grid.at(10, 10).entities) == 1, "New cell should have entity"
    print("PASS: spatial hash uses cell_pos")

def test_cell_pos_member_access():
    """cell_x and cell_y read/write correctly."""
    e = mcrfpy.Entity((3, 7))
    assert e.cell_x == 3
    assert e.cell_y == 7

    e.cell_x = 15
    assert e.cell_x == 15
    assert e.cell_y == 7  # y unchanged

    e.cell_y = 20
    assert e.cell_x == 15  # x unchanged
    assert e.cell_y == 20
    print("PASS: cell_x/cell_y member access")

if __name__ == "__main__":
    test_cell_pos_init()
    test_cell_pos_grid_pos_alias()
    test_cell_pos_independent_from_draw_pos()
    test_cell_pos_spatial_hash()
    test_cell_pos_member_access()
    print("All #295 tests passed")
    sys.exit(0)
