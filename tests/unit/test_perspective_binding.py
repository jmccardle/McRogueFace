#!/usr/bin/env python3
"""
Test Perspective Binding System
===============================

Tests the integration between:
1. ColorLayer.apply_perspective() - binding a layer to an entity
2. entity.updateVisibility() - automatically updating bound layers
3. ColorLayer.clear_perspective() - removing the binding

This implements issue #113 requirements for "Agent POV Integration".
"""

import mcrfpy
import sys

def run_tests():
    """Run perspective binding tests"""
    print("=== Perspective Binding Tests ===\n")

    # Test 1: Create grid with entity and color layer
    print("Test 1: Setup")
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

    # Create player entity
    player = mcrfpy.Entity((5, 12))
    grid.entities.append(player)
    print(f"  Player at ({player.x}, {player.y})")
    print("  Grid setup complete")
    print()

    # Test 2: Apply perspective binding
    print("Test 2: Perspective Binding")
    fov_layer = mcrfpy.ColorLayer(z_index=-1, grid_size=(40, 25))
    grid.add_layer(fov_layer)
    fov_layer.fill((0, 0, 0, 255))  # Start with black (unknown)

    fov_layer.apply_perspective(
        entity=player,
        visible=(255, 255, 200, 64),
        discovered=(100, 100, 100, 128),
        unknown=(0, 0, 0, 255)
    )
    print("  Applied perspective to layer")

    # Check layer is bound
    # (We can't directly check internal state, but we can verify behavior)
    print()

    # Test 3: updateVisibility should update the bound layer
    print("Test 3: Entity updateVisibility")
    player.update_visibility()

    # Check that the player's position is now visible
    visible_cell = fov_layer.at(player.grid_x, player.grid_y)
    assert visible_cell.r == 255, f"Player position should be visible (got r={visible_cell.r})"
    print("  Player position has visible color after updateVisibility()")

    # Check that cells behind wall are unknown
    behind_wall = fov_layer.at(21, 5)
    assert behind_wall.r == 0, f"Behind wall should be unknown (got r={behind_wall.r})"
    print("  Cell behind wall is unknown")
    print()

    # Test 4: Moving entity and calling updateVisibility
    print("Test 4: Entity Movement with Perspective")

    # Move player through the door (use grid coordinates)
    player.grid_pos = (21, 12)
    player.update_visibility()

    # Now the player should see both sides of the wall
    # Check a cell that was previously hidden
    now_visible = fov_layer.at(25, 12)  # To the right of where player moved
    # This should now be visible (or discovered if was visible)
    assert now_visible.r in [255, 100], f"Cell should be visible or discovered (got r={now_visible.r})"
    print(f"  After moving to door, cell (25,12) has r={now_visible.r}")

    # Player's new position should be visible
    new_pos_color = fov_layer.at(player.grid_x, player.grid_y)
    assert new_pos_color.r == 255, f"New player position should be visible (got r={new_pos_color.r})"
    print(f"  Player's new position ({player.grid_x}, {player.grid_y}) is visible")
    print()

    # Test 5: Check discovered cells remain discovered
    print("Test 5: Discovered State Persistence")

    # Move player away from original position (use grid coordinates)
    player.grid_pos = (35, 12)
    player.update_visibility()

    # Original position (5, 12) should now be discovered (not visible, but was seen)
    original_pos = fov_layer.at(5, 12)
    # It could be visible if in line of sight, or discovered if not
    print(f"  Original position (5,12) color: r={original_pos.r}")
    print()

    # Test 6: Clear perspective
    print("Test 6: Clear Perspective")
    fov_layer.clear_perspective()

    # After clearing, updateVisibility should not affect this layer
    fov_layer.fill((128, 0, 128, 255))  # Fill with purple
    player.update_visibility()

    # Layer should still be purple (not modified by updateVisibility)
    check_cell = fov_layer.at(player.grid_x, player.grid_y)
    assert check_cell.r == 128, f"Layer should be unchanged after clear_perspective (got r={check_cell.r})"
    assert check_cell.g == 0, f"Layer should be unchanged (got g={check_cell.g})"
    assert check_cell.b == 128, f"Layer should be unchanged (got b={check_cell.b})"
    print("  Layer unchanged after clear_perspective()")
    print()

    # Test 7: Grid FOV settings
    print("Test 7: Grid FOV Settings Integration")

    # Create a new grid and layer to test FOV radius without discovered interference
    grid2 = mcrfpy.Grid(pos=(0, 0), size=(640, 400), grid_size=(40, 25))

    # Set all cells walkable/transparent
    for y in range(25):
        for x in range(40):
            point = grid2.at(x, y)
            point.walkable = True
            point.transparent = True

    # Create player entity
    player2 = mcrfpy.Entity((20, 12))
    grid2.entities.append(player2)

    # Set grid FOV settings
    grid2.fov = mcrfpy.FOV.SHADOW
    grid2.fov_radius = 5  # Smaller radius

    # Create layer and bind perspective
    fov_layer2 = mcrfpy.ColorLayer(z_index=-1, grid_size=(40, 25))
    grid2.add_layer(fov_layer2)
    fov_layer2.fill((0, 0, 0, 255))  # Start with black (unknown)

    fov_layer2.apply_perspective(
        entity=player2,
        visible=(255, 0, 0, 64),  # Red for visible
        discovered=(100, 100, 100, 128),
        unknown=(0, 0, 0, 255)
    )

    # Update visibility - this should only illuminate cells within radius 5
    player2.update_visibility()

    # With radius 5, cells far from player should be unknown (never discovered)
    far_cell = fov_layer2.at(30, 12)  # 10 cells away from player
    assert far_cell.r == 0, f"Far cell should be unknown with radius 5 (got r={far_cell.r})"
    print(f"  Far cell (30,12) is unknown with radius=5")

    # Near cell should be visible
    near_cell = fov_layer2.at(22, 12)  # 2 cells away
    assert near_cell.r == 255, f"Near cell should be visible (got r={near_cell.r})"
    print(f"  Near cell (22,12) is visible")
    print()

    # Test 8: visible_entities method
    print("Test 8: Entity.visible_entities()")

    # Create a grid with multiple entities
    grid3 = mcrfpy.Grid(pos=(0, 0), size=(640, 400), grid_size=(40, 25))

    # Set all cells transparent
    for y in range(25):
        for x in range(40):
            point = grid3.at(x, y)
            point.walkable = True
            point.transparent = True

    # Add a wall to block visibility
    for y in range(25):
        if y != 12:  # Door at y=12
            point = grid3.at(20, y)
            point.walkable = False
            point.transparent = False

    # Create entities
    player3 = mcrfpy.Entity((5, 12))  # Left side
    ally = mcrfpy.Entity((8, 12))  # Near player
    enemy1 = mcrfpy.Entity((35, 12))  # Behind wall
    enemy2 = mcrfpy.Entity((25, 12))  # Through door (should be visible)

    grid3.entities.append(player3)
    grid3.entities.append(ally)
    grid3.entities.append(enemy1)
    grid3.entities.append(enemy2)

    # Set grid FOV settings
    grid3.fov = mcrfpy.FOV.SHADOW
    grid3.fov_radius = 20

    # Get visible entities from player
    visible = player3.visible_entities()
    visible_positions = [(e.grid_x, e.grid_y) for e in visible]

    print(f"  Player at (5, 12)")
    print(f"  Visible entities: {visible_positions}")

    # Ally should be visible
    assert (8, 12) in visible_positions, "Ally at (8,12) should be visible"
    print("  Ally at (8, 12) is visible")

    # Enemy1 behind wall should NOT be visible
    assert (35, 12) not in visible_positions, "Enemy1 at (35,12) should NOT be visible (behind wall)"
    print("  Enemy1 at (35, 12) is NOT visible (behind wall)")

    # Enemy2 through door should be visible
    assert (25, 12) in visible_positions, "Enemy2 at (25,12) should be visible through door"
    print("  Enemy2 at (25, 12) is visible (through door)")
    print()

    # Test 9: visible_entities with radius override
    print("Test 9: visible_entities with radius override")

    # With small radius, only ally should be visible
    visible_small = player3.visible_entities(radius=4)
    visible_small_positions = [(e.grid_x, e.grid_y) for e in visible_small]

    print(f"  With radius=4: {visible_small_positions}")
    assert (8, 12) in visible_small_positions, "Ally should be visible with radius=4"
    assert (25, 12) not in visible_small_positions, "Enemy2 should NOT be visible with radius=4"
    print("  Correctly limited visibility to nearby entities")
    print()

    print("=== All Perspective Binding Tests Passed! ===")
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
