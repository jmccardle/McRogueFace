#!/usr/bin/env python3
"""
Test TCOD Field of View with Two Entities
==========================================

Demonstrates:
1. Grid with obstacles (walls)
2. Two entities at different positions
3. Entity-specific FOV calculation
4. Color layer for FOV visualization (new API)
"""

import mcrfpy
import sys

def run_tests():
    """Run FOV entity tests"""
    print("=== TCOD FOV Entity Tests ===\n")

    # Test 1: FOV enum availability
    print("Test 1: FOV Enum")
    try:
        print(f"  FOV.BASIC = {mcrfpy.FOV.BASIC}")
        print(f"  FOV.SHADOW = {mcrfpy.FOV.SHADOW}")
        print("OK: FOV enum available\n")
    except Exception as e:
        print(f"FAIL: FOV enum not available: {e}")
        return False

    # Test 2: Create grid with walls
    print("Test 2: Grid Creation with Walls")
    grid = mcrfpy.Grid(pos=(0, 0), size=(640, 400), grid_size=(40, 25))

    # Set up walls
    for y in range(25):
        for x in range(40):
            point = grid.at(x, y)
            # Border walls
            if x == 0 or x == 39 or y == 0 or y == 24:
                point.walkable = False
                point.transparent = False
            # Central wall
            elif x == 20 and y != 12:  # Wall with door at y=12
                point.walkable = False
                point.transparent = False
            else:
                point.walkable = True
                point.transparent = True

    print("OK: Grid with walls created\n")

    # Test 3: Create entities
    print("Test 3: Entity Creation")
    player = mcrfpy.Entity((5, 12))
    enemy = mcrfpy.Entity((35, 12))
    grid.entities.append(player)
    grid.entities.append(enemy)
    print(f"  Player at grid ({player.grid_x}, {player.grid_y})")
    print(f"  Enemy at grid ({enemy.grid_x}, {enemy.grid_y})")
    print("OK: Entities created\n")

    # Test 4: FOV calculation for player
    print("Test 4: Player FOV Calculation")
    grid.compute_fov((player.grid_x, player.grid_y), radius=15, algorithm=mcrfpy.FOV.SHADOW)

    # Player should see themselves
    assert grid.is_in_fov(player.grid_x, player.grid_y), "Player should see themselves"
    print("  Player can see their own position")

    # Player should see nearby cells
    assert grid.is_in_fov(6, 12), "Player should see adjacent cells"
    print("  Player can see adjacent cells")

    # Player should NOT see behind the wall (outside door line)
    assert not grid.is_in_fov(21, 5), "Player should not see behind wall"
    print("  Player cannot see behind wall at (21, 5)")

    # Player should NOT see enemy (behind wall even with door)
    assert not grid.is_in_fov(enemy.grid_x, enemy.grid_y), "Player should not see enemy"
    print("  Player cannot see enemy")

    print("OK: Player FOV working correctly\n")

    # Test 5: FOV calculation for enemy
    print("Test 5: Enemy FOV Calculation")
    grid.compute_fov((enemy.grid_x, enemy.grid_y), radius=15, algorithm=mcrfpy.FOV.SHADOW)

    # Enemy should see themselves
    assert grid.is_in_fov(enemy.grid_x, enemy.grid_y), "Enemy should see themselves"
    print("  Enemy can see their own position")

    # Enemy should NOT see player (behind wall)
    assert not grid.is_in_fov(player.grid_x, player.grid_y), "Enemy should not see player"
    print("  Enemy cannot see player")

    print("OK: Enemy FOV working correctly\n")

    # Test 6: FOV with color layer
    print("Test 6: FOV Color Layer Visualization")
    fov_layer = mcrfpy.ColorLayer(z_index=-1, grid_size=(40, 25))
    grid.add_layer(fov_layer)
    fov_layer.fill((0, 0, 0, 255))  # Start with black (unknown)

    # Draw player FOV
    fov_layer.draw_fov(
        source=(player.grid_x, player.grid_y),
        radius=10,
        fov=mcrfpy.FOV.SHADOW,
        visible=(255, 255, 200, 64),
        discovered=(100, 100, 100, 128),
        unknown=(0, 0, 0, 255)
    )

    # Check visible cell
    visible_cell = fov_layer.at(player.grid_x, player.grid_y)
    assert visible_cell.r == 255, "Player position should be visible"
    print("  Player position has visible color")

    # Check hidden cell (behind wall)
    hidden_cell = fov_layer.at(enemy.grid_x, enemy.grid_y)
    assert hidden_cell.r == 0, "Enemy position should be unknown"
    print("  Enemy position has unknown color")

    print("OK: FOV color layer working correctly\n")

    print("=== All FOV Entity Tests Passed! ===")
    return True

# Main execution
if __name__ == "__main__":
    try:
        if run_tests():
            print("\nPASS")
            sys.exit(0)
        else:
            print("\nFAIL")
            sys.exit(1)
    except Exception as e:
        print(f"\nFAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
