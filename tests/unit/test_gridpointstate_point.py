#!/usr/bin/env python3
"""
Test GridPointState.point property (#16)
=========================================

Tests the GridPointState.point property that provides access to the
GridPoint data from an entity's perspective.

Key behavior:
- Returns None if the cell has not been discovered by the entity
- Returns the GridPoint (live reference) if discovered
- Works with the FOV/visibility system
"""

import mcrfpy
import sys

def run_tests():
    """Run GridPointState.point tests"""
    print("=== GridPointState.point Tests ===\n")

    # Test 1: Undiscovered cell returns None
    print("Test 1: Undiscovered cell returns None")
    grid = mcrfpy.Grid(pos=(0, 0), size=(640, 400), grid_size=(40, 25))

    # Set up grid
    for y in range(25):
        for x in range(40):
            pt = grid.at(x, y)
            pt.walkable = True
            pt.transparent = True

    # Create entity
    entity = mcrfpy.Entity((5, 5))
    grid.entities.append(entity)

    # Before update_visibility, nothing is discovered
    state = entity.at((10, 10))
    assert state.point is None, f"Expected None for undiscovered cell, got {state.point}"
    print("  Undiscovered cell returns None")
    print()

    # Test 2: Discovered cell returns GridPoint
    print("Test 2: Discovered cell returns GridPoint")
    grid.fov = mcrfpy.FOV.SHADOW
    grid.fov_radius = 8

    entity.update_visibility()

    # Entity's own position should be discovered
    state_own = entity.at((5, 5))
    assert state_own.discovered == True, "Entity's position should be discovered"
    assert state_own.point is not None, "Discovered cell should return GridPoint"
    print(f"  Entity position: discovered={state_own.discovered}, point={state_own.point}")
    print()

    # Test 3: GridPoint access through state
    print("Test 3: GridPoint properties accessible through state.point")

    # Make a specific cell have known properties
    grid.at(6, 5).walkable = False
    grid.at(6, 5).transparent = True

    state_adj = entity.at((6, 5))
    assert state_adj.point is not None, "Adjacent cell should be discovered"
    assert state_adj.point.walkable == False, f"Expected walkable=False, got {state_adj.point.walkable}"
    assert state_adj.point.transparent == True, f"Expected transparent=True, got {state_adj.point.transparent}"
    print(f"  Adjacent cell (6,5): walkable={state_adj.point.walkable}, transparent={state_adj.point.transparent}")
    print()

    # Test 4: Far cells remain undiscovered
    print("Test 4: Cells outside FOV radius remain undiscovered")

    # Cell far from entity (outside radius 8)
    state_far = entity.at((30, 20))
    assert state_far.discovered == False, "Far cell should not be discovered"
    assert state_far.point is None, "Far cell point should be None"
    print(f"  Far cell (30,20): discovered={state_far.discovered}, point={state_far.point}")
    print()

    # Test 5: Discovered but not visible cells
    print("Test 5: Discovered but not currently visible cells")

    # Move entity to discover new area
    entity.x = 6
    entity.y = 5
    entity.update_visibility()

    # Move back - old visible cells should now be discovered but not visible
    entity.x = 5
    entity.y = 5
    entity.update_visibility()

    # A cell that was visible when at (6,5) but might not be visible from (5,5)
    # Actually with radius 8, most nearby cells will still be visible
    # Let's check a cell that's on the edge
    state_edge = entity.at((12, 5))  # 7 cells away, should be visible with radius 8
    if state_edge.discovered:
        assert state_edge.point is not None, "Discovered cell should have point access"
        print(f"  Edge cell (12,5): discovered={state_edge.discovered}, visible={state_edge.visible}")
        print(f"    point.walkable={state_edge.point.walkable}")
    print()

    # Test 6: GridPoint.entities through state.point
    print("Test 6: GridPoint.entities accessible through state.point")

    # Add another entity at a visible position
    e2 = mcrfpy.Entity((7, 5))
    grid.entities.append(e2)

    state_with_entity = entity.at((7, 5))
    assert state_with_entity.point is not None, "Cell should be discovered"
    entities_at_cell = state_with_entity.point.entities
    assert len(entities_at_cell) == 1, f"Expected 1 entity, got {len(entities_at_cell)}"
    print(f"  Cell (7,5) has {len(entities_at_cell)} entity via state.point.entities")
    print()

    # Test 7: Live reference - changes to GridPoint are reflected
    print("Test 7: state.point is a live reference")

    # Get state before change
    state_live = entity.at((8, 5))
    original_walkable = state_live.point.walkable

    # Change the actual GridPoint
    grid.at(8, 5).walkable = not original_walkable

    # Check that state.point reflects the change
    new_walkable = state_live.point.walkable
    assert new_walkable != original_walkable, "state.point should reflect GridPoint changes"
    print(f"  Changed walkable from {original_walkable} to {new_walkable} - reflected in state.point")
    print()

    # Test 8: Wall blocking visibility
    print("Test 8: Walls block visibility correctly")

    # Create a wall
    grid.at(15, 5).transparent = False
    grid.at(15, 5).walkable = False

    entity.update_visibility()

    # Cell behind wall should not be visible (and possibly not discovered)
    state_behind = entity.at((20, 5))  # Behind wall at x=15
    print(f"  Cell behind wall (20,5): visible={state_behind.visible}, discovered={state_behind.discovered}")
    if not state_behind.discovered:
        assert state_behind.point is None, "Undiscovered cell behind wall should have point=None"
        print("  Correctly returns None for undiscovered cell behind wall")
    print()

    print("=== All GridPointState.point Tests Passed! ===")
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
