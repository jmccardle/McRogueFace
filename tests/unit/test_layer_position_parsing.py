#!/usr/bin/env python3
"""Test ColorLayer and TileLayer position parsing with new PyPositionHelper pattern."""
import sys
import mcrfpy

def test_colorlayer_at():
    """Test ColorLayer.at() with various position formats."""
    print("Testing ColorLayer.at() position parsing...")

    # Create a grid and color layer
    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = mcrfpy.ColorLayer(z_index=-1, grid_size=(10, 10))
    grid.add_layer(layer)

    # Set a color at position
    layer.set((5, 5), mcrfpy.Color(255, 0, 0))

    # Test at() with tuple
    c1 = layer.at((5, 5))
    assert c1.r == 255 and c1.g == 0 and c1.b == 0, f"Failed: tuple position - got {c1.r},{c1.g},{c1.b}"
    print("  - tuple position: PASS")

    # Test at() with two args
    c2 = layer.at(5, 5)
    assert c2.r == 255 and c2.g == 0 and c2.b == 0, f"Failed: two args - got {c2.r},{c2.g},{c2.b}"
    print("  - two args: PASS")

    # Test at() with list (if supported)
    c3 = layer.at([5, 5])
    assert c3.r == 255 and c3.g == 0 and c3.b == 0, f"Failed: list position - got {c3.r},{c3.g},{c3.b}"
    print("  - list position: PASS")

    # Test at() with Vector
    vec = mcrfpy.Vector(5, 5)
    c4 = layer.at(vec)
    assert c4.r == 255 and c4.g == 0 and c4.b == 0, f"Failed: Vector position - got {c4.r},{c4.g},{c4.b}"
    print("  - Vector position: PASS")

    print("ColorLayer.at(): ALL PASS")


def test_colorlayer_set():
    """Test ColorLayer.set() with grouped position."""
    print("Testing ColorLayer.set() grouped position...")

    grid = mcrfpy.Grid(grid_size=(10, 10))
    layer = mcrfpy.ColorLayer(z_index=-1, grid_size=(10, 10))
    grid.add_layer(layer)

    # Test set() with tuple position
    layer.set((3, 4), mcrfpy.Color(0, 255, 0))
    c = layer.at((3, 4))
    assert c.g == 255, f"Failed: tuple position - got g={c.g}"
    print("  - tuple position: PASS")

    # Test set() with list position
    layer.set([7, 8], (0, 0, 255))  # Also test tuple color
    c2 = layer.at((7, 8))
    assert c2.b == 255, f"Failed: list position - got b={c2.b}"
    print("  - list position: PASS")

    # Test set() with Vector position
    layer.set(mcrfpy.Vector(1, 1), mcrfpy.Color(128, 128, 128))
    c3 = layer.at((1, 1))
    assert c3.r == 128, f"Failed: Vector position - got r={c3.r}"
    print("  - Vector position: PASS")

    print("ColorLayer.set(): ALL PASS")


def test_tilelayer_at():
    """Test TileLayer.at() with various position formats."""
    print("Testing TileLayer.at() position parsing...")

    # Create a grid and tile layer
    grid = mcrfpy.Grid(grid_size=(10, 10))
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    layer = mcrfpy.TileLayer(z_index=-1, texture=texture, grid_size=(10, 10))
    grid.add_layer(layer)

    # Set a tile at position
    layer.set((5, 5), 42)

    # Test at() with tuple
    t1 = layer.at((5, 5))
    assert t1 == 42, f"Failed: tuple position - got {t1}"
    print("  - tuple position: PASS")

    # Test at() with two args
    t2 = layer.at(5, 5)
    assert t2 == 42, f"Failed: two args - got {t2}"
    print("  - two args: PASS")

    # Test at() with list
    t3 = layer.at([5, 5])
    assert t3 == 42, f"Failed: list position - got {t3}"
    print("  - list position: PASS")

    # Test at() with Vector
    t4 = layer.at(mcrfpy.Vector(5, 5))
    assert t4 == 42, f"Failed: Vector position - got {t4}"
    print("  - Vector position: PASS")

    print("TileLayer.at(): ALL PASS")


def test_tilelayer_set():
    """Test TileLayer.set() with grouped position."""
    print("Testing TileLayer.set() grouped position...")

    grid = mcrfpy.Grid(grid_size=(10, 10))
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    layer = mcrfpy.TileLayer(z_index=-1, texture=texture, grid_size=(10, 10))
    grid.add_layer(layer)

    # Test set() with tuple position
    layer.set((3, 4), 10)
    assert layer.at((3, 4)) == 10, "Failed: tuple position"
    print("  - tuple position: PASS")

    # Test set() with list position
    layer.set([7, 8], 20)
    assert layer.at((7, 8)) == 20, "Failed: list position"
    print("  - list position: PASS")

    # Test set() with Vector position
    layer.set(mcrfpy.Vector(1, 1), 30)
    assert layer.at((1, 1)) == 30, "Failed: Vector position"
    print("  - Vector position: PASS")

    print("TileLayer.set(): ALL PASS")


# Run all tests
try:
    test_colorlayer_at()
    test_colorlayer_set()
    test_tilelayer_at()
    test_tilelayer_set()
    print("\n=== ALL TESTS PASSED ===")
    sys.exit(0)
except AssertionError as e:
    print(f"\nTEST FAILED: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\nTEST ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
