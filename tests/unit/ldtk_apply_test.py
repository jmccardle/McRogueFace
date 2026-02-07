"""Unit tests for LDtk auto-rule apply (resolve + write to TileLayer)."""
import mcrfpy
import sys

def test_apply_basic():
    """Test applying rules to a TileLayer."""
    proj = mcrfpy.LdtkProject("../tests/fixtures/test_project.ldtk")
    rs = proj.ruleset("Terrain")
    ts = proj.tileset("Test_Tileset")
    texture = ts.to_texture()

    # Create DiscreteMap
    dm = mcrfpy.DiscreteMap((5, 5), fill=0)
    for y in range(5):
        for x in range(5):
            if x == 0 or x == 4 or y == 0 or y == 4:
                dm.set(x, y, 1)
            elif x == 2 and y == 2:
                dm.set(x, y, 3)
            else:
                dm.set(x, y, 2)

    # Create TileLayer and apply
    layer = mcrfpy.TileLayer(name="terrain", texture=texture, grid_size=(5, 5))
    rs.apply(dm, layer, seed=0)

    # Verify some tiles were written
    wall_tile = layer.at(0, 0)
    assert wall_tile == 0, f"Expected wall tile 0 at (0,0), got {wall_tile}"

    floor_tile = layer.at(1, 1)
    assert floor_tile >= 0, f"Expected floor tile at (1,1), got {floor_tile}"

    # Empty cells (water, value=3) should still be -1 (no rule matches water)
    water_tile = layer.at(2, 2)
    assert water_tile == -1, f"Expected -1 at water (2,2), got {water_tile}"

    print(f"  applied: wall={wall_tile}, floor={floor_tile}, water={water_tile}")

def test_apply_preserves_unmatched():
    """Test that unmatched cells retain their original value."""
    proj = mcrfpy.LdtkProject("../tests/fixtures/test_project.ldtk")
    rs = proj.ruleset("Terrain")
    ts = proj.tileset("Test_Tileset")
    texture = ts.to_texture()

    # Pre-fill layer with a sentinel value
    layer = mcrfpy.TileLayer(name="test", texture=texture, grid_size=(3, 3))
    layer.fill(99)

    # Create empty map - no rules will match
    dm = mcrfpy.DiscreteMap((3, 3), fill=0)
    rs.apply(dm, layer, seed=0)

    # All cells should still be 99 (no rules matched)
    for y in range(3):
        for x in range(3):
            val = layer.at(x, y)
            assert val == 99, f"Expected 99 at ({x},{y}), got {val}"
    print("  unmatched cells preserved: OK")

def test_apply_type_errors():
    """Test that apply raises TypeError for wrong argument types."""
    proj = mcrfpy.LdtkProject("../tests/fixtures/test_project.ldtk")
    rs = proj.ruleset("Terrain")

    # Wrong first argument type
    try:
        rs.apply("not_a_dmap", None, seed=0)
        assert False, "Should have raised TypeError"
    except TypeError:
        pass

    # Wrong second argument type
    dm = mcrfpy.DiscreteMap((3, 3))
    try:
        rs.apply(dm, "not_a_layer", seed=0)
        assert False, "Should have raised TypeError"
    except TypeError:
        pass

    print("  type errors raised correctly: OK")

def test_apply_clipping():
    """Test that apply clips to the smaller of map/layer dimensions."""
    proj = mcrfpy.LdtkProject("../tests/fixtures/test_project.ldtk")
    rs = proj.ruleset("Terrain")
    ts = proj.tileset("Test_Tileset")
    texture = ts.to_texture()

    # DiscreteMap larger than TileLayer
    dm = mcrfpy.DiscreteMap((10, 10), fill=1)
    layer = mcrfpy.TileLayer(name="small", texture=texture, grid_size=(3, 3))
    layer.fill(-1)

    rs.apply(dm, layer, seed=0)

    # Layer should have tiles written only within its bounds
    for y in range(3):
        for x in range(3):
            val = layer.at(x, y)
            assert val >= 0, f"Expected tile at ({x},{y}), got {val}"
    print("  clipping (large map, small layer): OK")

    # DiscreteMap smaller than TileLayer
    dm2 = mcrfpy.DiscreteMap((2, 2), fill=1)
    layer2 = mcrfpy.TileLayer(name="big", texture=texture, grid_size=(5, 5))
    layer2.fill(88)

    rs.apply(dm2, layer2, seed=0)

    # Only (0,0)-(1,1) should be overwritten
    for y in range(2):
        for x in range(2):
            val = layer2.at(x, y)
            assert val >= 0, f"Expected tile at ({x},{y}), got {val}"

    # (3,3) should still be the fill value
    assert layer2.at(3, 3) == 88, f"Expected 88 at (3,3), got {layer2.at(3, 3)}"
    print("  clipping (small map, large layer): OK")

def test_resolve_type_error():
    """Test that resolve raises TypeError for wrong argument."""
    proj = mcrfpy.LdtkProject("../tests/fixtures/test_project.ldtk")
    rs = proj.ruleset("Terrain")

    try:
        rs.resolve("not_a_dmap", seed=0)
        assert False, "Should have raised TypeError"
    except TypeError:
        pass
    print("  resolve TypeError: OK")

def test_precomputed_tiles():
    """Test loading pre-computed auto-layer tiles from a level."""
    proj = mcrfpy.LdtkProject("../tests/fixtures/test_project.ldtk")
    ts = proj.tileset("Test_Tileset")
    texture = ts.to_texture()

    level = proj.level("Level_0")
    layer_info = level["layers"][0]

    # Create TileLayer and write pre-computed tiles
    layer = mcrfpy.TileLayer(name="precomp", texture=texture, grid_size=(5, 5))
    layer.fill(-1)

    for tile in layer_info["auto_tiles"]:
        x, y = tile["x"], tile["y"]
        if 0 <= x < 5 and 0 <= y < 5:
            layer.set((x, y), tile["tile_id"])

    # Verify some tiles were written
    assert layer.at(0, 0) == 0, f"Expected tile 0 at (0,0), got {layer.at(0, 0)}"
    print(f"  precomputed tiles loaded: first = {layer.at(0, 0)}")

# Run tests
tests = [
    test_apply_basic,
    test_apply_preserves_unmatched,
    test_apply_type_errors,
    test_apply_clipping,
    test_resolve_type_error,
    test_precomputed_tiles,
]

passed = 0
failed = 0
print("=== LDtk Apply Tests ===")
for test in tests:
    name = test.__name__
    try:
        print(f"[TEST] {name}...")
        test()
        passed += 1
        print(f"  PASS")
    except Exception as e:
        failed += 1
        print(f"  FAIL: {e}")

print(f"\n=== Results: {passed} passed, {failed} failed ===")
if failed > 0:
    sys.exit(1)
sys.exit(0)
