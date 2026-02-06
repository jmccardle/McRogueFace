"""Unit tests for mcrfpy.TileSetFile - Tiled tileset loading"""
import mcrfpy
import sys
import os

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

def test_tsx_loading():
    """Test loading a .tsx tileset"""
    print("=== TSX Loading ===")
    ts = mcrfpy.TileSetFile("../tests/assets/tiled/test_tileset.tsx")
    check(ts.name == "test_tileset", f"name = '{ts.name}'")
    check(ts.tile_width == 16, f"tile_width = {ts.tile_width}")
    check(ts.tile_height == 16, f"tile_height = {ts.tile_height}")
    check(ts.tile_count == 16, f"tile_count = {ts.tile_count}")
    check(ts.columns == 4, f"columns = {ts.columns}")
    check(ts.margin == 0, f"margin = {ts.margin}")
    check(ts.spacing == 0, f"spacing = {ts.spacing}")
    check("test_tileset.png" in ts.image_source, f"image_source contains PNG: {ts.image_source}")
    return ts

def test_tsj_loading():
    """Test loading a .tsj tileset"""
    print("\n=== TSJ Loading ===")
    ts = mcrfpy.TileSetFile("../tests/assets/tiled/test_tileset.tsj")
    check(ts.name == "test_tileset", f"name = '{ts.name}'")
    check(ts.tile_width == 16, f"tile_width = {ts.tile_width}")
    check(ts.tile_height == 16, f"tile_height = {ts.tile_height}")
    check(ts.tile_count == 16, f"tile_count = {ts.tile_count}")
    check(ts.columns == 4, f"columns = {ts.columns}")
    return ts

def test_properties(ts):
    """Test tileset properties"""
    print("\n=== Properties ===")
    props = ts.properties
    check(isinstance(props, dict), f"properties is dict: {type(props)}")
    check(props.get("author") == "test", f"author = '{props.get('author')}'")
    check(props.get("version") == 1, f"version = {props.get('version')}")

def test_tile_info(ts):
    """Test per-tile metadata"""
    print("\n=== Tile Info ===")
    info = ts.tile_info(0)
    check(info is not None, "tile_info(0) exists")
    check("properties" in info, "has 'properties' key")
    check("animation" in info, "has 'animation' key")
    check(info["properties"].get("terrain") == "grass", f"terrain = '{info['properties'].get('terrain')}'")
    check(info["properties"].get("walkable") == True, f"walkable = {info['properties'].get('walkable')}")
    check(len(info["animation"]) == 2, f"animation frames = {len(info['animation'])}")
    check(info["animation"][0] == (0, 500), f"frame 0 = {info['animation'][0]}")
    check(info["animation"][1] == (4, 500), f"frame 1 = {info['animation'][1]}")

    info1 = ts.tile_info(1)
    check(info1 is not None, "tile_info(1) exists")
    check(info1["properties"].get("terrain") == "dirt", f"terrain = '{info1['properties'].get('terrain')}'")
    check(len(info1["animation"]) == 0, "tile 1 has no animation")

    info_none = ts.tile_info(5)
    check(info_none is None, "tile_info(5) returns None (no metadata)")

def test_wang_sets(ts):
    """Test Wang set access"""
    print("\n=== Wang Sets ===")
    wang_sets = ts.wang_sets
    check(len(wang_sets) == 1, f"wang_sets count = {len(wang_sets)}")

    ws = wang_sets[0]
    check(ws.name == "terrain", f"wang set name = '{ws.name}'")
    check(ws.type == "corner", f"wang set type = '{ws.type}'")
    check(ws.color_count == 2, f"color_count = {ws.color_count}")

    colors = ws.colors
    check(len(colors) == 2, f"colors length = {len(colors)}")
    check(colors[0]["name"] == "Grass", f"color 0 name = '{colors[0]['name']}'")
    check(colors[0]["index"] == 1, f"color 0 index = {colors[0]['index']}")
    check(colors[1]["name"] == "Dirt", f"color 1 name = '{colors[1]['name']}'")
    check(colors[1]["index"] == 2, f"color 1 index = {colors[1]['index']}")

def test_wang_set_lookup(ts):
    """Test wang_set() method"""
    print("\n=== Wang Set Lookup ===")
    ws = ts.wang_set("terrain")
    check(ws.name == "terrain", "wang_set('terrain') found")

    try:
        ts.wang_set("nonexistent")
        check(False, "wang_set('nonexistent') should raise KeyError")
    except KeyError:
        check(True, "wang_set('nonexistent') raises KeyError")

def test_to_texture(ts):
    """Test texture creation"""
    print("\n=== to_texture ===")
    tex = ts.to_texture()
    check(tex is not None, "to_texture() returns a Texture")
    check(isinstance(tex, mcrfpy.Texture), f"is Texture: {type(tex)}")

def test_error_handling():
    """Test error cases"""
    print("\n=== Error Handling ===")
    try:
        mcrfpy.TileSetFile("nonexistent.tsx")
        check(False, "Missing file should raise IOError")
    except IOError:
        check(True, "Missing file raises IOError")

def test_repr(ts):
    """Test repr"""
    print("\n=== Repr ===")
    r = repr(ts)
    check("TileSetFile" in r, f"repr contains 'TileSetFile': {r}")
    check("test_tileset" in r, f"repr contains name: {r}")

def main():
    ts_tsx = test_tsx_loading()
    ts_tsj = test_tsj_loading()
    test_properties(ts_tsx)
    test_tile_info(ts_tsx)
    test_wang_sets(ts_tsx)
    test_wang_set_lookup(ts_tsx)
    test_to_texture(ts_tsx)
    test_error_handling()
    test_repr(ts_tsx)

    print(f"\n{'='*40}")
    print(f"Results: {PASS_COUNT} passed, {FAIL_COUNT} failed")
    if FAIL_COUNT > 0:
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
