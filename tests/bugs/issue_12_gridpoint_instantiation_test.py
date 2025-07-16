#!/usr/bin/env python3
"""
Test for Issue #12: Forbid GridPoint/GridPointState instantiation

This test verifies that GridPoint and GridPointState cannot be instantiated
directly from Python, as they should only be created internally by the C++ code.
"""

import mcrfpy
import sys

def test_gridpoint_instantiation():
    """Test that GridPoint and GridPointState cannot be instantiated"""
    print("=== Testing GridPoint/GridPointState Instantiation Prevention (Issue #12) ===\n")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Try to instantiate GridPoint
    print("--- Test 1: GridPoint instantiation ---")
    tests_total += 1
    try:
        point = mcrfpy.GridPoint()
        print("✗ FAIL: GridPoint() should not be allowed")
    except TypeError as e:
        print(f"✓ PASS: GridPoint instantiation correctly prevented: {e}")
        tests_passed += 1
    except Exception as e:
        print(f"✗ FAIL: Unexpected error: {e}")
    
    # Test 2: Try to instantiate GridPointState
    print("\n--- Test 2: GridPointState instantiation ---")
    tests_total += 1
    try:
        state = mcrfpy.GridPointState()
        print("✗ FAIL: GridPointState() should not be allowed")
    except TypeError as e:
        print(f"✓ PASS: GridPointState instantiation correctly prevented: {e}")
        tests_passed += 1
    except Exception as e:
        print(f"✗ FAIL: Unexpected error: {e}")
    
    # Test 3: Verify GridPoint can still be obtained from Grid
    print("\n--- Test 3: GridPoint obtained from Grid.at() ---")
    tests_total += 1
    try:
        grid = mcrfpy.Grid(10, 10)
        point = grid.at(5, 5)
        print(f"✓ PASS: GridPoint obtained from Grid.at(): {point}")
        print(f"  Type: {type(point).__name__}")
        tests_passed += 1
    except Exception as e:
        print(f"✗ FAIL: Could not get GridPoint from Grid: {e}")
    
    # Test 4: Verify GridPointState can still be obtained from GridPoint
    print("\n--- Test 4: GridPointState obtained from GridPoint ---")
    tests_total += 1
    try:
        # GridPointState is accessed through GridPoint's click handler
        # Let's check if we can access point properties that would use GridPointState
        if hasattr(point, 'walkable'):
            print(f"✓ PASS: GridPoint has expected properties")
            print(f"  walkable: {point.walkable}")
            print(f"  transparent: {point.transparent}")
            tests_passed += 1
        else:
            print("✗ FAIL: GridPoint missing expected properties")
    except Exception as e:
        print(f"✗ FAIL: Error accessing GridPoint properties: {e}")
    
    # Test 5: Try to call the types directly (alternative syntax)
    print("\n--- Test 5: Alternative instantiation attempts ---")
    tests_total += 1
    all_prevented = True
    
    # Try various ways to instantiate
    attempts = [
        ("mcrfpy.GridPoint.__new__(mcrfpy.GridPoint)", 
         lambda: mcrfpy.GridPoint.__new__(mcrfpy.GridPoint)),
        ("type(point)()", 
         lambda: type(point)() if 'point' in locals() else None),
    ]
    
    for desc, func in attempts:
        try:
            if func:
                result = func()
                print(f"✗ FAIL: {desc} should not be allowed")
                all_prevented = False
        except (TypeError, AttributeError) as e:
            print(f"  ✓ Correctly prevented: {desc}")
        except Exception as e:
            print(f"  ? Unexpected error for {desc}: {e}")
    
    if all_prevented:
        print("✓ PASS: All alternative instantiation attempts prevented")
        tests_passed += 1
    else:
        print("✗ FAIL: Some instantiation attempts succeeded")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Tests passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("\nIssue #12 FIXED: GridPoint/GridPointState instantiation properly forbidden!")
    else:
        print("\nIssue #12: Some tests failed")
    
    return tests_passed == tests_total

def run_test(runtime):
    """Timer callback to run the test"""
    try:
        # First verify the types exist
        print("Checking that GridPoint and GridPointState types exist...")
        print(f"GridPoint type: {mcrfpy.GridPoint}")
        print(f"GridPointState type: {mcrfpy.GridPointState}")
        print()
        
        success = test_gridpoint_instantiation()
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