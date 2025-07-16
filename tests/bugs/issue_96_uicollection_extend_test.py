#!/usr/bin/env python3
"""
Test for Issue #96: Add extend() method to UICollection

This test verifies that UICollection now has an extend() method similar to
UIEntityCollection.extend().
"""

import mcrfpy
import sys

def test_uicollection_extend():
    """Test UICollection extend method"""
    print("=== Testing UICollection extend() Method (Issue #96) ===\n")
    
    tests_passed = 0
    tests_total = 0
    
    # Get scene UI collection
    scene_ui = mcrfpy.sceneUI("test")
    
    # Test 1: Basic extend with list
    print("--- Test 1: Extend with list ---")
    tests_total += 1
    try:
        # Create a list of UI elements
        elements = [
            mcrfpy.Frame(10, 10, 100, 100),
            mcrfpy.Caption((150, 50), "Test1", mcrfpy.Font("assets/JetbrainsMono.ttf")),
            mcrfpy.Sprite(200, 100)
        ]
        
        # Extend the collection
        scene_ui.extend(elements)
        
        if len(scene_ui) == 3:
            print("✓ PASS: Extended collection with 3 elements")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Expected 3 elements, got {len(scene_ui)}")
    except Exception as e:
        print(f"✗ FAIL: Error extending with list: {e}")
    
    # Test 2: Extend with tuple
    print("\n--- Test 2: Extend with tuple ---")
    tests_total += 1
    try:
        # Create a tuple of UI elements
        more_elements = (
            mcrfpy.Grid(10, 10),
            mcrfpy.Frame(300, 10, 100, 100)
        )
        
        # Extend the collection
        scene_ui.extend(more_elements)
        
        if len(scene_ui) == 5:
            print("✓ PASS: Extended collection with tuple (now 5 elements)")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Expected 5 elements, got {len(scene_ui)}")
    except Exception as e:
        print(f"✗ FAIL: Error extending with tuple: {e}")
    
    # Test 3: Extend with generator
    print("\n--- Test 3: Extend with generator ---")
    tests_total += 1
    try:
        # Create a generator of UI elements
        def create_sprites():
            for i in range(3):
                yield mcrfpy.Sprite(50 + i*50, 200)
        
        # Extend with generator
        scene_ui.extend(create_sprites())
        
        if len(scene_ui) == 8:
            print("✓ PASS: Extended collection with generator (now 8 elements)")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Expected 8 elements, got {len(scene_ui)}")
    except Exception as e:
        print(f"✗ FAIL: Error extending with generator: {e}")
    
    # Test 4: Error handling - non-iterable
    print("\n--- Test 4: Error handling - non-iterable ---")
    tests_total += 1
    try:
        scene_ui.extend(42)  # Not iterable
        print("✗ FAIL: Should have raised TypeError for non-iterable")
    except TypeError as e:
        print(f"✓ PASS: Correctly raised TypeError: {e}")
        tests_passed += 1
    except Exception as e:
        print(f"✗ FAIL: Wrong exception type: {e}")
    
    # Test 5: Error handling - wrong element type
    print("\n--- Test 5: Error handling - wrong element type ---")
    tests_total += 1
    try:
        scene_ui.extend([1, 2, 3])  # Wrong types
        print("✗ FAIL: Should have raised TypeError for non-UIDrawable elements")
    except TypeError as e:
        print(f"✓ PASS: Correctly raised TypeError: {e}")
        tests_passed += 1
    except Exception as e:
        print(f"✗ FAIL: Wrong exception type: {e}")
    
    # Test 6: Extend empty iterable
    print("\n--- Test 6: Extend with empty list ---")
    tests_total += 1
    try:
        initial_len = len(scene_ui)
        scene_ui.extend([])  # Empty list
        
        if len(scene_ui) == initial_len:
            print("✓ PASS: Extending with empty list works correctly")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Length changed from {initial_len} to {len(scene_ui)}")
    except Exception as e:
        print(f"✗ FAIL: Error extending with empty list: {e}")
    
    # Test 7: Z-index ordering
    print("\n--- Test 7: Z-index ordering ---")
    tests_total += 1
    try:
        # Clear and add fresh elements
        while len(scene_ui) > 0:
            scene_ui.remove(0)
        
        # Add some initial elements
        frame1 = mcrfpy.Frame(0, 0, 50, 50)
        scene_ui.append(frame1)
        
        # Extend with more elements
        new_elements = [
            mcrfpy.Frame(60, 0, 50, 50),
            mcrfpy.Caption((120, 25), "Test", mcrfpy.Font("assets/JetbrainsMono.ttf"))
        ]
        scene_ui.extend(new_elements)
        
        # Check z-indices are properly assigned
        z_indices = [scene_ui[i].z_index for i in range(3)]
        
        # Z-indices should be increasing
        if z_indices[0] < z_indices[1] < z_indices[2]:
            print(f"✓ PASS: Z-indices properly ordered: {z_indices}")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Z-indices not properly ordered: {z_indices}")
    except Exception as e:
        print(f"✗ FAIL: Error checking z-indices: {e}")
    
    # Test 8: Extend with another UICollection
    print("\n--- Test 8: Extend with another UICollection ---")
    tests_total += 1
    try:
        # Create a Frame with children
        frame_with_children = mcrfpy.Frame(200, 200, 100, 100)
        frame_with_children.children.append(mcrfpy.Sprite(10, 10))
        frame_with_children.children.append(mcrfpy.Caption((10, 50), "Child", mcrfpy.Font("assets/JetbrainsMono.ttf")))
        
        # Try to extend scene_ui with the frame's children collection
        initial_len = len(scene_ui)
        scene_ui.extend(frame_with_children.children)
        
        if len(scene_ui) == initial_len + 2:
            print("✓ PASS: Extended with another UICollection")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Expected {initial_len + 2} elements, got {len(scene_ui)}")
    except Exception as e:
        print(f"✗ FAIL: Error extending with UICollection: {e}")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Tests passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("\nIssue #96 FIXED: UICollection.extend() implemented successfully!")
    else:
        print("\nIssue #96: Some tests failed")
    
    return tests_passed == tests_total

def run_test(runtime):
    """Timer callback to run the test"""
    try:
        success = test_uicollection_extend()
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