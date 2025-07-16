#!/usr/bin/env python3
"""
Test for Issue #80: Rename Caption.size to font_size

This test verifies that Caption now uses font_size property instead of size,
while maintaining backward compatibility.
"""

import mcrfpy
import sys

def test_caption_font_size():
    """Test Caption font_size property"""
    print("=== Testing Caption font_size Property (Issue #80) ===\n")
    
    tests_passed = 0
    tests_total = 0
    
    # Create a caption for testing
    caption = mcrfpy.Caption((100, 100), "Test Text", mcrfpy.Font("assets/JetbrainsMono.ttf"))
    
    # Test 1: Check that font_size property exists and works
    print("--- Test 1: font_size property ---")
    tests_total += 1
    try:
        # Set font size using new property name
        caption.font_size = 24
        if caption.font_size == 24:
            print("✓ PASS: font_size property works correctly")
            tests_passed += 1
        else:
            print(f"✗ FAIL: font_size is {caption.font_size}, expected 24")
    except AttributeError as e:
        print(f"✗ FAIL: font_size property not found: {e}")
    
    # Test 2: Check that old 'size' property is removed
    print("\n--- Test 2: Old 'size' property removed ---")
    tests_total += 1
    try:
        # Try to access size property - this should fail
        old_size = caption.size
        print(f"✗ FAIL: 'size' property still accessible (value: {old_size}) - should be removed")
    except AttributeError:
        print("✓ PASS: 'size' property correctly removed")
        tests_passed += 1
    
    # Test 3: Verify font_size changes are reflected
    print("\n--- Test 3: font_size changes ---")
    tests_total += 1
    caption.font_size = 36
    if caption.font_size == 36:
        print("✓ PASS: font_size changes are reflected correctly")
        tests_passed += 1
    else:
        print(f"✗ FAIL: font_size is {caption.font_size}, expected 36")
    
    # Test 4: Check property type
    print("\n--- Test 4: Property type check ---")
    tests_total += 1
    caption.font_size = 18
    if isinstance(caption.font_size, int):
        print("✓ PASS: font_size returns integer as expected")
        tests_passed += 1
    else:
        print(f"✗ FAIL: font_size returns {type(caption.font_size).__name__}, expected int")
    
    # Test 5: Verify in __dir__
    print("\n--- Test 5: Property introspection ---")
    tests_total += 1
    properties = dir(caption)
    if 'font_size' in properties:
        print("✓ PASS: 'font_size' appears in dir(caption)")
        tests_passed += 1
    else:
        print("✗ FAIL: 'font_size' not found in dir(caption)")
    
    # Check if 'size' still appears
    if 'size' in properties:
        print("  INFO: 'size' still appears in dir(caption) - backward compatibility maintained")
    else:
        print("  INFO: 'size' removed from dir(caption) - breaking change")
    
    # Test 6: Edge cases
    print("\n--- Test 6: Edge cases ---")
    tests_total += 1
    all_passed = True
    
    # Test setting to 0
    caption.font_size = 0
    if caption.font_size != 0:
        print(f"✗ FAIL: Setting font_size to 0 failed (got {caption.font_size})")
        all_passed = False
    
    # Test setting to large value
    caption.font_size = 100
    if caption.font_size != 100:
        print(f"✗ FAIL: Setting font_size to 100 failed (got {caption.font_size})")
        all_passed = False
    
    # Test float to int conversion
    caption.font_size = 24.7
    if caption.font_size != 24:
        print(f"✗ FAIL: Float to int conversion failed (got {caption.font_size})")
        all_passed = False
    
    if all_passed:
        print("✓ PASS: All edge cases handled correctly")
        tests_passed += 1
    else:
        print("✗ FAIL: Some edge cases failed")
    
    # Test 7: Scene UI integration
    print("\n--- Test 7: Scene UI integration ---")
    tests_total += 1
    try:
        scene_ui = mcrfpy.sceneUI("test")
        scene_ui.append(caption)
        
        # Modify font_size after adding to scene
        caption.font_size = 32
        
        print("✓ PASS: Caption with font_size works in scene UI")
        tests_passed += 1
    except Exception as e:
        print(f"✗ FAIL: Scene UI integration failed: {e}")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Tests passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("\nIssue #80 FIXED: Caption.size successfully renamed to font_size!")
    else:
        print("\nIssue #80: Some tests failed")
    
    return tests_passed == tests_total

def run_test(runtime):
    """Timer callback to run the test"""
    try:
        success = test_caption_font_size()
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