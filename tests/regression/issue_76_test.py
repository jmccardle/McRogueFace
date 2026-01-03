#!/usr/bin/env python3
"""
Test for Issue #76: UIEntityCollection::getitem returns wrong type for derived classes

This test checks if derived Entity classes maintain their type when retrieved from collections.
"""

import mcrfpy
import sys

# Create a derived Entity class
class CustomEntity(mcrfpy.Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.custom_attribute = "I am custom!"

    def custom_method(self):
        return "Custom method called"

def run_test(runtime):
    """Test that derived entity classes maintain their type in collections"""
    try:
        # Create a grid
        grid = mcrfpy.Grid(grid_size=(10, 10))

        # Create instances of base and derived entities
        base_entity = mcrfpy.Entity((1, 1))
        custom_entity = CustomEntity((2, 2))
        
        # Add them to the grid's entity collection
        grid.entities.append(base_entity)
        grid.entities.append(custom_entity)
        
        # Retrieve them back
        retrieved_base = grid.entities[0]
        retrieved_custom = grid.entities[1]
        
        print(f"Base entity type: {type(retrieved_base)}")
        print(f"Custom entity type: {type(retrieved_custom)}")
        
        # Test 1: Check if base entity is correct type
        if type(retrieved_base).__name__ == "Entity":
            print("✓ Test 1 PASSED: Base entity maintains correct type")
        else:
            print("✗ Test 1 FAILED: Base entity has wrong type")
        
        # Test 2: Check if custom entity maintains its derived type
        if type(retrieved_custom).__name__ == "CustomEntity":
            print("✓ Test 2 PASSED: Derived entity maintains correct type")
            
            # Test 3: Check if custom attributes are preserved
            try:
                attr = retrieved_custom.custom_attribute
                method_result = retrieved_custom.custom_method()
                print(f"✓ Test 3 PASSED: Custom attributes preserved - {attr}, {method_result}")
            except AttributeError as e:
                print(f"✗ Test 3 FAILED: Custom attributes lost - {e}")
        else:
            print("✗ Test 2 FAILED: Derived entity type lost!")
            print("This is the bug described in Issue #76!")
            
            # Try to access custom attributes anyway
            try:
                attr = retrieved_custom.custom_attribute
                print(f"  - Has custom_attribute: {attr} (but wrong type)")
            except AttributeError:
                print("  - Lost custom_attribute")
        
        # Test 4: Check iteration
        print("\nTesting iteration:")
        for i, entity in enumerate(grid.entities):
            print(f"  Entity {i}: {type(entity).__name__}")
        
        print("\nTest complete")
        
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
    
    sys.exit(0)

# Set up the test scene
test = mcrfpy.Scene("test")
test.activate()

# Schedule test to run after game loop starts
mcrfpy.setTimer("test", run_test, 100)