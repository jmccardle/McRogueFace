#!/usr/bin/env python3
"""Test for Entity class - Related to issue #73 (index() method)"""
import mcrfpy
import sys

print("Test script starting...")

failures = []

def check(cond, msg):
    if cond:
        print(f":) {msg}")
    else:
        print(f"X {msg}")
        failures.append(msg)

def test_Entity():
    """Test Entity class and index() method for collection removal"""
    # Create test scene with grid
    entity_test = mcrfpy.Scene("entity_test")
    entity_test.activate()
    ui = entity_test.children

    # Create a grid (current ctor: grid_size/pos/size keywords)
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(10, 10), size=(400, 400),
                       texture=texture)
    ui.append(grid)
    entities = grid.entities

    # Create multiple entities (current ctor: grid_pos=, texture=, sprite_index=)
    entity1 = mcrfpy.Entity(grid_pos=(2, 2), texture=texture, sprite_index=0)
    entity2 = mcrfpy.Entity(grid_pos=(5, 5), texture=texture, sprite_index=1)
    entity3 = mcrfpy.Entity(grid_pos=(7, 7), texture=texture, sprite_index=2)

    entities.append(entity1)
    entities.append(entity2)
    entities.append(entity3)

    print(f"Created {len(entities)} entities")
    check(len(entities) == 3, "3 entities in collection after append")

    # Test entity properties
    print(f" Entity1 grid_pos: {entity1.grid_pos}")
    print(f" Entity1 pos: {entity1.pos}")
    print(f" Entity1 draw_pos: {entity1.draw_pos}")
    print(f" Entity1 sprite_index: {entity1.sprite_index}")
    check(entity1.sprite_index == 0, "entity1.sprite_index reads back as 0")
    check((entity1.grid_pos.x, entity1.grid_pos.y) == (2, 2),
          "entity1.grid_pos reads back as (2, 2)")

    # Modify properties
    entity1.grid_pos = mcrfpy.Vector(3, 3)
    entity1.sprite_index = 5
    check((entity1.grid_pos.x, entity1.grid_pos.y) == (3, 3),
          "entity1.grid_pos writable")
    check(entity1.sprite_index == 5, "entity1.sprite_index writable")

    # Entity association with a grid: entity.grid is the shared GridData
    # (current contract, #313/#361 -- it is NOT the Grid view object)
    check(isinstance(entity1.grid, mcrfpy.GridData),
          "entity.grid returns the GridData")
    check(entity1.grid is grid.grid_data,
          "entity.grid is the same GridData as grid.grid_data")

    # Test perspective/visibility access (was: entity.gridstate)
    pmap = entity2.perspective_map
    check(pmap is not None, "Entity perspective_map accessible")
    entity2.update_visibility()

    # Test at() method - returns the GridPoint if visible to this entity
    point_state = entity2.at(5, 5)
    check(point_state is not None, "Entity at() returns own (visible) cell")
    check(point_state is None or tuple(point_state.grid_pos) == (5, 5),
          "Entity at(5, 5) returns the GridPoint for (5, 5)")

    # Test index() method (Issue #73)
    print("\nTesting index() method (Issue #73)...")
    index = entity2.index()
    print(f":) index() method works: entity2 is at index {index}")
    check(index == 1, "entity2.index() == 1")
    check(entities[index] == entity2, "Index is correct (entities[index] is entity2)")

    # Remove using the index reported by index() (Issue #73's purpose)
    removed = entities.pop(index)
    check(removed == entity2, "pop(index) returned entity2")
    check(len(entities) == 2, f"Removed entity using index, now {len(entities)} entities")
    check(entity1.index() == 0 and entity3.index() == 1,
          "index() reflects collection after removal")

    # Test EntityCollection iteration
    positions = [e.grid_pos for e in entities]
    check(len(positions) == 2, f"Entity iteration works: {len(positions)} entities")
    check([(p.x, p.y) for p in positions] == [(3, 3), (7, 7)],
          "Iteration yields the surviving entities in order")

    # Test EntityCollection extend (Issue #27)
    new_entities = [
        mcrfpy.Entity(grid_pos=(1, 1), texture=texture, sprite_index=3),
        mcrfpy.Entity(grid_pos=(9, 9), texture=texture, sprite_index=4)
    ]
    entities.extend(new_entities)
    check(len(entities) == 4, f"extend() method works: now {len(entities)} entities")
    check(new_entities[1].index() == 3, "extended entity reports its index()")

    # remove(entity) is the object-based counterpart to index()/pop()
    entities.remove(entity3)
    check(len(entities) == 3, "remove(entity) drops the entity")


# Run test immediately in headless mode
print("Running test immediately...")
test_Entity()
print("Test completed.")

if failures:
    print(f"FAIL: {len(failures)} check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("PASS")
sys.exit(0)
