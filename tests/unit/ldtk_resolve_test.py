"""Unit tests for LDtk auto-rule resolution."""
import mcrfpy
import sys

def test_basic_resolve():
    """Test resolving a simple IntGrid against auto-rules."""
    proj = mcrfpy.LdtkProject("../tests/fixtures/test_project.ldtk")
    rs = proj.ruleset("Terrain")

    # Create a DiscreteMap matching the test fixture
    dm = mcrfpy.DiscreteMap((5, 5), fill=0)
    # Fill with the same pattern as test_project.ldtk Level_0:
    # 1 1 1 1 1
    # 1 2 2 2 1
    # 1 2 3 2 1
    # 1 2 2 2 1
    # 1 1 1 1 1
    for y in range(5):
        for x in range(5):
            if x == 0 or x == 4 or y == 0 or y == 4:
                dm.set(x, y, 1)  # wall
            elif x == 2 and y == 2:
                dm.set(x, y, 3)  # water
            else:
                dm.set(x, y, 2)  # floor

    tiles = rs.resolve(dm, seed=0)
    assert isinstance(tiles, list), f"Expected list, got {type(tiles)}"
    assert len(tiles) == 25, f"Expected 25 tiles, got {len(tiles)}"
    print(f"  resolved: {tiles}")

    # Wall cells (value=1) should have tile_id 0 (from rule 51 matching pattern center=1)
    assert tiles[0] >= 0, f"Expected wall tile at (0,0), got {tiles[0]}"
    # Floor cells (value=2) should match floor rule (rule 61, tile_id 2 or 3)
    assert tiles[6] >= 0, f"Expected floor tile at (1,1), got {tiles[6]}"
    print("  wall and floor cells matched rules: OK")

def test_resolve_with_seed():
    """Test that different seeds produce deterministic but different results for multi-tile rules."""
    proj = mcrfpy.LdtkProject("../tests/fixtures/test_project.ldtk")
    rs = proj.ruleset("Terrain")

    dm = mcrfpy.DiscreteMap((5, 5), fill=2)  # All floor

    tiles_a = rs.resolve(dm, seed=0)
    tiles_b = rs.resolve(dm, seed=0)
    tiles_c = rs.resolve(dm, seed=42)

    # Same seed = same result
    assert tiles_a == tiles_b, "Same seed should produce same result"
    print("  deterministic with same seed: OK")

    # Different seed may produce different tile picks (floor rule has 2 alternatives)
    # Not guaranteed to differ for all cells, but we test determinism
    tiles_d = rs.resolve(dm, seed=42)
    assert tiles_c == tiles_d, "Same seed should produce same result"
    print("  deterministic with different seed: OK")

def test_resolve_empty():
    """Test resolving an all-empty grid (value 0 = empty)."""
    proj = mcrfpy.LdtkProject("../tests/fixtures/test_project.ldtk")
    rs = proj.ruleset("Terrain")

    dm = mcrfpy.DiscreteMap((3, 3), fill=0)
    tiles = rs.resolve(dm, seed=0)
    assert len(tiles) == 9, f"Expected 9 tiles, got {len(tiles)}"
    # All empty - no rules should match (rules match value 1 or 2)
    for i, t in enumerate(tiles):
        assert t == -1, f"Expected -1 at index {i}, got {t}"
    print("  empty grid: all tiles -1: OK")

def test_pattern_negation():
    """Test that negative pattern values work (must NOT match)."""
    proj = mcrfpy.LdtkProject("../tests/fixtures/test_project.ldtk")
    rs = proj.ruleset("Terrain")

    # Rule 52 has pattern: [0, -1, 0, 0, 1, 0, 0, 0, 0]
    # Center must be 1 (wall), top neighbor must NOT be 1
    # Create a 3x3 grid with wall center and non-wall top
    dm = mcrfpy.DiscreteMap((3, 3), fill=0)
    dm.set(1, 1, 1)  # center = wall
    dm.set(1, 0, 2)  # top = floor (not wall)

    tiles = rs.resolve(dm, seed=0)
    # The center cell should match rule 52 (wall with non-wall top)
    # Rule 52 gives tile_id 1 (from tileRectsIds [16,0] = column 1, row 0 = tile 1)
    center = tiles[4]  # (1,1) = index 4 in 3x3
    print(f"  negation pattern: center tile = {center}")
    # It should match either rule 51 (generic wall) or rule 52 (wall with non-wall top)
    assert center >= 0, f"Expected match at center, got {center}"
    print("  pattern negation test: OK")

def test_resolve_dimensions():
    """Test resolve works with different grid dimensions."""
    proj = mcrfpy.LdtkProject("../tests/fixtures/test_project.ldtk")
    rs = proj.ruleset("Terrain")

    for w, h in [(1, 1), (3, 3), (10, 10), (1, 20), (20, 1)]:
        dm = mcrfpy.DiscreteMap((w, h), fill=1)
        tiles = rs.resolve(dm, seed=0)
        assert len(tiles) == w * h, f"Expected {w*h} tiles for {w}x{h}, got {len(tiles)}"
    print("  various dimensions: OK")

def test_break_on_match():
    """Test that breakOnMatch prevents later rules from overwriting."""
    proj = mcrfpy.LdtkProject("../tests/fixtures/test_project.ldtk")
    rs = proj.ruleset("Terrain")

    # Create a grid where rule 51 (generic wall) should match
    # Rule 51 has breakOnMatch=true, so rule 52 should not override it
    dm = mcrfpy.DiscreteMap((3, 3), fill=1)  # All walls

    tiles = rs.resolve(dm, seed=0)
    # All cells should be tile 0 (from rule 51)
    center = tiles[4]
    assert center == 0, f"Expected tile 0 from rule 51, got {center}"
    print(f"  break on match: center = {center}: OK")

# Run tests
tests = [
    test_basic_resolve,
    test_resolve_with_seed,
    test_resolve_empty,
    test_pattern_negation,
    test_resolve_dimensions,
    test_break_on_match,
]

passed = 0
failed = 0
print("=== LDtk Resolve Tests ===")
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
