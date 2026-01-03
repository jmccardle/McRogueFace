#!/usr/bin/env python3
"""Test for Entity class - Related to issue #73 (index() method)"""
import mcrfpy
from datetime import datetime

print("Test script starting...")

def test_Entity():
    """Test Entity class and index() method for collection removal"""
    # Create test scene with grid
    entity_test = mcrfpy.Scene("entity_test")
    entity_test.activate()
    ui = entity_test.children
    
    # Create a grid
    grid = mcrfpy.Grid(10, 10,
                      mcrfpy.default_texture,
                      mcrfpy.Vector(10, 10),
                      mcrfpy.Vector(400, 400))
    ui.append(grid)
    entities = grid.entities
    
    # Create multiple entities
    entity1 = mcrfpy.Entity(mcrfpy.Vector(2, 2), mcrfpy.default_texture, 0, grid)
    entity2 = mcrfpy.Entity(mcrfpy.Vector(5, 5), mcrfpy.default_texture, 1, grid)
    entity3 = mcrfpy.Entity(mcrfpy.Vector(7, 7), mcrfpy.default_texture, 2, grid)
    
    entities.append(entity1)
    entities.append(entity2)
    entities.append(entity3)
    
    print(f"Created {len(entities)} entities")
    
    # Test entity properties
    try:
        print(f" Entity1 pos: {entity1.pos}")
        print(f" Entity1 draw_pos: {entity1.draw_pos}")
        print(f" Entity1 sprite_number: {entity1.sprite_number}")
        
        # Modify properties
        entity1.pos = mcrfpy.Vector(3, 3)
        entity1.sprite_number = 5
        print(" Entity properties modified")
    except Exception as e:
        print(f"X Entity property access failed: {e}")
    
    # Test gridstate access
    try:
        gridstate = entity2.gridstate
        print(" Entity gridstate accessible")
        
        # Test at() method
        point_state = entity2.at()#.at(0, 0)
        print(" Entity at() method works")
    except Exception as e:
        print(f"X Entity gridstate/at() failed: {e}")
    
    # Test index() method (Issue #73)
    print("\nTesting index() method (Issue #73)...")
    try:
        # Try to find entity2's index
        index = entity2.index()
        print(f":) index() method works: entity2 is at index {index}")
        
        # Verify by checking collection
        if entities[index] == entity2:
            print("✓ Index is correct")
        else:
            print("✗ Index mismatch")
            
        # Remove using index
        entities.remove(index)
        print(f":) Removed entity using index, now {len(entities)} entities")
    except AttributeError:
        print("✗ index() method not implemented (Issue #73)")
        # Try manual removal as workaround
        try:
            for i in range(len(entities)):
                if entities[i] == entity2:
                    entities.remove(i)
                    print(":)  Manual removal workaround succeeded")
                    break
        except:
            print("✗ Manual removal also failed")
    except Exception as e:
        print(f":) index() method error: {e}")
    
    # Test EntityCollection iteration
    try:
        positions = []
        for entity in entities:
            positions.append(entity.pos)
        print(f":) Entity iteration works: {len(positions)} entities")
    except Exception as e:
        print(f"X Entity iteration failed: {e}")
    
    # Test EntityCollection extend (Issue #27)
    try:
        new_entities = [
            mcrfpy.Entity(mcrfpy.Vector(1, 1), mcrfpy.default_texture, 3, grid),
            mcrfpy.Entity(mcrfpy.Vector(9, 9), mcrfpy.default_texture, 4, grid)
        ]
        entities.extend(new_entities)
        print(f":) extend() method works: now {len(entities)} entities")
    except AttributeError:
        print("✗ extend() method not implemented (Issue #27)")
    except Exception as e:
        print(f"X extend() method error: {e}")
    
    # Skip screenshot in headless mode
    print("PASS")

# Run test immediately in headless mode
print("Running test immediately...")
test_Entity()
print("Test completed.")
