# pathfinding_3d_test.py - Unit tests for 3D pathfinding
# Tests A* pathfinding on VoxelPoint navigation grid

import mcrfpy
import sys

def test_simple_path():
    """Test pathfinding on an open grid"""
    print("Testing simple pathfinding...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))
    viewport.grid_size = (10, 10)

    # Find path from corner to corner
    path = viewport.find_path((0, 0), (9, 9))

    # Should find a path
    assert len(path) > 0, "Expected a path, got empty list"

    # Path should end at destination (start is not included)
    assert path[-1] == (9, 9), f"Path should end at (9, 9), got {path[-1]}"

    # Path length should be reasonable (diagonal allows shorter paths)
    # Manhattan distance is 18, but with diagonals it can be ~9-14 steps
    assert len(path) >= 9 and len(path) <= 18, f"Path length {len(path)} is unexpected"

    print(f"  PASS: Simple pathfinding ({len(path)} steps)")


def test_path_with_obstacles():
    """Test pathfinding around obstacles"""
    print("Testing pathfinding with obstacles...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))
    viewport.grid_size = (10, 10)

    # Create a wall blocking direct path
    # Wall from (4, 0) to (4, 8)
    for z in range(9):
        viewport.at(4, z).walkable = False

    # Find path from left side to right side
    path = viewport.find_path((2, 5), (7, 5))

    # Should find a path (going around the wall via z=9)
    assert len(path) > 0, "Expected a path around the wall"

    # Verify path doesn't go through wall
    for x, z in path:
        if x == 4 and z < 9:
            assert False, f"Path goes through wall at ({x}, {z})"

    print(f"  PASS: Pathfinding with obstacles ({len(path)} steps)")


def test_no_path():
    """Test pathfinding when no path exists"""
    print("Testing no path scenario...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))
    viewport.grid_size = (10, 10)

    # Create a complete wall blocking all paths
    # Wall from (5, 0) to (5, 9) - blocks entire grid
    for z in range(10):
        viewport.at(5, z).walkable = False

    # Try to find path from left to right
    path = viewport.find_path((2, 5), (7, 5))

    # Should return empty list (no path)
    assert len(path) == 0, f"Expected empty path, got {len(path)} steps"

    print("  PASS: No path returns empty list")


def test_start_equals_end():
    """Test pathfinding when start equals end"""
    print("Testing start equals end...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))
    viewport.grid_size = (10, 10)

    # Find path to same location
    path = viewport.find_path((5, 5), (5, 5))

    # Should return empty path (already there)
    assert len(path) == 0, f"Expected empty path for start==end, got {len(path)} steps"

    print("  PASS: Start equals end")


def test_adjacent_path():
    """Test pathfinding to adjacent cell"""
    print("Testing adjacent cell pathfinding...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))
    viewport.grid_size = (10, 10)

    # Find path to adjacent cell
    path = viewport.find_path((5, 5), (5, 6))

    # Should be a single step
    assert len(path) == 1, f"Expected 1 step, got {len(path)}"
    assert path[0] == (5, 6), f"Expected (5, 6), got {path[0]}"

    print("  PASS: Adjacent cell pathfinding")


def test_heightmap_threshold():
    """Test apply_threshold sets walkability"""
    print("Testing HeightMap threshold...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))

    # Create a heightmap
    hm = mcrfpy.HeightMap((10, 10))

    # Set heights: left half low (0.2), right half high (0.8)
    for z in range(10):
        for x in range(5):
            hm[x, z] = 0.2
        for x in range(5, 10):
            hm[x, z] = 0.8

    # Initialize grid
    viewport.grid_size = (10, 10)

    # Apply threshold: mark high areas (>0.6) as unwalkable
    viewport.apply_threshold(hm, 0.6, 1.0, walkable=False)

    # Check left side is walkable
    assert viewport.at(2, 5).walkable == True, "Left side should be walkable"

    # Check right side is unwalkable
    assert viewport.at(7, 5).walkable == False, "Right side should be unwalkable"

    # Pathfinding should fail to cross
    path = viewport.find_path((2, 5), (7, 5))
    assert len(path) == 0, "Path should not exist through unwalkable terrain"

    print("  PASS: HeightMap threshold")


def test_slope_cost():
    """Test slope cost calculation"""
    print("Testing slope cost...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))
    viewport.grid_size = (10, 10)

    # Create terrain with a steep slope
    # Set heights manually
    for z in range(10):
        for x in range(10):
            viewport.at(x, z).height = 0.0

    # Create a cliff at x=5
    for z in range(10):
        for x in range(5, 10):
            viewport.at(x, z).height = 2.0  # 2.0 units high

    # Apply slope cost: max slope 0.5, mark steeper as unwalkable
    viewport.set_slope_cost(max_slope=0.5, cost_multiplier=2.0)

    # Check that cells at the cliff edge are marked unwalkable
    # Cell at (4, 5) borders (5, 5) which is 2.0 higher
    assert viewport.at(4, 5).walkable == False, "Cliff edge should be unwalkable"
    assert viewport.at(5, 5).walkable == False, "Cliff top edge should be unwalkable"

    # Cells away from cliff should still be walkable
    assert viewport.at(0, 5).walkable == True, "Flat area should be walkable"
    assert viewport.at(9, 5).walkable == True, "Flat high area should be walkable"

    print("  PASS: Slope cost")


def run_all_tests():
    """Run all unit tests"""
    print("=" * 60)
    print("3D Pathfinding Unit Tests")
    print("=" * 60)

    try:
        test_simple_path()
        test_path_with_obstacles()
        test_no_path()
        test_start_equals_end()
        test_adjacent_path()
        test_heightmap_threshold()
        test_slope_cost()

        print("=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)
        sys.exit(0)
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# Run tests
run_all_tests()
