"""Regression test for Grid/GridView/GridData compatibility (#252, updated for #313/#361).

The old GridView "shim" model (Grid owns data, .view property auto-creates a separate
GridView object) is gone. Current contract: mcrfpy.Grid IS mcrfpy.GridView (same type);
the view owns rendering state (zoom/center/camera), and the shared map lives in
.grid_data (a mcrfpy.GridData -- cells, entities, layers; not a drawable).

The intent of each test below is preserved; the assertions were retargeted at the
current contract.
"""
import mcrfpy
import sys

def test_grid_creates_grid_data():
    """Grid auto-creates its GridData, accessible via .grid_data."""
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(10, 10), texture=tex, pos=(0, 0), size=(160, 160))
    assert grid.grid_data is not None, "Grid should auto-create its grid data"
    assert isinstance(grid.grid_data, mcrfpy.GridData)
    # Grid and GridView are the same type now (alias), not shim + shimmed object.
    assert mcrfpy.Grid is mcrfpy.GridView, "Grid should be an alias of GridView"
    assert isinstance(grid, mcrfpy.GridView)
    print("PASS: Grid auto-creates grid data")

def test_view_shares_grid_data():
    """A GridView constructed over an existing Grid shares the same GridData."""
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(10, 10), texture=tex, pos=(0, 0), size=(160, 160))
    view = mcrfpy.GridView(grid=grid, pos=(0, 0), size=(160, 160))

    # The view must share -- not copy -- the source grid's data.
    assert view.grid_data is grid.grid_data, "view should share the Grid's GridData"
    assert view.grid_data.grid_w == 10
    # Passing the GridData itself is equivalent.
    view2 = mcrfpy.GridView(grid=grid.grid_data, pos=(0, 0), size=(160, 160))
    assert view2.grid_data is grid.grid_data, "GridView(grid=GridData) should share it"
    print("PASS: view shares grid data")

def test_rendering_properties():
    """Rendering properties live on the view (Grid) itself and round-trip."""
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(10, 10), texture=tex, pos=(0, 0), size=(160, 160))

    grid.zoom = 3.0
    assert abs(grid.zoom - 3.0) < 0.01, f"zoom should round-trip: {grid.zoom}"

    grid.center_x = 200.0
    assert abs(grid.center.x - 200.0) < 0.01, f"center.x should track center_x: {grid.center.x}"

    grid.center_y = 150.0
    assert abs(grid.center.y - 150.0) < 0.01, f"center.y should track center_y: {grid.center.y}"

    grid.camera_rotation = 45.0
    assert abs(grid.camera_rotation - 45.0) < 0.01, f"camera_rotation should round-trip: {grid.camera_rotation}"

    # Rendering state is view-only; it must not have leaked onto the shared map.
    assert not hasattr(grid.grid_data, "zoom"), "GridData must not carry rendering state"
    print("PASS: rendering properties live on the view")

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
    assert retrieved is grid, "scene.children should return the same object (#369)"
    assert type(retrieved).__name__ == "GridView", f"Expected GridView, got {type(retrieved).__name__}"
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

    data = grid.grid_data
    for y in range(20):
        for x in range(20):
            data.at(x, y).walkable = True
            data.at(x, y).transparent = True

    e = mcrfpy.Entity((5, 5), grid=grid)
    assert len(data.entities) == 1
    assert e.cell_x == 5
    assert e.cell_y == 5
    assert len(data.at(5, 5).entities) == 1
    # Current contract (#313/#361): entity.grid is the shared GridData, not the view.
    assert e.grid is data, "entity.grid should be the GridData it lives in"
    print("PASS: entity operations unaffected")

def test_gridview_independent_rendering():
    """A second GridView over the same data has independent rendering settings."""
    scene = mcrfpy.Scene("test_independent")
    mcrfpy.current_scene = scene

    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(20, 20), texture=tex, pos=(0, 0), size=(320, 320))

    # Create an explicit second view over the same grid data, with different settings
    view2 = mcrfpy.GridView(grid=grid, pos=(350, 0), size=(160, 160), zoom=0.5)
    scene.children.append(grid)
    scene.children.append(view2)

    assert view2.grid_data is grid.grid_data, "both views should share one GridData"

    # Grid and view2 should have different zoom
    assert abs(grid.zoom - 1.0) < 0.01
    assert abs(view2.zoom - 0.5) < 0.01

    # Changing grid zoom doesn't affect the second view
    grid.zoom = 2.0
    assert abs(view2.zoom - 0.5) < 0.01, "Second GridView should keep its own zoom"
    assert abs(grid.zoom - 2.0) < 0.01
    print("PASS: GridView independent rendering")

if __name__ == "__main__":
    tests = [
        test_grid_creates_grid_data,
        test_view_shares_grid_data,
        test_rendering_properties,
        test_grid_still_works_in_scene,
        test_grid_subclass_preserved,
        test_entity_operations_unaffected,
        test_gridview_independent_rendering,
    ]
    failures = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failures += 1
            print(f"FAIL: {t.__name__}: {e}")
    if failures:
        print(f"FAILED: {failures} of {len(tests)} tests failed")
        sys.exit(1)
    print("All backward compatibility tests passed")
    print("PASS")
    sys.exit(0)
