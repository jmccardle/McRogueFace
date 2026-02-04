"""
Unit tests for the modernized Grid Layer API.

Tests:
1. Layer name in constructor
2. Lazy allocation (size (0,0) auto-resizes)
3. layer.grid property (getter and setter)
4. grid.layer(name) lookup
5. grid.layers returns tuple
6. add_layer accepts layer objects
7. remove_layer by name and by layer object
8. Name collision handling
"""

import mcrfpy
import sys

def test_layer_name_in_constructor():
    """Test that layers can be created with names."""
    print("Test 1: Layer name in constructor...")

    color_layer = mcrfpy.ColorLayer(name='fog', z_index=-1)
    assert color_layer.name == 'fog', f"Expected 'fog', got {color_layer.name}"

    tile_layer = mcrfpy.TileLayer(name='terrain', z_index=-2)
    assert tile_layer.name == 'terrain', f"Expected 'terrain', got {tile_layer.name}"

    # Name should appear in repr
    assert 'fog' in repr(color_layer), f"Name not in repr: {repr(color_layer)}"
    assert 'terrain' in repr(tile_layer), f"Name not in repr: {repr(tile_layer)}"

    # Layers without name should work too
    unnamed = mcrfpy.ColorLayer(z_index=0)
    assert unnamed.name == '', f"Expected empty string, got {unnamed.name}"

    print("  PASS")

def test_lazy_allocation():
    """Test that layers with size (0,0) auto-resize when attached to grid."""
    print("Test 2: Lazy allocation...")

    layer = mcrfpy.ColorLayer(name='test')
    assert layer.grid_size == (0, 0), f"Expected (0,0), got {layer.grid_size}"

    grid = mcrfpy.Grid(grid_size=(10, 8), layers=[layer])
    assert layer.grid_size == (10, 8), f"Expected (10,8), got {layer.grid_size}"

    print("  PASS")

def test_layer_grid_property():
    """Test that layer.grid property works for getting and setting."""
    print("Test 3: layer.grid property...")

    layer = mcrfpy.ColorLayer(name='overlay', z_index=0)
    assert layer.grid is None, f"Expected None, got {layer.grid}"

    grid = mcrfpy.Grid(grid_size=(5, 5), layers=[])
    layer.grid = grid

    assert layer.grid is not None, "layer.grid should not be None after assignment"
    assert len(grid.layers) == 1, f"Expected 1 layer, got {len(grid.layers)}"
    assert layer.grid_size == (5, 5), f"Expected (5,5), got {layer.grid_size}"

    # Unlink by setting to None
    layer.grid = None
    assert layer.grid is None, "layer.grid should be None after unsetting"
    assert len(grid.layers) == 0, f"Expected 0 layers, got {len(grid.layers)}"

    print("  PASS")

def test_grid_layer_name_lookup():
    """Test that grid.layer(name) finds layers by name."""
    print("Test 4: grid.layer(name) lookup...")

    fog = mcrfpy.ColorLayer(name='fog', z_index=-1)
    terrain = mcrfpy.TileLayer(name='terrain', z_index=-2)
    grid = mcrfpy.Grid(grid_size=(5, 5), layers=[fog, terrain])

    retrieved_fog = grid.layer('fog')
    assert retrieved_fog is not None, "Should find 'fog' layer"
    assert retrieved_fog.name == 'fog', f"Expected 'fog', got {retrieved_fog.name}"

    retrieved_terrain = grid.layer('terrain')
    assert retrieved_terrain is not None, "Should find 'terrain' layer"
    assert retrieved_terrain.name == 'terrain', f"Expected 'terrain', got {retrieved_terrain.name}"

    # Non-existent name should return None
    result = grid.layer('nonexistent')
    assert result is None, f"Expected None for nonexistent, got {result}"

    print("  PASS")

def test_layers_returns_tuple():
    """Test that grid.layers returns a tuple (immutable)."""
    print("Test 5: grid.layers returns tuple...")

    fog = mcrfpy.ColorLayer(name='fog')
    grid = mcrfpy.Grid(grid_size=(5, 5), layers=[fog])

    layers = grid.layers
    assert isinstance(layers, tuple), f"Expected tuple, got {type(layers)}"

    print("  PASS")

def test_add_layer_accepts_objects():
    """Test that add_layer accepts ColorLayer and TileLayer objects."""
    print("Test 6: add_layer accepts objects...")

    grid = mcrfpy.Grid(grid_size=(5, 5), layers=[])
    assert len(grid.layers) == 0, f"Expected 0 layers, got {len(grid.layers)}"

    new_layer = mcrfpy.TileLayer(name='overlay', z_index=1)
    returned = grid.add_layer(new_layer)

    assert len(grid.layers) == 1, f"Expected 1 layer, got {len(grid.layers)}"
    assert new_layer.grid is not None, "Layer should be attached to grid"
    assert returned is new_layer, "Should return the same layer object"

    # Add another layer
    color = mcrfpy.ColorLayer(name='highlights', z_index=2)
    grid.add_layer(color)
    assert len(grid.layers) == 2, f"Expected 2 layers, got {len(grid.layers)}"

    print("  PASS")

def test_remove_layer_by_name():
    """Test that remove_layer accepts layer name as string."""
    print("Test 7a: remove_layer by name...")

    fog = mcrfpy.ColorLayer(name='fog')
    terrain = mcrfpy.TileLayer(name='terrain')
    grid = mcrfpy.Grid(grid_size=(5, 5), layers=[fog, terrain])

    assert len(grid.layers) == 2

    grid.remove_layer('fog')
    assert len(grid.layers) == 1, f"Expected 1 layer, got {len(grid.layers)}"
    assert grid.layer('fog') is None, "fog should be removed"
    assert grid.layer('terrain') is not None, "terrain should remain"

    # Removing non-existent should raise KeyError
    try:
        grid.remove_layer('nonexistent')
        assert False, "Should raise KeyError for nonexistent layer"
    except KeyError:
        pass  # Expected

    print("  PASS")

def test_remove_layer_by_object():
    """Test that remove_layer accepts layer object."""
    print("Test 7b: remove_layer by object...")

    fog = mcrfpy.ColorLayer(name='fog')
    terrain = mcrfpy.TileLayer(name='terrain')
    grid = mcrfpy.Grid(grid_size=(5, 5), layers=[fog, terrain])

    grid.remove_layer(terrain)
    assert len(grid.layers) == 1, f"Expected 1 layer, got {len(grid.layers)}"
    assert terrain.grid is None, "Removed layer should have grid=None"

    print("  PASS")

def test_name_collision_replaces():
    """Test that adding a layer with existing name replaces the old layer."""
    print("Test 8: Name collision replaces old layer...")

    old = mcrfpy.ColorLayer(name='fog')
    grid = mcrfpy.Grid(grid_size=(5, 5), layers=[old])

    assert len(grid.layers) == 1
    assert old.grid is not None

    # Add new layer with same name
    new = mcrfpy.ColorLayer(name='fog')
    grid.add_layer(new)

    assert len(grid.layers) == 1, f"Expected 1 layer after replacement, got {len(grid.layers)}"
    assert old.grid is None, "Old layer should be unlinked"
    assert new.grid is not None, "New layer should be linked"

    # Verify it's the new one
    retrieved = grid.layer('fog')
    # Both have same name, but we can check the new one is attached
    assert retrieved is not None

    print("  PASS")

def test_size_validation():
    """Test that mismatched sizes raise errors."""
    print("Test 9: Size validation...")

    # Layer with specific size that doesn't match grid
    layer = mcrfpy.ColorLayer(name='test', grid_size=(10, 10))
    grid = mcrfpy.Grid(grid_size=(5, 5), layers=[])

    try:
        grid.add_layer(layer)
        assert False, "Should raise ValueError for size mismatch"
    except ValueError as e:
        assert "size" in str(e).lower(), f"Error should mention size: {e}"

    print("  PASS")

def test_protected_names():
    """Test that protected names (walkable, transparent) are rejected."""
    print("Test 10: Protected names...")

    layer = mcrfpy.ColorLayer(name='walkable')
    grid = mcrfpy.Grid(grid_size=(5, 5), layers=[])

    try:
        grid.add_layer(layer)
        assert False, "Should raise ValueError for protected name 'walkable'"
    except ValueError as e:
        assert "reserved" in str(e).lower() or "walkable" in str(e).lower(), f"Error: {e}"

    layer2 = mcrfpy.ColorLayer(name='transparent')
    try:
        grid.add_layer(layer2)
        assert False, "Should raise ValueError for protected name 'transparent'"
    except ValueError as e:
        assert "reserved" in str(e).lower() or "transparent" in str(e).lower(), f"Error: {e}"

    print("  PASS")

def test_already_attached_error():
    """Test that attaching a layer to two grids raises error."""
    print("Test 11: Already attached error...")

    layer = mcrfpy.ColorLayer(name='shared')
    grid1 = mcrfpy.Grid(grid_size=(5, 5), layers=[layer])
    grid2 = mcrfpy.Grid(grid_size=(5, 5), layers=[])

    try:
        grid2.add_layer(layer)
        assert False, "Should raise ValueError for already attached layer"
    except ValueError as e:
        assert "attached" in str(e).lower() or "another" in str(e).lower(), f"Error: {e}"

    print("  PASS")

def run_all_tests():
    """Run all tests."""
    print("Running Grid Layer API tests...\n")

    test_layer_name_in_constructor()
    test_lazy_allocation()
    test_layer_grid_property()
    test_grid_layer_name_lookup()
    test_layers_returns_tuple()
    test_add_layer_accepts_objects()
    test_remove_layer_by_name()
    test_remove_layer_by_object()
    test_name_collision_replaces()
    test_size_validation()
    test_protected_names()
    test_already_attached_error()

    print("\n" + "="*50)
    print("All tests PASSED!")
    print("="*50)

if __name__ == "__main__":
    try:
        run_all_tests()
        sys.exit(0)
    except AssertionError as e:
        print(f"\nFAIL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
