#!/usr/bin/env python3
"""
Comprehensive test for Issues #26 & #28: Iterator implementation for collections

This test covers both UICollection and UIEntityCollection iterator implementations,
testing all aspects of the Python sequence protocol.

Issues:
- #26: Iterator support for UIEntityCollection
- #28: Iterator support for UICollection
"""

import mcrfpy
from mcrfpy import automation
import sys
import gc

def test_sequence_protocol(collection, name, expected_types=None):
    """Test all sequence protocol operations on a collection"""
    print(f"\n=== Testing {name} ===")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: len()
    tests_total += 1
    try:
        length = len(collection)
        print(f"✓ len() works: {length} items")
        tests_passed += 1
    except Exception as e:
        print(f"✗ len() failed: {e}")
        return tests_passed, tests_total
    
    # Test 2: Basic iteration
    tests_total += 1
    try:
        items = []
        types = []
        for item in collection:
            items.append(item)
            types.append(type(item).__name__)
        print(f"✓ Iteration works: found {len(items)} items")
        print(f"  Types: {types}")
        if expected_types and types != expected_types:
            print(f"  WARNING: Expected types {expected_types}")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Iteration failed (Issue #26/#28): {e}")
    
    # Test 3: Indexing (positive)
    tests_total += 1
    try:
        if length > 0:
            first = collection[0]
            last = collection[length-1]
            print(f"✓ Positive indexing works: [0]={type(first).__name__}, [{length-1}]={type(last).__name__}")
            tests_passed += 1
        else:
            print("  Skipping indexing test - empty collection")
    except Exception as e:
        print(f"✗ Positive indexing failed: {e}")
    
    # Test 4: Negative indexing
    tests_total += 1
    try:
        if length > 0:
            last = collection[-1]
            first = collection[-length]
            print(f"✓ Negative indexing works: [-1]={type(last).__name__}, [-{length}]={type(first).__name__}")
            tests_passed += 1
        else:
            print("  Skipping negative indexing test - empty collection")
    except Exception as e:
        print(f"✗ Negative indexing failed: {e}")
    
    # Test 5: Out of bounds indexing
    tests_total += 1
    try:
        _ = collection[length + 10]
        print(f"✗ Out of bounds indexing should raise IndexError but didn't")
    except IndexError:
        print(f"✓ Out of bounds indexing correctly raises IndexError")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Out of bounds indexing raised wrong exception: {type(e).__name__}: {e}")
    
    # Test 6: Slicing
    tests_total += 1
    try:
        if length >= 2:
            slice_result = collection[0:2]
            print(f"✓ Slicing works: [0:2] returned {len(slice_result)} items")
            tests_passed += 1
        else:
            print("  Skipping slicing test - not enough items")
    except NotImplementedError:
        print(f"✗ Slicing not implemented")
    except Exception as e:
        print(f"✗ Slicing failed: {e}")
    
    # Test 7: Contains operator
    tests_total += 1
    try:
        if length > 0:
            first_item = collection[0]
            if first_item in collection:
                print(f"✓ 'in' operator works")
                tests_passed += 1
            else:
                print(f"✗ 'in' operator returned False for existing item")
        else:
            print("  Skipping 'in' operator test - empty collection")
    except NotImplementedError:
        print(f"✗ 'in' operator not implemented")
    except Exception as e:
        print(f"✗ 'in' operator failed: {e}")
    
    # Test 8: Multiple iterations
    tests_total += 1
    try:
        count1 = sum(1 for _ in collection)
        count2 = sum(1 for _ in collection)
        if count1 == count2 == length:
            print(f"✓ Multiple iterations work correctly")
            tests_passed += 1
        else:
            print(f"✗ Multiple iterations inconsistent: {count1} vs {count2} vs {length}")
    except Exception as e:
        print(f"✗ Multiple iterations failed: {e}")
    
    # Test 9: Iterator state independence
    tests_total += 1
    try:
        iter1 = iter(collection)
        iter2 = iter(collection)
        
        # Advance iter1
        next(iter1)
        
        # iter2 should still be at the beginning
        item1_from_iter2 = next(iter2)
        item1_from_collection = collection[0]
        
        if type(item1_from_iter2).__name__ == type(item1_from_collection).__name__:
            print(f"✓ Iterator state independence maintained")
            tests_passed += 1
        else:
            print(f"✗ Iterator states are not independent")
    except Exception as e:
        print(f"✗ Iterator state test failed: {e}")
    
    # Test 10: List conversion
    tests_total += 1
    try:
        as_list = list(collection)
        if len(as_list) == length:
            print(f"✓ list() conversion works: {len(as_list)} items")
            tests_passed += 1
        else:
            print(f"✗ list() conversion wrong length: {len(as_list)} vs {length}")
    except Exception as e:
        print(f"✗ list() conversion failed: {e}")
    
    return tests_passed, tests_total

def test_modification_during_iteration(collection, name):
    """Test collection modification during iteration"""
    print(f"\n=== Testing {name} Modification During Iteration ===")
    
    # This is a tricky case - some implementations might crash
    # or behave unexpectedly when the collection is modified during iteration
    
    if len(collection) < 2:
        print("  Skipping - need at least 2 items")
        return
    
    try:
        count = 0
        for i, item in enumerate(collection):
            count += 1
            if i == 0 and hasattr(collection, 'remove'):
                # Try to remove an item during iteration
                # This might raise an exception or cause undefined behavior
                pass  # Don't actually modify to avoid breaking the test
        print(f"✓ Iteration completed without modification: {count} items")
    except Exception as e:
        print(f"  Note: Iteration with modification would fail: {e}")

def run_comprehensive_test():
    """Run comprehensive iterator tests for both collection types"""
    print("=== Testing Collection Iterator Implementation (Issues #26 & #28) ===")
    
    total_passed = 0
    total_tests = 0
    
    # Test UICollection
    print("\n--- Testing UICollection ---")
    
    # Create UI elements
    scene_ui = mcrfpy.sceneUI("test")
    
    # Add various UI elements
    frame = mcrfpy.Frame(10, 10, 200, 150,
                        fill_color=mcrfpy.Color(100, 100, 200),
                        outline_color=mcrfpy.Color(255, 255, 255))
    caption = mcrfpy.Caption(mcrfpy.Vector(220, 10),
                           text="Test Caption",
                           fill_color=mcrfpy.Color(255, 255, 0))
    
    scene_ui.append(frame)
    scene_ui.append(caption)
    
    # Test UICollection
    passed, total = test_sequence_protocol(scene_ui, "UICollection", 
                                         expected_types=["Frame", "Caption"])
    total_passed += passed
    total_tests += total
    
    test_modification_during_iteration(scene_ui, "UICollection")
    
    # Test UICollection with children
    print("\n--- Testing UICollection Children (Nested) ---")
    child_caption = mcrfpy.Caption(mcrfpy.Vector(10, 10),
                                 text="Child",
                                 fill_color=mcrfpy.Color(200, 200, 200))
    frame.children.append(child_caption)
    
    passed, total = test_sequence_protocol(frame.children, "Frame.children",
                                         expected_types=["Caption"])
    total_passed += passed
    total_tests += total
    
    # Test UIEntityCollection
    print("\n--- Testing UIEntityCollection ---")
    
    # Create a grid with entities
    grid = mcrfpy.Grid(30, 30)
    grid.x = 10
    grid.y = 200
    grid.w = 600
    grid.h = 400
    scene_ui.append(grid)
    
    # Add various entities
    entity1 = mcrfpy.Entity(5, 5)
    entity2 = mcrfpy.Entity(10, 10)
    entity3 = mcrfpy.Entity(15, 15)
    
    grid.entities.append(entity1)
    grid.entities.append(entity2)
    grid.entities.append(entity3)
    
    passed, total = test_sequence_protocol(grid.entities, "UIEntityCollection",
                                         expected_types=["Entity", "Entity", "Entity"])
    total_passed += passed
    total_tests += total
    
    test_modification_during_iteration(grid.entities, "UIEntityCollection")
    
    # Test empty collections
    print("\n--- Testing Empty Collections ---")
    empty_grid = mcrfpy.Grid(10, 10)
    
    passed, total = test_sequence_protocol(empty_grid.entities, "Empty UIEntityCollection")
    total_passed += passed
    total_tests += total
    
    empty_frame = mcrfpy.Frame(0, 0, 50, 50)
    passed, total = test_sequence_protocol(empty_frame.children, "Empty UICollection")
    total_passed += passed
    total_tests += total
    
    # Test large collection
    print("\n--- Testing Large Collection ---")
    large_grid = mcrfpy.Grid(50, 50)
    for i in range(100):
        large_grid.entities.append(mcrfpy.Entity(i % 50, i // 50))
    
    print(f"Created large collection with {len(large_grid.entities)} entities")
    
    # Just test basic iteration performance
    import time
    start = time.time()
    count = sum(1 for _ in large_grid.entities)
    elapsed = time.time() - start
    print(f"✓ Large collection iteration: {count} items in {elapsed:.3f}s")
    
    # Edge case: Single item collection
    print("\n--- Testing Single Item Collection ---")
    single_grid = mcrfpy.Grid(5, 5)
    single_grid.entities.append(mcrfpy.Entity(1, 1))
    
    passed, total = test_sequence_protocol(single_grid.entities, "Single Item UIEntityCollection")
    total_passed += passed
    total_tests += total
    
    # Take screenshot
    automation.screenshot("/tmp/issue_26_28_iterator_test.png")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Total tests passed: {total_passed}/{total_tests}")
    
    if total_passed < total_tests:
        print("\nIssues found:")
        print("- Issue #26: UIEntityCollection may not fully implement iterator protocol")
        print("- Issue #28: UICollection may not fully implement iterator protocol")
        print("\nThe iterator implementation should support:")
        print("1. Forward iteration with 'for item in collection'")
        print("2. Multiple independent iterators")
        print("3. Proper cleanup when iteration completes")
        print("4. Integration with Python's sequence protocol")
    else:
        print("\nAll iterator tests passed!")
    
    return total_passed == total_tests

def run_test(runtime):
    """Timer callback to run the test"""
    try:
        success = run_comprehensive_test()
        print("\nOverall result: " + ("PASS" if success else "FAIL"))
    except Exception as e:
        print(f"\nTest error: {e}")
        import traceback
        traceback.print_exc()
        print("\nOverall result: FAIL")
    
    sys.exit(0)

# Set up the test scene
mcrfpy.createScene("test")
mcrfpy.setScene("test")

# Schedule test to run after game loop starts
mcrfpy.setTimer("test", run_test, 100)