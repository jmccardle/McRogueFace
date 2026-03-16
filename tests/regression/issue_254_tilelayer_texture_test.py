"""Regression test for #254: TileLayer inherits Grid texture when none set."""
import mcrfpy
import sys

def test_tilelayer_texture_inheritance():
    """TileLayer without texture should inherit grid's texture on attachment."""
    scene = mcrfpy.Scene("test254")
    mcrfpy.current_scene = scene

    # Create grid with texture
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(10, 10), texture=tex, pos=(0, 0), size=(160, 160))
    scene.children.append(grid)

    # Create TileLayer WITHOUT texture
    layer_no_tex = mcrfpy.TileLayer(name="terrain", z_index=0)
    grid.add_layer(layer_no_tex)

    # Verify it inherited the grid's texture
    assert layer_no_tex.texture is not None, "TileLayer should inherit grid texture"
    print("PASS: TileLayer without texture inherits grid texture")

    # Create TileLayer WITH explicit texture
    tex2 = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    layer_with_tex = mcrfpy.TileLayer(name="overlay", z_index=1, texture=tex2)
    grid.add_layer(layer_with_tex)

    # Verify it kept its own texture
    assert layer_with_tex.texture is not None, "TileLayer with texture should keep it"
    print("PASS: TileLayer with explicit texture keeps its own")

def test_tilelayer_texture_via_constructor():
    """TileLayer passed in Grid constructor should also inherit texture."""
    scene = mcrfpy.Scene("test254b")
    mcrfpy.current_scene = scene

    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    layer = mcrfpy.TileLayer(name="base", z_index=0)

    grid = mcrfpy.Grid(grid_size=(10, 10), texture=tex, pos=(0, 0), size=(160, 160),
                        layers=[layer])
    scene.children.append(grid)

    assert layer.texture is not None, "TileLayer in constructor should inherit grid texture"
    print("PASS: TileLayer in constructor inherits grid texture")

def test_tilelayer_texture_via_grid_property():
    """TileLayer attached via layer.grid = grid should inherit texture."""
    scene = mcrfpy.Scene("test254c")
    mcrfpy.current_scene = scene

    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(10, 10), texture=tex, pos=(0, 0), size=(160, 160))
    scene.children.append(grid)

    layer = mcrfpy.TileLayer(name="via_prop", z_index=0)
    layer.grid = grid

    assert layer.texture is not None, "TileLayer attached via .grid should inherit texture"
    print("PASS: TileLayer via .grid property inherits grid texture")

if __name__ == "__main__":
    test_tilelayer_texture_inheritance()
    test_tilelayer_texture_via_constructor()
    test_tilelayer_texture_via_grid_property()
    print("All #254 tests passed")
    sys.exit(0)
