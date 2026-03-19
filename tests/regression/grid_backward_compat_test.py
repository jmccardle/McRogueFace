"""Regression test for Grid backward compatibility with GridView shim (#252)."""
import mcrfpy
import sys

def test_grid_creates_view():
    """Grid auto-creates a GridView accessible via .view property."""
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(10, 10), texture=tex, pos=(0, 0), size=(160, 160))
    assert grid.view is not None, "Grid should auto-create a view"
    assert isinstance(grid.view, mcrfpy.GridView)
    print("PASS: Grid auto-creates view")

def test_view_shares_grid_data():
    """GridView created by shim shares the same grid data."""
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(10, 10), texture=tex, pos=(0, 0), size=(160, 160))
    view = grid.view

    # View's grid should be the same Grid
    assert view.grid is grid, "view.grid should be the same Grid"
    assert view.grid.grid_w == 10
    print("PASS: view shares grid data")

def test_rendering_property_sync():
    """Setting rendering properties on Grid syncs to the view."""
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(10, 10), texture=tex, pos=(0, 0), size=(160, 160))
    view = grid.view

    grid.zoom = 3.0
    assert abs(view.zoom - 3.0) < 0.01, f"View zoom should sync: {view.zoom}"

    grid.center_x = 200.0
    assert abs(view.center.x - 200.0) < 0.01, f"View center_x should sync: {view.center.x}"

    grid.center_y = 150.0
    assert abs(view.center.y - 150.0) < 0.01, f"View center_y should sync: {view.center.y}"

    grid.camera_rotation = 45.0
    # camera_rotation syncs through set_float_member
    print("PASS: rendering properties sync to view")

def test_grid_still_works_in_scene():
    """Grid can still be appended to scenes and works as before."""
    scene = mcrfpy.Scene("test_compat")
    mcrfpy.current_scene = scene

    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(10, 10), texture=tex, pos=(0, 0), size=(160, 160))
    scene.children.append(grid)

    # Grid is in the scene as itself (not substituted)
    assert len(scene.children) == 1
    retrieved = scene.children[0]
    assert type(retrieved).__name__ == "Grid", f"Expected Grid, got {type(retrieved).__name__}"
    print("PASS: Grid works in scene as before")

def test_grid_subclass_preserved():
    """Grid subclasses maintain identity when appended to scene."""
    scene = mcrfpy.Scene("test_subclass_compat")
    mcrfpy.current_scene = scene

    class MyGrid(mcrfpy.Grid):
        pass

    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = MyGrid(grid_size=(5, 5), texture=tex, pos=(0, 0), size=(80, 80))
    scene.children.append(grid)

    retrieved = scene.children[0]
    assert isinstance(retrieved, MyGrid), f"Expected MyGrid, got {type(retrieved).__name__}"
    print("PASS: Grid subclass identity preserved")

def test_entity_operations_unaffected():
    """Entity creation and manipulation still works normally."""
    scene = mcrfpy.Scene("test_entity_compat")
    mcrfpy.current_scene = scene

    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(20, 20), texture=tex, pos=(0, 0), size=(320, 320))
    scene.children.append(grid)

    for y in range(20):
        for x in range(20):
            grid.at(x, y).walkable = True
            grid.at(x, y).transparent = True

    e = mcrfpy.Entity((5, 5), grid=grid)
    assert len(grid.entities) == 1
    assert e.cell_x == 5
    assert e.cell_y == 5
    assert len(grid.at(5, 5).entities) == 1
    print("PASS: entity operations unaffected")

def test_gridview_independent_rendering():
    """A GridView can have different rendering settings from the Grid."""
    scene = mcrfpy.Scene("test_independent")
    mcrfpy.current_scene = scene

    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(20, 20), texture=tex, pos=(0, 0), size=(320, 320))

    # Create an explicit GridView with different settings
    view2 = mcrfpy.GridView(grid=grid, pos=(350, 0), size=(160, 160), zoom=0.5)
    scene.children.append(grid)
    scene.children.append(view2)

    # Grid and view2 should have different zoom
    assert abs(grid.zoom - 1.0) < 0.01
    assert abs(view2.zoom - 0.5) < 0.01

    # Changing grid zoom doesn't affect explicit GridView
    grid.zoom = 2.0
    assert abs(view2.zoom - 0.5) < 0.01, "Explicit GridView should keep its own zoom"
    print("PASS: GridView independent rendering")

if __name__ == "__main__":
    test_grid_creates_view()
    test_view_shares_grid_data()
    test_rendering_property_sync()
    test_grid_still_works_in_scene()
    test_grid_subclass_preserved()
    test_entity_operations_unaffected()
    test_gridview_independent_rendering()
    print("All backward compatibility tests passed")
    sys.exit(0)
