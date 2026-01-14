"""Test DijkstraMap.to_heightmap() method."""
import mcrfpy
import sys

def test_basic_conversion():
    """Test basic conversion of DijkstraMap to HeightMap."""
    grid = mcrfpy.Grid(grid_size=(10, 10))

    # Initialize all cells as walkable
    for y in range(10):
        for x in range(10):
            grid.at((x, y)).walkable = True

    # Get a dijkstra map from center
    dijkstra = grid.get_dijkstra_map((5, 5))

    # Convert to heightmap
    hmap = dijkstra.to_heightmap()

    # Verify type
    assert type(hmap).__name__ == "HeightMap", f"Expected HeightMap, got {type(hmap).__name__}"

    # Verify root cell has distance 0
    assert hmap[(5, 5)] == 0.0, f"Root cell should have height 0, got {hmap[(5, 5)]}"

    # Verify corner has non-zero distance
    corner_dist = dijkstra.distance((0, 0))
    corner_height = hmap[(0, 0)]
    assert abs(corner_dist - corner_height) < 0.001, f"Height {corner_height} should match distance {corner_dist}"

    print("test_basic_conversion PASSED")

def test_unreachable_cells():
    """Test that unreachable cells use the unreachable parameter."""
    grid = mcrfpy.Grid(grid_size=(10, 10))

    # Initialize all cells as walkable
    for y in range(10):
        for x in range(10):
            grid.at((x, y)).walkable = True

    # Add a wall
    grid.at((3, 3)).walkable = False

    dijkstra = grid.get_dijkstra_map((5, 5))

    # Default unreachable value is -1.0 (distinct from root which has distance 0)
    hmap1 = dijkstra.to_heightmap()
    assert hmap1[(3, 3)] == -1.0, f"Default unreachable should be -1.0, got {hmap1[(3, 3)]}"

    # Custom unreachable value
    hmap2 = dijkstra.to_heightmap(unreachable=0.0)
    assert hmap2[(3, 3)] == 0.0, f"Custom unreachable should be 0.0, got {hmap2[(3, 3)]}"

    # Large unreachable value
    hmap3 = dijkstra.to_heightmap(unreachable=999.0)
    assert hmap3[(3, 3)] == 999.0, f"Large unreachable should be 999.0, got {hmap3[(3, 3)]}"

    print("test_unreachable_cells PASSED")

def test_custom_size():
    """Test custom size parameter."""
    grid = mcrfpy.Grid(grid_size=(10, 10))

    for y in range(10):
        for x in range(10):
            grid.at((x, y)).walkable = True

    dijkstra = grid.get_dijkstra_map((5, 5))

    # Custom smaller size
    hmap = dijkstra.to_heightmap(size=(5, 5))

    # Verify dimensions via repr
    repr_str = repr(hmap)
    assert "5 x 5" in repr_str, f"Expected 5x5 heightmap, got {repr_str}"

    # Values within dijkstra bounds should work
    assert hmap[(0, 0)] == dijkstra.distance((0, 0)), "Heights should match distances within bounds"

    print("test_custom_size PASSED")

def test_larger_custom_size():
    """Test custom size larger than dijkstra bounds."""
    grid = mcrfpy.Grid(grid_size=(5, 5))

    for y in range(5):
        for x in range(5):
            grid.at((x, y)).walkable = True

    dijkstra = grid.get_dijkstra_map((2, 2))

    # Custom larger size - cells outside dijkstra bounds get unreachable value
    hmap = dijkstra.to_heightmap(size=(10, 10), unreachable=-99.0)

    # Values within dijkstra bounds should work
    assert hmap[(2, 2)] == 0.0, "Root should have height 0"

    # Values outside bounds should have unreachable value
    assert hmap[(8, 8)] == -99.0, f"Outside bounds should be -99.0, got {hmap[(8, 8)]}"

    print("test_larger_custom_size PASSED")

def test_distance_values():
    """Test that heightmap values match dijkstra distances."""
    grid = mcrfpy.Grid(grid_size=(10, 10))

    for y in range(10):
        for x in range(10):
            grid.at((x, y)).walkable = True

    dijkstra = grid.get_dijkstra_map((0, 0))
    hmap = dijkstra.to_heightmap()

    # Check various positions
    for pos in [(0, 0), (1, 0), (0, 1), (5, 5), (9, 9)]:
        dist = dijkstra.distance(pos)
        height = hmap[pos]
        assert abs(dist - height) < 0.001, f"At {pos}: height {height} != distance {dist}"

    print("test_distance_values PASSED")

# Run all tests
test_basic_conversion()
test_unreachable_cells()
test_custom_size()
test_larger_custom_size()
test_distance_values()

print("\nAll DijkstraMap.to_heightmap tests PASSED")
sys.exit(0)
