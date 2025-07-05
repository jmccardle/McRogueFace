#!/usr/bin/env python3
"""
Test for Issue #95: Fix UICollection __repr__ type display

This test verifies that UICollection's repr shows the actual types of contained
objects instead of just showing them all as "UIDrawable".
"""

import mcrfpy
import sys

def test_uicollection_repr():
    """Test UICollection repr shows correct types"""
    print("=== Testing UICollection __repr__ Type Display (Issue #95) ===\n")
    
    tests_passed = 0
    tests_total = 0
    
    # Get scene UI collection
    scene_ui = mcrfpy.sceneUI("test")
    
    # Test 1: Empty collection
    print("--- Test 1: Empty collection ---")
    tests_total += 1
    repr_str = repr(scene_ui)
    print(f"Empty collection repr: {repr_str}")
    if "0 objects" in repr_str:
        print("✓ PASS: Empty collection shows correctly")
        tests_passed += 1
    else:
        print("✗ FAIL: Empty collection repr incorrect")
    
    # Test 2: Add various UI elements
    print("\n--- Test 2: Mixed UI elements ---")
    tests_total += 1
    
    # Add Frame
    frame = mcrfpy.Frame(10, 10, 100, 100)
    scene_ui.append(frame)
    
    # Add Caption
    caption = mcrfpy.Caption((150, 50), "Test", mcrfpy.Font("assets/JetbrainsMono.ttf"))
    scene_ui.append(caption)
    
    # Add Sprite
    sprite = mcrfpy.Sprite(200, 100)
    scene_ui.append(sprite)
    
    # Add Grid
    grid = mcrfpy.Grid(10, 10)
    grid.x = 300
    grid.y = 100
    scene_ui.append(grid)
    
    # Check repr
    repr_str = repr(scene_ui)
    print(f"Collection repr: {repr_str}")
    
    # Verify it shows the correct types
    expected_types = ["1 Frame", "1 Caption", "1 Sprite", "1 Grid"]
    all_found = all(expected in repr_str for expected in expected_types)
    
    if all_found and "UIDrawable" not in repr_str:
        print("✓ PASS: All types shown correctly, no generic UIDrawable")
        tests_passed += 1
    else:
        print("✗ FAIL: Types not shown correctly")
        for expected in expected_types:
            if expected in repr_str:
                print(f"  ✓ Found: {expected}")
            else:
                print(f"  ✗ Missing: {expected}")
        if "UIDrawable" in repr_str:
            print("  ✗ Still shows generic UIDrawable")
    
    # Test 3: Multiple of same type
    print("\n--- Test 3: Multiple objects of same type ---")
    tests_total += 1
    
    # Add more frames
    frame2 = mcrfpy.Frame(10, 120, 100, 100)
    frame3 = mcrfpy.Frame(10, 230, 100, 100)
    scene_ui.append(frame2)
    scene_ui.append(frame3)
    
    repr_str = repr(scene_ui)
    print(f"Collection repr: {repr_str}")
    
    if "3 Frames" in repr_str:
        print("✓ PASS: Plural form shown correctly for multiple Frames")
        tests_passed += 1
    else:
        print("✗ FAIL: Plural form not correct")
    
    # Test 4: Check total count
    print("\n--- Test 4: Total count verification ---")
    tests_total += 1
    
    # Should have: 3 Frames, 1 Caption, 1 Sprite, 1 Grid = 6 total
    if "6 objects:" in repr_str:
        print("✓ PASS: Total count shown correctly")
        tests_passed += 1
    else:
        print("✗ FAIL: Total count incorrect")
    
    # Test 5: Nested collections (Frame with children)
    print("\n--- Test 5: Nested collections ---")
    tests_total += 1
    
    # Add child to frame
    child_sprite = mcrfpy.Sprite(10, 10)
    frame.children.append(child_sprite)
    
    # Check frame's children collection
    children_repr = repr(frame.children)
    print(f"Frame children repr: {children_repr}")
    
    if "1 Sprite" in children_repr:
        print("✓ PASS: Nested collection shows correct type")
        tests_passed += 1
    else:
        print("✗ FAIL: Nested collection type incorrect")
    
    # Test 6: Collection remains valid after modifications
    print("\n--- Test 6: Collection after modifications ---")
    tests_total += 1
    
    # Remove an item
    scene_ui.remove(0)  # Remove first frame
    
    repr_str = repr(scene_ui)
    print(f"After removal repr: {repr_str}")
    
    if "2 Frames" in repr_str and "5 objects:" in repr_str:
        print("✓ PASS: Collection repr updated correctly after removal")
        tests_passed += 1
    else:
        print("✗ FAIL: Collection repr not updated correctly")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Tests passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("\nIssue #95 FIXED: UICollection __repr__ now shows correct types!")
    else:
        print("\nIssue #95: Some tests failed")
    
    return tests_passed == tests_total

def run_test(runtime):
    """Timer callback to run the test"""
    try:
        success = test_uicollection_repr()
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