"""Unit test for GridView (#252): rendering view for Grid data."""
import mcrfpy
import sys

def test_gridview_creation():
    """GridView can be created with a Grid reference."""
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(10, 10), texture=tex, pos=(0, 0), size=(160, 160))
    view = mcrfpy.GridView(grid=grid, pos=(200, 0), size=(160, 160))
    assert view.zoom == 1.0
    print("PASS: GridView creation")

def test_gridview_properties():
    """GridView properties can be read and set."""
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(10, 10), texture=tex, pos=(0, 0), size=(160, 160))
    view = mcrfpy.GridView(grid=grid, pos=(0, 0), size=(200, 200))

    view.zoom = 2.0
    assert abs(view.zoom - 2.0) < 0.01

    view.center = (50, 50)
    c = view.center
    assert abs(c.x - 50) < 0.01 and abs(c.y - 50) < 0.01

    view.fill_color = mcrfpy.Color(255, 0, 0)
    assert view.fill_color.r == 255
    print("PASS: GridView properties")

def test_gridview_in_scene():
    """GridView can be added to a scene's children."""
    scene = mcrfpy.Scene("test_gv_scene")
    mcrfpy.current_scene = scene

    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(10, 10), texture=tex, pos=(0, 0), size=(160, 160))
    view = mcrfpy.GridView(grid=grid, pos=(200, 0), size=(160, 160))

    scene.children.append(grid)
    scene.children.append(view)
    assert len(scene.children) == 2
    print("PASS: GridView in scene")

def test_gridview_multi_view():
    """Multiple GridViews can reference the same Grid."""
    scene = mcrfpy.Scene("test_gv_multi")
    mcrfpy.current_scene = scene

    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(20, 20), texture=tex, pos=(0, 0), size=(320, 320))
    scene.children.append(grid)

    view1 = mcrfpy.GridView(grid=grid, pos=(350, 0), size=(160, 160), zoom=0.5)
    view2 = mcrfpy.GridView(grid=grid, pos=(350, 170), size=(160, 160), zoom=2.0)

    scene.children.append(view1)
    scene.children.append(view2)

    # Both views exist with different zoom
    assert abs(view1.zoom - 0.5) < 0.01
    assert abs(view2.zoom - 2.0) < 0.01
    assert len(scene.children) == 3
    print("PASS: Multiple GridViews of same Grid")

def test_gridview_repr():
    """GridView has useful repr."""
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(15, 10), texture=tex, pos=(0, 0), size=(240, 160))
    view = mcrfpy.GridView(grid=grid, pos=(0, 0), size=(240, 160))
    r = repr(view)
    assert "GridView" in r
    assert "15x10" in r
    print("PASS: GridView repr")

def test_gridview_no_grid():
    """GridView without a grid doesn't crash."""
    view = mcrfpy.GridView()
    assert view.grid is None
    r = repr(view)
    assert "None" in r
    print("PASS: GridView without grid")

if __name__ == "__main__":
    test_gridview_creation()
    test_gridview_properties()
    test_gridview_in_scene()
    test_gridview_multi_view()
    test_gridview_repr()
    test_gridview_no_grid()
    print("All GridView tests passed")
    sys.exit(0)
