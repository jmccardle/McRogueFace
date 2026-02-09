#!/usr/bin/env python3
"""Test Grid pathfinding methods with new position parsing.

Tests that Grid.find_path, Grid.compute_fov, etc. accept positions
in multiple formats: tuples, lists, Vectors.
"""
import mcrfpy
import sys

def run_tests():
    """Run all grid pathfinding position parsing tests."""
    print("Testing Grid pathfinding position parsing...")

    # Create a test grid
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(10, 10), texture=texture, pos=(0, 0), size=(320, 320))

    # Set up walkability: all cells walkable initially
    for y in range(10):
        for x in range(10):
            cell = grid.at((x, y))
            cell.walkable = True

    # Add a wall in the middle
    grid.at((5, 5)).walkable = False

    print("  Grid created with walkable cells and one wall at (5,5)")

    # ============ Test find_path ============
    print("\n  Testing find_path...")

    # Test with tuple positions
    path1 = grid.find_path((0, 0), (3, 3))
    assert path1 is not None, "find_path with tuples returned None"
    assert len(path1) > 0, "find_path with tuples returned empty path"
    print(f"    find_path((0,0), (3,3)) -> {len(path1)} steps: PASS")

    # Test with list positions
    path2 = grid.find_path([0, 0], [3, 3])
    assert path2 is not None, "find_path with lists returned None"
    assert len(path2) > 0, "find_path with lists returned empty path"
    print(f"    find_path([0,0], [3,3]) -> {len(path2)} steps: PASS")

    # Test with Vector positions
    start_vec = mcrfpy.Vector(0, 0)
    end_vec = mcrfpy.Vector(3, 3)
    path3 = grid.find_path(start_vec, end_vec)
    assert path3 is not None, "find_path with Vectors returned None"
    assert len(path3) > 0, "find_path with Vectors returned empty path"
    print(f"    find_path(Vector(0,0), Vector(3,3)) -> {len(path3)} steps: PASS")

    # Test path with diagonal_cost parameter
    path4 = grid.find_path((0, 0), (3, 3), diagonal_cost=1.41)
    assert path4 is not None, "find_path with diagonal_cost returned None"
    print(f"    find_path with diagonal_cost=1.41: PASS")

    # ============ Test compute_fov / is_in_fov ============
    print("\n  Testing compute_fov / is_in_fov...")

    # All cells transparent for FOV testing
    for y in range(10):
        for x in range(10):
            cell = grid.at((x, y))
            cell.transparent = True

    # Test compute_fov with tuple
    grid.compute_fov((5, 5), radius=5)
    print("    compute_fov((5,5), radius=5): PASS")

    # Test is_in_fov with tuple
    in_fov1 = grid.is_in_fov((5, 5))
    assert in_fov1 == True, "Center should be in FOV"
    print(f"    is_in_fov((5,5)) = {in_fov1}: PASS")

    # Test is_in_fov with list
    in_fov2 = grid.is_in_fov([4, 5])
    assert in_fov2 == True, "Adjacent cell should be in FOV"
    print(f"    is_in_fov([4,5]) = {in_fov2}: PASS")

    # Test is_in_fov with Vector
    pos_vec = mcrfpy.Vector(6, 5)
    in_fov3 = grid.is_in_fov(pos_vec)
    assert in_fov3 == True, "Adjacent cell should be in FOV"
    print(f"    is_in_fov(Vector(6,5)) = {in_fov3}: PASS")

    # Test compute_fov with Vector
    center_vec = mcrfpy.Vector(3, 3)
    grid.compute_fov(center_vec, radius=3)
    print("    compute_fov(Vector(3,3), radius=3): PASS")

    # Note: compute_dijkstra/get_dijkstra_* and compute_astar_path are tested
    # via integration tests in tests/integration/dijkstra_*.py

    print("\n" + "="*50)
    print("All grid pathfinding position tests PASSED!")
    print("="*50)
    return True

# Run tests
try:
    success = run_tests()
    if success:
        print("\nPASS")
        sys.exit(0)
except Exception as e:
    print(f"\nFAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
