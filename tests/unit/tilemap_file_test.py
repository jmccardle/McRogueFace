"""Unit tests for mcrfpy.TileMapFile - Tiled tilemap loading"""
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

def test_tmx_loading():
    """Test loading a .tmx map"""
    print("=== TMX Loading ===")
    tm = mcrfpy.TileMapFile("../tests/assets/tiled/test_map.tmx")
    check(tm.width == 4, f"width = {tm.width}")
    check(tm.height == 4, f"height = {tm.height}")
    check(tm.tile_width == 16, f"tile_width = {tm.tile_width}")
    check(tm.tile_height == 16, f"tile_height = {tm.tile_height}")
    check(tm.orientation == "orthogonal", f"orientation = '{tm.orientation}'")
    return tm

def test_tmj_loading():
    """Test loading a .tmj map"""
    print("\n=== TMJ Loading ===")
    tm = mcrfpy.TileMapFile("../tests/assets/tiled/test_map.tmj")
    check(tm.width == 4, f"width = {tm.width}")
    check(tm.height == 4, f"height = {tm.height}")
    check(tm.tile_width == 16, f"tile_width = {tm.tile_width}")
    check(tm.tile_height == 16, f"tile_height = {tm.tile_height}")
    return tm

def test_map_properties(tm):
    """Test map properties"""
    print("\n=== Map Properties ===")
    props = tm.properties
    check(isinstance(props, dict), f"properties is dict: {type(props)}")
    check(props.get("map_name") == "test", f"map_name = '{props.get('map_name')}'")

def test_tileset_references(tm):
    """Test tileset references"""
    print("\n=== Tileset References ===")
    check(tm.tileset_count == 1, f"tileset_count = {tm.tileset_count}")

    firstgid, ts = tm.tileset(0)
    check(firstgid == 1, f"firstgid = {firstgid}")
    check(isinstance(ts, mcrfpy.TileSetFile), f"tileset is TileSetFile: {type(ts)}")
    check(ts.name == "test_tileset", f"tileset name = '{ts.name}'")
    check(ts.tile_count == 16, f"tileset tile_count = {ts.tile_count}")

def test_tile_layer_names(tm):
    """Test tile layer name listing"""
    print("\n=== Layer Names ===")
    names = tm.tile_layer_names
    check(len(names) == 2, f"tile_layer count = {len(names)}")
    check("Ground" in names, f"'Ground' in names: {names}")
    check("Overlay" in names, f"'Overlay' in names: {names}")

    obj_names = tm.object_layer_names
    check(len(obj_names) == 1, f"object_layer count = {len(obj_names)}")
    check("Objects" in obj_names, f"'Objects' in obj_names: {obj_names}")

def test_tile_layer_data(tm):
    """Test raw tile layer data access"""
    print("\n=== Tile Layer Data ===")
    ground = tm.tile_layer_data("Ground")
    check(len(ground) == 16, f"Ground layer length = {len(ground)}")
    # First row: 1,2,1,1 (GIDs)
    check(ground[0] == 1, f"ground[0] = {ground[0]}")
    check(ground[1] == 2, f"ground[1] = {ground[1]}")
    check(ground[2] == 1, f"ground[2] = {ground[2]}")
    check(ground[3] == 1, f"ground[3] = {ground[3]}")

    overlay = tm.tile_layer_data("Overlay")
    check(len(overlay) == 16, f"Overlay layer length = {len(overlay)}")
    # First row all zeros (empty)
    check(overlay[0] == 0, f"overlay[0] = {overlay[0]} (empty)")
    # Second row: 0,9,10,0
    check(overlay[5] == 9, f"overlay[5] = {overlay[5]}")

    try:
        tm.tile_layer_data("nonexistent")
        check(False, "tile_layer_data('nonexistent') should raise KeyError")
    except KeyError:
        check(True, "tile_layer_data('nonexistent') raises KeyError")

def test_resolve_gid(tm):
    """Test GID resolution"""
    print("\n=== GID Resolution ===")
    # GID 0 = empty
    ts_idx, local_id = tm.resolve_gid(0)
    check(ts_idx == -1, f"GID 0: ts_idx = {ts_idx}")
    check(local_id == -1, f"GID 0: local_id = {local_id}")

    # GID 1 = first tileset (firstgid=1), local_id=0
    ts_idx, local_id = tm.resolve_gid(1)
    check(ts_idx == 0, f"GID 1: ts_idx = {ts_idx}")
    check(local_id == 0, f"GID 1: local_id = {local_id}")

    # GID 2 = first tileset, local_id=1
    ts_idx, local_id = tm.resolve_gid(2)
    check(ts_idx == 0, f"GID 2: ts_idx = {ts_idx}")
    check(local_id == 1, f"GID 2: local_id = {local_id}")

    # GID 9 = first tileset, local_id=8
    ts_idx, local_id = tm.resolve_gid(9)
    check(ts_idx == 0, f"GID 9: ts_idx = {ts_idx}")
    check(local_id == 8, f"GID 9: local_id = {local_id}")

def test_object_layer(tm):
    """Test object layer access"""
    print("\n=== Object Layer ===")
    objects = tm.object_layer("Objects")
    check(isinstance(objects, list), f"objects is list: {type(objects)}")
    check(len(objects) == 2, f"object count = {len(objects)}")

    # Find spawn point
    spawn = None
    trigger = None
    for obj in objects:
        if obj.get("name") == "spawn":
            spawn = obj
        elif obj.get("name") == "trigger_zone":
            trigger = obj

    check(spawn is not None, "spawn object found")
    if spawn:
        check(spawn.get("x") == 32, f"spawn x = {spawn.get('x')}")
        check(spawn.get("y") == 32, f"spawn y = {spawn.get('y')}")
        check(spawn.get("point") == True, f"spawn is point")
        props = spawn.get("properties", {})
        check(props.get("player_start") == True, f"player_start = {props.get('player_start')}")

    check(trigger is not None, "trigger_zone object found")
    if trigger:
        check(trigger.get("width") == 64, f"trigger width = {trigger.get('width')}")
        check(trigger.get("height") == 64, f"trigger height = {trigger.get('height')}")
        props = trigger.get("properties", {})
        check(props.get("zone_id") == 42, f"zone_id = {props.get('zone_id')}")

    try:
        tm.object_layer("nonexistent")
        check(False, "object_layer('nonexistent') should raise KeyError")
    except KeyError:
        check(True, "object_layer('nonexistent') raises KeyError")

def test_error_handling():
    """Test error cases"""
    print("\n=== Error Handling ===")
    try:
        mcrfpy.TileMapFile("nonexistent.tmx")
        check(False, "Missing file should raise IOError")
    except IOError:
        check(True, "Missing file raises IOError")

def test_repr(tm):
    """Test repr"""
    print("\n=== Repr ===")
    r = repr(tm)
    check("TileMapFile" in r, f"repr contains 'TileMapFile': {r}")
    check("4x4" in r, f"repr contains dimensions: {r}")

def main():
    tm_tmx = test_tmx_loading()
    tm_tmj = test_tmj_loading()
    test_map_properties(tm_tmx)
    test_tileset_references(tm_tmx)
    test_tile_layer_names(tm_tmx)
    test_tile_layer_data(tm_tmx)
    test_resolve_gid(tm_tmx)
    test_object_layer(tm_tmx)
    test_error_handling()
    test_repr(tm_tmx)

    print(f"\n{'='*40}")
    print(f"Results: {PASS_COUNT} passed, {FAIL_COUNT} failed")
    if FAIL_COUNT > 0:
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
