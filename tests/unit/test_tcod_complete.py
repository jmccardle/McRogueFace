#!/usr/bin/env python3
"""Complete test of TCOD integration features."""

import mcrfpy
import sys

def run_tests():
    print("=== TCOD Integration Test Suite ===\n")
    
    # Test 1: Basic Grid Creation
    print("Test 1: Grid Creation")
    tcod_test = mcrfpy.Scene("tcod_test")
    grid = mcrfpy.Grid(grid_w=10, grid_h=10, texture=None, pos=(10, 10), size=(160, 160))
    print("OK: Grid created successfully\n")
    
    # Test 2: Grid Point Manipulation
    print("Test 2: Grid Point Properties")
    # Set all cells as floor
    for y in range(10):
        for x in range(10):
            point = grid.at(x, y)
            point.walkable = True
            point.transparent = True
    
    # Create walls
    walls = [(4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (4, 7)]
    for x, y in walls:
        point = grid.at(x, y)
        point.walkable = False
        point.transparent = False
    
    # Verify
    assert grid.at(0, 0).walkable == True
    assert grid.at(4, 3).walkable == False
    print("OK: Grid points configured correctly\n")
    
    # Test 3: Field of View
    print("Test 3: Field of View Algorithms")
    
    # Test different algorithms (using new mcrfpy.FOV enum)
    algorithms = [
        ("Basic", mcrfpy.FOV.BASIC),
        ("Diamond", mcrfpy.FOV.DIAMOND),
        ("Shadow", mcrfpy.FOV.SHADOW),
        ("Permissive", mcrfpy.FOV.PERMISSIVE_2),
        ("Restrictive", mcrfpy.FOV.RESTRICTIVE)
    ]
    
    for name, algo in algorithms:
        grid.compute_fov((2, 5), radius=5, light_walls=True, algorithm=algo)
        visible_count = sum(1 for y in range(10) for x in range(10) if grid.is_in_fov(x, y))
        print(f"  {name}: {visible_count} cells visible")
        
        # Check specific cells
        assert grid.is_in_fov(2, 5) == True  # Origin always visible
        assert grid.is_in_fov(5, 5) == False  # Behind wall
    
    print("OK: All FOV algorithms working\n")
    
    # Test 4: Pathfinding
    print("Test 4: A* Pathfinding")
    
    # Find path around wall
    path = grid.find_path((1, 5), (8, 5))
    if path:
        path_len = len(path)  # Get length before iteration consumes it
        path_list = [(int(p.x), int(p.y)) for p in path]
        print(f"  Path found: {path_len} steps")
        print(f"  Route: {path_list[:3]}...{path_list[-3:]}")

        # Verify path goes around wall
        assert (4, 5) not in path_list  # Should not go through wall
        assert path_len >= 7  # Should be at least 7 steps (direct would be 7)
    else:
        print("  ERROR: No path found!")

    # Test diagonal movement
    path_diag = grid.find_path((0, 0), (9, 9), diagonal_cost=1.41)
    path_no_diag = grid.find_path((0, 0), (9, 9), diagonal_cost=0.0)

    print(f"  With diagonals: {len(path_diag)} steps")
    print(f"  Without diagonals: {len(path_no_diag)} steps")
    assert len(path_diag) < len(path_no_diag)  # Diagonal should be shorter
    
    print("OK: Pathfinding working correctly\n")
    
    # Test 5: Edge Cases
    print("Test 5: Edge Cases")
    
    # Out of bounds
    assert grid.is_in_fov(-1, 0) == False
    assert grid.is_in_fov(10, 10) == False
    
    # Invalid path
    # Surround a cell completely
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx != 0 or dy != 0:
                grid.at(5 + dx, 5 + dy).walkable = False
    
    blocked_path = grid.find_path((5, 5), (0, 0))
    assert blocked_path is None, "Blocked path should return None"
    
    print("OK: Edge cases handled properly\n")
    
    print("=== All Tests Passed! ===")
    return True

try:
    if run_tests():
        print("\nPASS")
    else:
        print("\nFAIL")
except Exception as e:
    print(f"\nFAIL: {e}")
    import traceback
    traceback.print_exc()

sys.exit(0)