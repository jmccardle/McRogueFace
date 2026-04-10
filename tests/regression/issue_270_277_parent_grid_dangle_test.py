"""Regression test: parent_grid dangling raw pointer (#270, #271, #277).

Bug: GridLayer, UIGridPoint, and GridChunk each stored a raw GridData*
parent_grid pointer. If the grid was destroyed while a C++ shared_ptr
still held a layer, the raw pointer would dangle and subsequent layer
operations that need the grid (like updatePerspective/drawFOV) could crash.

Fix: GridData::~GridData() now nulls parent_grid in all layers, grid
points, and chunks before destruction. All usage sites already have
null checks so they degrade gracefully.
"""
import mcrfpy
import sys
import gc

def test_layer_detach_then_access():
    """Layer operations work after explicit detach from grid (#270)"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = mcrfpy.ColorLayer(z_index=-1, name="fog")
    grid.add_layer(layer)
    layer.fill(mcrfpy.Color(50, 50, 50))

    # Detach layer - this nulls parent_grid
    layer.grid = None
    gc.collect()

    # Layer should still be usable for non-grid operations
    assert layer is not None
    assert layer.name == "fog"
    assert layer.z_index == -1
    assert layer.grid is None
    print("  PASS: layer_detach_then_access")

def test_tilelayer_detach_then_access():
    """TileLayer operations work after explicit detach (#270)"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = mcrfpy.TileLayer(z_index=-2, name="terrain")
    grid.add_layer(layer)

    layer.grid = None
    gc.collect()

    assert layer is not None
    assert layer.name == "terrain"
    assert layer.z_index == -2
    assert layer.grid is None
    print("  PASS: tilelayer_detach_then_access")

def test_gridpoint_property_setter_with_valid_grid():
    """GridPoint walkable/transparent setters sync TCOD map (#271)"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    gp = grid.at(5, 5)
    gp.walkable = True
    assert gp.walkable == True
    gp.transparent = True
    assert gp.transparent == True

    # Verify sync worked by checking the reverse
    gp.walkable = False
    assert gp.walkable == False
    print("  PASS: gridpoint_property_setter_with_valid_grid")

def test_layer_reattach_to_new_grid():
    """Layer can be detached from one grid and attached to another"""
    grid1 = mcrfpy.Grid(grid_size=(10, 10))
    layer = mcrfpy.ColorLayer(z_index=-1, name="fog")
    grid1.add_layer(layer)
    layer.fill(mcrfpy.Color(50, 50, 50))

    # Detach from first grid
    layer.grid = None
    assert layer.grid is None

    # Attach to new grid (same size since layer size must match)
    grid2 = mcrfpy.Grid(grid_size=(10, 10))
    grid2.add_layer(layer)
    assert layer.grid is not None
    print("  PASS: layer_reattach_to_new_grid")

def test_multiple_layers_detach():
    """Multiple layers can be detached independently"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    color = mcrfpy.ColorLayer(z_index=-1, name="color")
    tile = mcrfpy.TileLayer(z_index=-2, name="tile")
    grid.add_layer(color)
    grid.add_layer(tile)

    color.grid = None
    assert color.grid is None
    assert tile.grid is not None

    tile.grid = None
    assert tile.grid is None
    print("  PASS: multiple_layers_detach")

def test_layer_from_grid_layers_tuple():
    """Layers obtained from grid.layers have proper grid reference"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = mcrfpy.ColorLayer(z_index=-1, name="fog")
    grid.add_layer(layer)

    # Get layer through grid.layers property (grid has default 'tilesprite' layer too)
    layers = grid.layers
    assert len(layers) >= 2  # default tilesprite + our fog
    # Find our layer by name
    retrieved = [l for l in layers if l.name == "fog"]
    assert len(retrieved) == 1
    assert retrieved[0].grid is not None
    print("  PASS: layer_from_grid_layers_tuple")

def test_large_grid_chunks():
    """Large grids use chunk storage; GridPoints have valid parent_grid (#277)"""
    # Threshold is 64, so 100x100 uses chunks
    grid = mcrfpy.Grid(grid_size=(100, 100))
    gp = grid.at(50, 50)
    gp.walkable = True
    assert gp.walkable == True
    gp.transparent = True
    assert gp.transparent == True

    # Edge cell
    gp2 = grid.at(99, 99)
    gp2.walkable = True
    assert gp2.walkable == True
    print("  PASS: large_grid_chunks")


print("Testing parent_grid dangling pointer fixes (#270, #271, #277)...")
test_layer_detach_then_access()
test_tilelayer_detach_then_access()
test_gridpoint_property_setter_with_valid_grid()
test_layer_reattach_to_new_grid()
test_multiple_layers_detach()
test_layer_from_grid_layers_tuple()
test_large_grid_chunks()
print("PASS: all parent_grid dangling pointer tests passed")
sys.exit(0)
