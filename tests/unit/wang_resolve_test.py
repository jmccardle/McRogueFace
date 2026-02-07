"""Unit tests for WangSet terrain_enum, resolve, and apply"""
import mcrfpy
import sys

PASS_COUNT = 0
FAIL_COUNT = 0

def check(condition, msg):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"  PASS: {msg}")
    else:
        FAIL_COUNT += 1
        print(f"  FAIL: {msg}")

def test_terrain_enum():
    """Test IntEnum generation from WangSet colors"""
    print("=== Terrain Enum ===")
    ts = mcrfpy.TileSetFile("../tests/assets/tiled/test_tileset.tsx")
    ws = ts.wang_set("terrain")
    Terrain = ws.terrain_enum()

    check(Terrain is not None, "terrain_enum() returns something")
    check(hasattr(Terrain, "NONE"), "has NONE member")
    check(hasattr(Terrain, "GRASS"), "has GRASS member")
    check(hasattr(Terrain, "DIRT"), "has DIRT member")
    check(int(Terrain.NONE) == 0, f"NONE = {int(Terrain.NONE)}")
    check(int(Terrain.GRASS) == 1, f"GRASS = {int(Terrain.GRASS)}")
    check(int(Terrain.DIRT) == 2, f"DIRT = {int(Terrain.DIRT)}")

    # Check it's an IntEnum
    import enum
    check(issubclass(Terrain, enum.IntEnum), "is IntEnum subclass")
    return Terrain

def test_enum_with_discrete_map(Terrain):
    """Test that terrain enum is compatible with DiscreteMap"""
    print("\n=== Enum + DiscreteMap ===")
    dm = mcrfpy.DiscreteMap((4, 4))
    dm.enum_type = Terrain
    check(dm.enum_type == Terrain, "DiscreteMap accepts terrain enum")

    # Set values using enum
    dm.set(0, 0, Terrain.GRASS)
    dm.set(1, 0, Terrain.DIRT)
    val = dm.get(0, 0)
    check(int(val) == int(Terrain.GRASS), f"get(0,0) = {val}")
    val = dm.get(1, 0)
    check(int(val) == int(Terrain.DIRT), f"get(1,0) = {val}")

def test_resolve_uniform():
    """Test resolve with uniform terrain"""
    print("\n=== Resolve Uniform ===")
    ts = mcrfpy.TileSetFile("../tests/assets/tiled/test_tileset.tsx")
    ws = ts.wang_set("terrain")

    # All grass (terrain ID 1)
    dm = mcrfpy.DiscreteMap((3, 3))
    dm.fill(1)  # All grass

    tiles = ws.resolve(dm)
    check(isinstance(tiles, list), f"resolve returns list: {type(tiles)}")
    check(len(tiles) == 9, f"resolve length = {len(tiles)}")

    # All cells should map to the "all grass corners" tile (id=0)
    # wangid [0,1,0,1,0,1,0,1] = tile 0
    # Note: border cells will see 0 (NONE) on their outer edges, so may not match
    # Center cell (1,1) sees all grass neighbors -> should be tile 0
    center = tiles[4]  # (1,1) in 3x3
    check(center == 0, f"center tile (uniform grass) = {center}")

def test_resolve_mixed():
    """Test resolve with mixed terrain"""
    print("\n=== Resolve Mixed ===")
    ts = mcrfpy.TileSetFile("../tests/assets/tiled/test_tileset.tsx")
    ws = ts.wang_set("terrain")

    # Create a 3x3 grid: grass everywhere except center = dirt
    dm = mcrfpy.DiscreteMap((3, 3))
    dm.fill(1)  # All grass
    dm.set(1, 1, 2)  # Center = dirt

    tiles = ws.resolve(dm)
    check(len(tiles) == 9, f"resolve length = {len(tiles)}")

    # The center cell has grass neighbors and is dirt itself
    # Corners depend on the max of surrounding cells
    center = tiles[4]
    # Center: all 4 corners should be max(dirt, grass neighbors) = 2 (dirt)
    # wangid [0,2,0,2,0,2,0,2] = tile 1 (all-dirt)
    check(center == 1, f"center (dirt surrounded by grass) = {center}")

def test_resolve_returns_negative_for_unknown():
    """Test that unknown wangid combinations return -1"""
    print("\n=== Unknown WangID ===")
    ts = mcrfpy.TileSetFile("../tests/assets/tiled/test_tileset.tsx")
    ws = ts.wang_set("terrain")

    # Use terrain ID 3 which doesn't exist in the wang set
    dm = mcrfpy.DiscreteMap((2, 2))
    dm.fill(3)  # Terrain 3 not in wang set

    tiles = ws.resolve(dm)
    # All should be -1 since terrain 3 has no matching wangid
    all_neg = all(t == -1 for t in tiles)
    check(all_neg, f"all tiles = -1 for unknown terrain: {tiles}")

def test_resolve_border_handling():
    """Test that border cells handle out-of-bounds correctly"""
    print("\n=== Border Handling ===")
    ts = mcrfpy.TileSetFile("../tests/assets/tiled/test_tileset.tsx")
    ws = ts.wang_set("terrain")

    # 1x1 grid - all neighbors are out-of-bounds (0)
    dm = mcrfpy.DiscreteMap((1, 1))
    dm.set(0, 0, 1)  # Single grass cell

    tiles = ws.resolve(dm)
    check(len(tiles) == 1, f"1x1 resolve length = {len(tiles)}")
    # Corner terrain: max(0, 0, 0, grass) = 1 for each corner -> all grass
    # wangid [0,1,0,1,0,1,0,1] = tile 0
    check(tiles[0] == 0, f"1x1 grass tile = {tiles[0]}")

def test_wang_set_repr():
    """Test WangSet repr"""
    print("\n=== WangSet Repr ===")
    ts = mcrfpy.TileSetFile("../tests/assets/tiled/test_tileset.tsx")
    ws = ts.wang_set("terrain")
    r = repr(ws)
    check("WangSet" in r, f"repr contains 'WangSet': {r}")
    check("terrain" in r, f"repr contains name: {r}")
    check("corner" in r, f"repr contains type: {r}")

def main():
    Terrain = test_terrain_enum()
    test_enum_with_discrete_map(Terrain)
    test_resolve_uniform()
    test_resolve_mixed()
    test_resolve_returns_negative_for_unknown()
    test_resolve_border_handling()
    test_wang_set_repr()

    print(f"\n{'='*40}")
    print(f"Results: {PASS_COUNT} passed, {FAIL_COUNT} failed")
    if FAIL_COUNT > 0:
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
