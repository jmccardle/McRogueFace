#!/usr/bin/env python3
"""
Test for Python object cache - verifies that derived Python classes
maintain their identity when stored in and retrieved from collections.

Issue #112: Object Splitting - Preserve Python derived types in collections
"""

import mcrfpy
import sys

# Test setup
test_passed = True
test_results = []

def test(condition, message):
    global test_passed
    if condition:
        test_results.append(f"✓ {message}")
    else:
        test_results.append(f"✗ {message}")
        test_passed = False

def run_tests(runtime):
    """Timer callback to run tests after game loop starts"""
    global test_passed
    
    print("\n=== Testing Python Object Cache ===")
    
    # Test 1: Create derived Frame class
    class MyFrame(mcrfpy.Frame):
        def __init__(self, x=0, y=0):
            super().__init__(pos=(x, y), size=(100, 100))
            self.custom_data = "I am a custom frame"
            self.test_value = 42
    
    # Test 2: Create instance and add to scene
    frame = MyFrame(50, 50)
    scene_ui = mcrfpy.sceneUI("test_scene")
    scene_ui.append(frame)
    
    # Test 3: Retrieve from collection and check type
    retrieved = scene_ui[0]
    test(type(retrieved) == MyFrame, "Retrieved object maintains derived type")
    test(isinstance(retrieved, MyFrame), "isinstance check passes")
    test(hasattr(retrieved, 'custom_data'), "Custom attribute exists")
    if hasattr(retrieved, 'custom_data'):
        test(retrieved.custom_data == "I am a custom frame", "Custom attribute value preserved")
    if hasattr(retrieved, 'test_value'):
        test(retrieved.test_value == 42, "Numeric attribute value preserved")
    
    # Test 4: Check object identity (same Python object)
    test(retrieved is frame, "Retrieved object is the same Python object")
    test(id(retrieved) == id(frame), "Object IDs match")
    
    # Test 5: Multiple retrievals return same object
    retrieved2 = scene_ui[0]
    test(retrieved2 is retrieved, "Multiple retrievals return same object")
    
    # Test 6: Test with other UI types
    class MySprite(mcrfpy.Sprite):
        def __init__(self):
            # Use default texture by passing None
            super().__init__(texture=None, sprite_index=0)
            self.sprite_data = "custom sprite"
    
    sprite = MySprite()
    sprite.x = 200
    sprite.y = 200
    scene_ui.append(sprite)
    
    retrieved_sprite = scene_ui[1]
    test(type(retrieved_sprite) == MySprite, "Sprite maintains derived type")
    if hasattr(retrieved_sprite, 'sprite_data'):
        test(retrieved_sprite.sprite_data == "custom sprite", "Sprite custom data preserved")
    
    # Test 7: Test with Caption
    class MyCaption(mcrfpy.Caption):
        def __init__(self, text):
            # Use default font by passing None
            super().__init__(text=text, font=None)
            self.caption_id = "test_caption"
    
    caption = MyCaption("Test Caption")
    caption.x = 10
    caption.y = 10
    scene_ui.append(caption)
    
    retrieved_caption = scene_ui[2]
    test(type(retrieved_caption) == MyCaption, "Caption maintains derived type")
    if hasattr(retrieved_caption, 'caption_id'):
        test(retrieved_caption.caption_id == "test_caption", "Caption custom data preserved")
    
    # Test 8: Test removal and re-addition
    # Use del to remove by index (Python standard), or .remove(element) to remove by value
    print(f"before remove: {len(scene_ui)=}")
    del scene_ui[-1]  # Remove last element by index
    print(f"after remove: {len(scene_ui)=}")

    scene_ui.append(frame)
    retrieved3 = scene_ui[-1]  # Get last element
    test(retrieved3 is frame, "Object identity preserved after removal/re-addition")
    
    # Test 9: Test with Grid
    class MyGrid(mcrfpy.Grid):
        def __init__(self, w, h):
            super().__init__(grid_size=(w, h))
            self.grid_name = "custom_grid"
    
    grid = MyGrid(10, 10)
    grid.x = 300
    grid.y = 100
    scene_ui.append(grid)
    
    retrieved_grid = scene_ui[-1]
    test(type(retrieved_grid) == MyGrid, "Grid maintains derived type")
    if hasattr(retrieved_grid, 'grid_name'):
        test(retrieved_grid.grid_name == "custom_grid", "Grid custom data preserved")
    
    # Test 10: Test with nested collections (Frame with children)
    parent = MyFrame(400, 400)
    child = MyFrame(10, 10)
    child.custom_data = "I am a child"
    parent.children.append(child)
    scene_ui.append(parent)
    
    retrieved_parent = scene_ui[-1]
    test(type(retrieved_parent) == MyFrame, "Parent frame maintains type")
    if len(retrieved_parent.children) > 0:
        retrieved_child = retrieved_parent.children[0]
        test(type(retrieved_child) == MyFrame, "Child frame maintains type in nested collection")
        if hasattr(retrieved_child, 'custom_data'):
            test(retrieved_child.custom_data == "I am a child", "Child custom data preserved")
    
    # Print results
    print("\n=== Test Results ===")
    for result in test_results:
        print(result)
    
    print(f"\n{'PASS' if test_passed else 'FAIL'}: {sum(1 for r in test_results if r.startswith('✓'))}/{len(test_results)} tests passed")
    
    sys.exit(0 if test_passed else 1)

# Create test scene
mcrfpy.createScene("test_scene")
mcrfpy.setScene("test_scene")

# Schedule tests to run after game loop starts
mcrfpy.setTimer("test", run_tests, 100)

print("Python object cache test initialized. Running tests...")
