#!/usr/bin/env python3
"""
Test for Issue #79: Color r, g, b, a properties return None

This test verifies that Color object properties (r, g, b, a) work correctly.
"""

import mcrfpy
import sys

def test_color_properties():
    """Test Color r, g, b, a property access and modification"""
    print("=== Testing Color r, g, b, a Properties (Issue #79) ===\n")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Create color and check properties
    print("--- Test 1: Basic property access ---")
    color1 = mcrfpy.Color(255, 128, 64, 32)
    
    tests_total += 1
    if color1.r == 255:
        print("✓ PASS: color.r returns correct value (255)")
        tests_passed += 1
    else:
        print(f"✗ FAIL: color.r returned {color1.r} instead of 255")
    
    tests_total += 1
    if color1.g == 128:
        print("✓ PASS: color.g returns correct value (128)")
        tests_passed += 1
    else:
        print(f"✗ FAIL: color.g returned {color1.g} instead of 128")
    
    tests_total += 1
    if color1.b == 64:
        print("✓ PASS: color.b returns correct value (64)")
        tests_passed += 1
    else:
        print(f"✗ FAIL: color.b returned {color1.b} instead of 64")
    
    tests_total += 1
    if color1.a == 32:
        print("✓ PASS: color.a returns correct value (32)")
        tests_passed += 1
    else:
        print(f"✗ FAIL: color.a returned {color1.a} instead of 32")
    
    # Test 2: Modify properties
    print("\n--- Test 2: Property modification ---")
    color1.r = 200
    color1.g = 100
    color1.b = 50
    color1.a = 25
    
    tests_total += 1
    if color1.r == 200:
        print("✓ PASS: color.r set successfully")
        tests_passed += 1
    else:
        print(f"✗ FAIL: color.r is {color1.r} after setting to 200")
    
    tests_total += 1
    if color1.g == 100:
        print("✓ PASS: color.g set successfully")
        tests_passed += 1
    else:
        print(f"✗ FAIL: color.g is {color1.g} after setting to 100")
    
    tests_total += 1
    if color1.b == 50:
        print("✓ PASS: color.b set successfully")
        tests_passed += 1
    else:
        print(f"✗ FAIL: color.b is {color1.b} after setting to 50")
    
    tests_total += 1
    if color1.a == 25:
        print("✓ PASS: color.a set successfully")
        tests_passed += 1
    else:
        print(f"✗ FAIL: color.a is {color1.a} after setting to 25")
    
    # Test 3: Boundary values
    print("\n--- Test 3: Boundary value tests ---")
    color2 = mcrfpy.Color(0, 0, 0, 0)
    
    tests_total += 1
    if color2.r == 0 and color2.g == 0 and color2.b == 0 and color2.a == 0:
        print("✓ PASS: Minimum values (0) work correctly")
        tests_passed += 1
    else:
        print("✗ FAIL: Minimum values not working")
    
    color3 = mcrfpy.Color(255, 255, 255, 255)
    tests_total += 1
    if color3.r == 255 and color3.g == 255 and color3.b == 255 and color3.a == 255:
        print("✓ PASS: Maximum values (255) work correctly")
        tests_passed += 1
    else:
        print("✗ FAIL: Maximum values not working")
    
    # Test 4: Invalid value handling
    print("\n--- Test 4: Invalid value handling ---")
    tests_total += 1
    try:
        color3.r = 256  # Out of range
        print("✗ FAIL: Should have raised ValueError for value > 255")
    except ValueError as e:
        print(f"✓ PASS: Correctly raised ValueError: {e}")
        tests_passed += 1
    
    tests_total += 1
    try:
        color3.g = -1  # Out of range
        print("✗ FAIL: Should have raised ValueError for value < 0")
    except ValueError as e:
        print(f"✓ PASS: Correctly raised ValueError: {e}")
        tests_passed += 1
    
    tests_total += 1
    try:
        color3.b = "red"  # Wrong type
        print("✗ FAIL: Should have raised TypeError for string value")
    except TypeError as e:
        print(f"✓ PASS: Correctly raised TypeError: {e}")
        tests_passed += 1
    
    # Test 5: Verify __repr__ shows correct values
    print("\n--- Test 5: String representation ---")
    color4 = mcrfpy.Color(10, 20, 30, 40)
    repr_str = repr(color4)
    tests_total += 1
    if "(10, 20, 30, 40)" in repr_str:
        print(f"✓ PASS: __repr__ shows correct values: {repr_str}")
        tests_passed += 1
    else:
        print(f"✗ FAIL: __repr__ incorrect: {repr_str}")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Tests passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("\nIssue #79 FIXED: Color properties now work correctly!")
    else:
        print("\nIssue #79: Some tests failed")
    
    return tests_passed == tests_total

def run_test(timer, runtime):
    """Timer callback to run the test"""
    try:
        success = test_color_properties()
        print("\nOverall result: " + ("PASS" if success else "FAIL"))
    except Exception as e:
        print(f"\nTest error: {e}")
        import traceback
        traceback.print_exc()
        print("\nOverall result: FAIL")
    
    sys.exit(0)

# Set up the test scene
test = mcrfpy.Scene("test")
test.activate()

# Schedule test to run after game loop starts
test_timer = mcrfpy.Timer("test", run_test, 100, once=True)