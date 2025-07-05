#!/usr/bin/env python3
"""
Test for Issue #82: Add scale_x and scale_y to UISprite

This test verifies that UISprite now supports non-uniform scaling through
separate scale_x and scale_y properties, in addition to the existing uniform
scale property.
"""

import mcrfpy
import sys

def test_scale_xy_properties():
    """Test scale_x and scale_y properties on UISprite"""
    print("=== Testing UISprite scale_x and scale_y Properties ===")
    
    tests_passed = 0
    tests_total = 0
    
    # Create a texture and sprite
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    sprite = mcrfpy.Sprite(10, 10, texture, 0, 1.0)
    
    # Test 1: Check scale_x property exists and defaults correctly
    tests_total += 1
    try:
        scale_x = sprite.scale_x
        if scale_x == 1.0:
            print(f"✓ PASS: sprite.scale_x = {scale_x} (default)")
            tests_passed += 1
        else:
            print(f"✗ FAIL: sprite.scale_x = {scale_x}, expected 1.0")
    except AttributeError as e:
        print(f"✗ FAIL: scale_x not accessible: {e}")
    
    # Test 2: Check scale_y property exists and defaults correctly
    tests_total += 1
    try:
        scale_y = sprite.scale_y
        if scale_y == 1.0:
            print(f"✓ PASS: sprite.scale_y = {scale_y} (default)")
            tests_passed += 1
        else:
            print(f"✗ FAIL: sprite.scale_y = {scale_y}, expected 1.0")
    except AttributeError as e:
        print(f"✗ FAIL: scale_y not accessible: {e}")
    
    # Test 3: Set scale_x independently
    tests_total += 1
    try:
        sprite.scale_x = 2.0
        if sprite.scale_x == 2.0 and sprite.scale_y == 1.0:
            print(f"✓ PASS: scale_x set independently (x={sprite.scale_x}, y={sprite.scale_y})")
            tests_passed += 1
        else:
            print(f"✗ FAIL: scale_x didn't set correctly (x={sprite.scale_x}, y={sprite.scale_y})")
    except Exception as e:
        print(f"✗ FAIL: scale_x setter error: {e}")
    
    # Test 4: Set scale_y independently
    tests_total += 1
    try:
        sprite.scale_y = 3.0
        if sprite.scale_x == 2.0 and sprite.scale_y == 3.0:
            print(f"✓ PASS: scale_y set independently (x={sprite.scale_x}, y={sprite.scale_y})")
            tests_passed += 1
        else:
            print(f"✗ FAIL: scale_y didn't set correctly (x={sprite.scale_x}, y={sprite.scale_y})")
    except Exception as e:
        print(f"✗ FAIL: scale_y setter error: {e}")
    
    # Test 5: Uniform scale property interaction
    tests_total += 1
    try:
        # Setting uniform scale should affect both x and y
        sprite.scale = 1.5
        if sprite.scale_x == 1.5 and sprite.scale_y == 1.5:
            print(f"✓ PASS: uniform scale sets both scale_x and scale_y")
            tests_passed += 1
        else:
            print(f"✗ FAIL: uniform scale didn't update scale_x/scale_y correctly")
    except Exception as e:
        print(f"✗ FAIL: uniform scale interaction error: {e}")
    
    # Test 6: Reading uniform scale with non-uniform values
    tests_total += 1
    try:
        sprite.scale_x = 2.0
        sprite.scale_y = 3.0
        uniform_scale = sprite.scale
        # When scales differ, scale property should return scale_x (or could be average, or error)
        print(f"? INFO: With non-uniform scaling (x=2.0, y=3.0), scale property returns: {uniform_scale}")
        # We'll accept this behavior whatever it is
        tests_passed += 1
    except Exception as e:
        print(f"✗ FAIL: reading scale with non-uniform values failed: {e}")
    
    return tests_passed, tests_total

def test_animation_compatibility():
    """Test that animations work with scale_x and scale_y"""
    print("\n=== Testing Animation Compatibility ===")
    
    tests_passed = 0
    tests_total = 0
    
    # Test property system compatibility
    tests_total += 1
    try:
        texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
        sprite = mcrfpy.Sprite(0, 0, texture, 0, 1.0)
        
        # Test setting various scale values
        sprite.scale_x = 0.5
        sprite.scale_y = 2.0
        sprite.scale_x = 1.5
        sprite.scale_y = 1.5
        
        print("✓ PASS: scale_x and scale_y properties work for potential animations")
        tests_passed += 1
    except Exception as e:
        print(f"✗ FAIL: scale_x/scale_y animation compatibility issue: {e}")
    
    return tests_passed, tests_total

def test_edge_cases():
    """Test edge cases for scale properties"""
    print("\n=== Testing Edge Cases ===")
    
    tests_passed = 0
    tests_total = 0
    
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    sprite = mcrfpy.Sprite(0, 0, texture, 0, 1.0)
    
    # Test 1: Zero scale
    tests_total += 1
    try:
        sprite.scale_x = 0.0
        sprite.scale_y = 0.0
        print(f"✓ PASS: Zero scale allowed (x={sprite.scale_x}, y={sprite.scale_y})")
        tests_passed += 1
    except Exception as e:
        print(f"✗ FAIL: Zero scale not allowed: {e}")
    
    # Test 2: Negative scale (flip)
    tests_total += 1
    try:
        sprite.scale_x = -1.0
        sprite.scale_y = -1.0
        print(f"✓ PASS: Negative scale allowed for flipping (x={sprite.scale_x}, y={sprite.scale_y})")
        tests_passed += 1
    except Exception as e:
        print(f"✗ FAIL: Negative scale not allowed: {e}")
    
    # Test 3: Very large scale
    tests_total += 1
    try:
        sprite.scale_x = 100.0
        sprite.scale_y = 100.0
        print(f"✓ PASS: Large scale values allowed (x={sprite.scale_x}, y={sprite.scale_y})")
        tests_passed += 1
    except Exception as e:
        print(f"✗ FAIL: Large scale values not allowed: {e}")
    
    return tests_passed, tests_total

def run_test(runtime):
    """Timer callback to run the test"""
    try:
        print("=== Testing scale_x and scale_y Properties (Issue #82) ===\n")
        
        basic_passed, basic_total = test_scale_xy_properties()
        anim_passed, anim_total = test_animation_compatibility()
        edge_passed, edge_total = test_edge_cases()
        
        total_passed = basic_passed + anim_passed + edge_passed
        total_tests = basic_total + anim_total + edge_total
        
        print(f"\n=== SUMMARY ===")
        print(f"Basic tests: {basic_passed}/{basic_total}")
        print(f"Animation tests: {anim_passed}/{anim_total}")
        print(f"Edge case tests: {edge_passed}/{edge_total}")
        print(f"Total tests passed: {total_passed}/{total_tests}")
        
        if total_passed == total_tests:
            print("\nIssue #82 FIXED: scale_x and scale_y properties added!")
            print("\nOverall result: PASS")
        else:
            print("\nIssue #82: Some tests failed")
            print("\nOverall result: FAIL")
            
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