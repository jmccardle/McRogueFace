"""Regression test for #292: Deduplicate FOV computation via dirty flag."""
import mcrfpy
import sys

def test_fov_basic_correctness():
    """FOV computation still works correctly with dirty flag."""
    scene = mcrfpy.Scene("test292")
    mcrfpy.current_scene = scene

    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(20, 20), texture=tex, pos=(0, 0), size=(320, 320))
    scene.children.append(grid)

    # Make all cells transparent and walkable
    for y in range(20):
        for x in range(20):
            pt = grid.at(x, y)
            pt.walkable = True
            pt.transparent = True

    # Compute FOV from center
    grid.compute_fov((10, 10), radius=5)

    # Center should be visible
    assert grid.is_in_fov((10, 10)), "Center should be in FOV"
    # Nearby cell should be visible
    assert grid.is_in_fov((10, 11)), "Adjacent cell should be in FOV"
    # Far cell should NOT be visible
    assert not grid.is_in_fov((0, 0)), "Far cell should not be in FOV"
    print("PASS: FOV basic correctness")

def test_fov_duplicate_call():
    """Calling computeFOV twice with same params should still give correct results."""
    scene = mcrfpy.Scene("test292b")
    mcrfpy.current_scene = scene

    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(20, 20), texture=tex, pos=(0, 0), size=(320, 320))
    scene.children.append(grid)

    for y in range(20):
        for x in range(20):
            pt = grid.at(x, y)
            pt.walkable = True
            pt.transparent = True

    # Compute FOV twice with same params (second should be skipped internally)
    grid.compute_fov((10, 10), radius=5)
    result1 = grid.is_in_fov((10, 11))

    grid.compute_fov((10, 10), radius=5)
    result2 = grid.is_in_fov((10, 11))

    assert result1 == result2, "Duplicate FOV call should give same result"
    print("PASS: Duplicate FOV call gives same result")

def test_fov_updates_after_map_change():
    """FOV should recompute after a cell's walkable/transparent changes."""
    scene = mcrfpy.Scene("test292c")
    mcrfpy.current_scene = scene

    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(20, 20), texture=tex, pos=(0, 0), size=(320, 320))
    scene.children.append(grid)

    for y in range(20):
        for x in range(20):
            pt = grid.at(x, y)
            pt.walkable = True
            pt.transparent = True

    # Compute FOV - cell (10, 12) should be visible
    grid.compute_fov((10, 10), radius=5)
    assert grid.is_in_fov((10, 12)), "Cell should be visible initially"

    # Block line of sight by making (10, 11) opaque
    grid.at(10, 11).transparent = False

    # Recompute FOV with same params - dirty flag should force recomputation
    grid.compute_fov((10, 10), radius=5)
    assert not grid.is_in_fov((10, 12)), "Cell behind wall should not be visible after map change"
    print("PASS: FOV updates correctly after map change")

def test_fov_different_params_recompute():
    """FOV should recompute when params change even if map hasn't."""
    scene = mcrfpy.Scene("test292d")
    mcrfpy.current_scene = scene

    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(20, 20), texture=tex, pos=(0, 0), size=(320, 320))
    scene.children.append(grid)

    for y in range(20):
        for x in range(20):
            pt = grid.at(x, y)
            pt.walkable = True
            pt.transparent = True

    # Compute from (10, 10) with radius 3
    grid.compute_fov((10, 10), radius=3)
    visible_3 = grid.is_in_fov((10, 14))

    # Compute from (10, 10) with radius 5 - different params should recompute
    grid.compute_fov((10, 10), radius=5)
    visible_5 = grid.is_in_fov((10, 14))

    # Radius 3 shouldn't see (10, 14), but radius 5 should
    assert not visible_3, "(10,14) should not be visible with radius 3"
    assert visible_5, "(10,14) should be visible with radius 5"
    print("PASS: Different FOV params force recomputation")

if __name__ == "__main__":
    test_fov_basic_correctness()
    test_fov_duplicate_call()
    test_fov_updates_after_map_change()
    test_fov_different_params_recompute()
    print("All #292 tests passed")
    sys.exit(0)
