"""Unit tests for LDtk project parsing."""
import mcrfpy
import sys
import os

def test_load_project():
    """Test basic project loading."""
    proj = mcrfpy.LdtkProject("../tests/fixtures/test_project.ldtk")
    assert proj is not None, "Failed to create LdtkProject"
    print(f"  repr: {repr(proj)}")
    return proj

def test_version(proj):
    """Test version property."""
    assert proj.version == "1.5.3", f"Expected version '1.5.3', got '{proj.version}'"
    print(f"  version: {proj.version}")

def test_tileset_names(proj):
    """Test tileset enumeration."""
    names = proj.tileset_names
    assert isinstance(names, list), f"Expected list, got {type(names)}"
    assert len(names) == 1, f"Expected 1 tileset, got {len(names)}"
    assert names[0] == "Test_Tileset", f"Expected 'Test_Tileset', got '{names[0]}'"
    print(f"  tileset_names: {names}")

def test_ruleset_names(proj):
    """Test ruleset enumeration."""
    names = proj.ruleset_names
    assert isinstance(names, list), f"Expected list, got {type(names)}"
    assert len(names) == 1, f"Expected 1 ruleset, got {len(names)}"
    assert names[0] == "Terrain", f"Expected 'Terrain', got '{names[0]}'"
    print(f"  ruleset_names: {names}")

def test_level_names(proj):
    """Test level enumeration."""
    names = proj.level_names
    assert isinstance(names, list), f"Expected list, got {type(names)}"
    assert len(names) == 1, f"Expected 1 level, got {len(names)}"
    assert names[0] == "Level_0", f"Expected 'Level_0', got '{names[0]}'"
    print(f"  level_names: {names}")

def test_enums(proj):
    """Test enum access."""
    enums = proj.enums
    assert isinstance(enums, list), f"Expected list, got {type(enums)}"
    assert len(enums) == 1, f"Expected 1 enum, got {len(enums)}"
    assert enums[0]["identifier"] == "TileType"
    print(f"  enums: {len(enums)} enum(s), first = {enums[0]['identifier']}")

def test_tileset_access(proj):
    """Test tileset retrieval."""
    ts = proj.tileset("Test_Tileset")
    assert ts is not None, "Failed to get tileset"
    print(f"  tileset: {repr(ts)}")
    assert ts.name == "Test_Tileset", f"Expected 'Test_Tileset', got '{ts.name}'"
    assert ts.tile_width == 16, f"Expected tile_width 16, got {ts.tile_width}"
    assert ts.tile_height == 16, f"Expected tile_height 16, got {ts.tile_height}"
    assert ts.columns == 4, f"Expected columns 4, got {ts.columns}"
    assert ts.tile_count == 16, f"Expected tile_count 16, got {ts.tile_count}"

def test_tileset_not_found(proj):
    """Test KeyError for missing tileset."""
    try:
        proj.tileset("Nonexistent")
        assert False, "Should have raised KeyError"
    except KeyError:
        pass
    print("  KeyError raised for missing tileset: OK")

def test_ruleset_access(proj):
    """Test ruleset retrieval."""
    rs = proj.ruleset("Terrain")
    assert rs is not None, "Failed to get ruleset"
    print(f"  ruleset: {repr(rs)}")
    assert rs.name == "Terrain", f"Expected 'Terrain', got '{rs.name}'"
    assert rs.grid_size == 16, f"Expected grid_size 16, got {rs.grid_size}"
    assert rs.value_count == 3, f"Expected 3 values, got {rs.value_count}"
    assert rs.group_count == 2, f"Expected 2 groups, got {rs.group_count}"
    assert rs.rule_count == 3, f"Expected 3 rules, got {rs.rule_count}"

def test_ruleset_values(proj):
    """Test IntGrid value definitions."""
    rs = proj.ruleset("Terrain")
    values = rs.values
    assert len(values) == 3, f"Expected 3 values, got {len(values)}"
    assert values[0]["value"] == 1
    assert values[0]["name"] == "wall"
    assert values[1]["value"] == 2
    assert values[1]["name"] == "floor"
    assert values[2]["value"] == 3
    assert values[2]["name"] == "water"
    print(f"  values: {values}")

def test_terrain_enum(proj):
    """Test terrain_enum() generation."""
    rs = proj.ruleset("Terrain")
    Terrain = rs.terrain_enum()
    assert Terrain is not None, "Failed to create terrain enum"
    assert Terrain.NONE == 0, f"Expected NONE=0, got {Terrain.NONE}"
    assert Terrain.WALL == 1, f"Expected WALL=1, got {Terrain.WALL}"
    assert Terrain.FLOOR == 2, f"Expected FLOOR=2, got {Terrain.FLOOR}"
    assert Terrain.WATER == 3, f"Expected WATER=3, got {Terrain.WATER}"
    print(f"  terrain enum: {list(Terrain)}")

def test_level_access(proj):
    """Test level data retrieval."""
    level = proj.level("Level_0")
    assert isinstance(level, dict), f"Expected dict, got {type(level)}"
    assert level["name"] == "Level_0"
    assert level["width_px"] == 80
    assert level["height_px"] == 80
    assert level["world_x"] == 0
    assert level["world_y"] == 0
    print(f"  level: {level['name']} ({level['width_px']}x{level['height_px']}px)")

def test_level_layers(proj):
    """Test level layer data."""
    level = proj.level("Level_0")
    layers = level["layers"]
    assert len(layers) == 1, f"Expected 1 layer, got {len(layers)}"

    layer = layers[0]
    assert layer["name"] == "Terrain"
    assert layer["type"] == "IntGrid"
    assert layer["width"] == 5
    assert layer["height"] == 5
    print(f"  layer: {layer['name']} ({layer['type']}) {layer['width']}x{layer['height']}")

def test_level_intgrid(proj):
    """Test IntGrid CSV data."""
    level = proj.level("Level_0")
    layer = level["layers"][0]
    intgrid = layer["intgrid"]
    assert len(intgrid) == 25, f"Expected 25 cells, got {len(intgrid)}"
    # Check corners are walls (1)
    assert intgrid[0] == 1, f"Expected wall at (0,0), got {intgrid[0]}"
    assert intgrid[4] == 1, f"Expected wall at (4,0), got {intgrid[4]}"
    # Check center is water (3)
    assert intgrid[12] == 3, f"Expected water at (2,2), got {intgrid[12]}"
    # Check floor tiles (2)
    assert intgrid[6] == 2, f"Expected floor at (1,1), got {intgrid[6]}"
    print(f"  intgrid: {intgrid[:5]}... ({len(intgrid)} cells)")

def test_level_auto_tiles(proj):
    """Test pre-computed auto-layer tiles."""
    level = proj.level("Level_0")
    layer = level["layers"][0]
    auto_tiles = layer["auto_tiles"]
    assert len(auto_tiles) > 0, f"Expected auto tiles, got {len(auto_tiles)}"
    # Check first tile structure
    t = auto_tiles[0]
    assert "tile_id" in t, f"Missing tile_id in auto tile: {t}"
    assert "x" in t, f"Missing x in auto tile: {t}"
    assert "y" in t, f"Missing y in auto tile: {t}"
    assert "flip" in t, f"Missing flip in auto tile: {t}"
    print(f"  auto_tiles: {len(auto_tiles)} tiles, first = {auto_tiles[0]}")

def test_level_not_found(proj):
    """Test KeyError for missing level."""
    try:
        proj.level("Nonexistent")
        assert False, "Should have raised KeyError"
    except KeyError:
        pass
    print("  KeyError raised for missing level: OK")

def test_load_nonexistent():
    """Test IOError for missing file."""
    try:
        mcrfpy.LdtkProject("nonexistent.ldtk")
        assert False, "Should have raised IOError"
    except IOError:
        pass
    print("  IOError raised for missing file: OK")

# Run all tests
tests = [
    ("load_project", None),
    ("version", None),
    ("tileset_names", None),
    ("ruleset_names", None),
    ("level_names", None),
    ("enums", None),
    ("tileset_access", None),
    ("tileset_not_found", None),
    ("ruleset_access", None),
    ("ruleset_values", None),
    ("terrain_enum", None),
    ("level_access", None),
    ("level_layers", None),
    ("level_intgrid", None),
    ("level_auto_tiles", None),
    ("level_not_found", None),
    ("load_nonexistent", None),
]

passed = 0
failed = 0
proj = None

# First test returns the project
print("=== LDtk Parse Tests ===")
for name, func in tests:
    try:
        test_fn = globals()[f"test_{name}"]
        print(f"[TEST] {name}...")
        if name == "load_project":
            proj = test_fn()
        elif name in ("load_nonexistent",):
            test_fn()
        else:
            test_fn(proj)
        passed += 1
        print(f"  PASS")
    except Exception as e:
        failed += 1
        print(f"  FAIL: {e}")

print(f"\n=== Results: {passed} passed, {failed} failed ===")
if failed > 0:
    sys.exit(1)
sys.exit(0)
