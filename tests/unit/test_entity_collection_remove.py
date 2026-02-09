#!/usr/bin/env python3
"""
Test for UIEntityCollection.remove() accepting Entity instances
Tests the new behavior where remove() takes an Entity object instead of an index
"""

import mcrfpy
import sys

def test_remove_by_entity():
    """Test removing entities by passing the entity object"""

    # Create a test scene and grid
    scene_name = "test_entity_remove"
    _scene = mcrfpy.Scene(scene_name)

    # Create a grid (entities need a grid)
    grid = mcrfpy.Grid(grid_size=(30, 30), pos=(0, 0), size=(300, 300))
    _scene.children.append(grid)

    # Get the entity collection
    entities = grid.entities

    # Create some test entities - position is set via constructor tuple (grid coords)
    # Entity.x/.y requires grid attachment, so append first, then check
    entity1 = mcrfpy.Entity((5, 5))
    entity2 = mcrfpy.Entity((10, 10))
    entity3 = mcrfpy.Entity((15, 15))

    # Add entities to the collection
    entities.append(entity1)
    entities.append(entity2)
    entities.append(entity3)

    print(f"Initial entity count: {len(entities)}")
    assert len(entities) == 3, "Should have 3 entities"

    # Test 1: Remove an entity that exists
    print("\nTest 1: Remove existing entity")
    entities.remove(entity2)
    assert len(entities) == 2, "Should have 2 entities after removal"
    assert entity1 in entities, "Entity1 should still be in collection"
    assert entity2 not in entities, "Entity2 should not be in collection"
    assert entity3 in entities, "Entity3 should still be in collection"
    print("  Successfully removed entity2")

    # Test 2: Try to remove an entity that's not in the collection
    print("\nTest 2: Remove non-existent entity")
    try:
        entities.remove(entity2)  # Already removed
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"  Got expected ValueError: {e}")

    # Test 3: Try to remove with wrong type
    print("\nTest 3: Remove with wrong type")
    try:
        entities.remove(42)  # Not an Entity
        assert False, "Should have raised TypeError"
    except TypeError as e:
        print(f"  Got expected TypeError: {e}")

    # Test 4: Try to remove with None
    print("\nTest 4: Remove with None")
    try:
        entities.remove(None)
        assert False, "Should have raised TypeError"
    except TypeError as e:
        print(f"  Got expected TypeError: {e}")

    # Test 5: Verify grid property is cleared (C++ internal)
    print("\nTest 5: Grid property handling")
    # Create a new entity and add it
    entity4 = mcrfpy.Entity((20, 20))
    entities.append(entity4)
    # Note: grid property is managed internally in C++ and not exposed to Python

    # Remove it - this clears the C++ grid reference internally
    entities.remove(entity4)
    print("  Grid property handling (managed internally in C++)")

    # Test 6: Remove all entities one by one
    print("\nTest 6: Remove all entities")
    entities.remove(entity1)
    entities.remove(entity3)
    assert len(entities) == 0, "Collection should be empty"
    print("  Successfully removed all entities")

    print("\nAll tests passed!")
    return True

if __name__ == "__main__":
    try:
        success = test_remove_by_entity()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
