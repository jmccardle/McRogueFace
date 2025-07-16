#!/usr/bin/env python3
"""Test Grid.at() method with various argument formats"""

import mcrfpy
import sys

def test_grid_at_arguments():
    """Test that Grid.at() accepts all required argument formats"""
    print("Testing Grid.at() argument formats...")
    
    # Create a test scene
    mcrfpy.createScene("test")
    
    # Create a grid
    grid = mcrfpy.Grid(10, 10)
    ui = mcrfpy.sceneUI("test")
    ui.append(grid)
    
    success_count = 0
    total_tests = 4
    
    # Test 1: Two positional arguments (x, y)
    try:
        point1 = grid.at(5, 5)
        print("✓ Test 1 PASSED: grid.at(5, 5)")
        success_count += 1
    except Exception as e:
        print(f"✗ Test 1 FAILED: grid.at(5, 5) - {e}")
    
    # Test 2: Single tuple argument (x, y)
    try:
        point2 = grid.at((3, 3))
        print("✓ Test 2 PASSED: grid.at((3, 3))")
        success_count += 1
    except Exception as e:
        print(f"✗ Test 2 FAILED: grid.at((3, 3)) - {e}")
    
    # Test 3: Keyword arguments x=x, y=y
    try:
        point3 = grid.at(x=7, y=2)
        print("✓ Test 3 PASSED: grid.at(x=7, y=2)")
        success_count += 1
    except Exception as e:
        print(f"✗ Test 3 FAILED: grid.at(x=7, y=2) - {e}")
    
    # Test 4: pos keyword argument pos=(x, y)
    try:
        point4 = grid.at(pos=(1, 8))
        print("✓ Test 4 PASSED: grid.at(pos=(1, 8))")
        success_count += 1
    except Exception as e:
        print(f"✗ Test 4 FAILED: grid.at(pos=(1, 8)) - {e}")
    
    # Test error cases
    print("\nTesting error cases...")
    
    # Test 5: Invalid - mixing pos with x/y
    try:
        grid.at(x=1, pos=(2, 2))
        print("✗ Test 5 FAILED: Should have raised error for mixing pos and x/y")
    except TypeError as e:
        print(f"✓ Test 5 PASSED: Correctly rejected mixing pos and x/y - {e}")
    
    # Test 6: Invalid - out of range
    try:
        grid.at(15, 15)
        print("✗ Test 6 FAILED: Should have raised error for out of range")
    except ValueError as e:
        print(f"✓ Test 6 PASSED: Correctly rejected out of range - {e}")
    
    # Test 7: Verify all points are valid GridPoint objects
    try:
        # Check that we can set walkable on all returned points
        if 'point1' in locals():
            point1.walkable = True
        if 'point2' in locals():
            point2.walkable = False
        if 'point3' in locals():
            point3.color = mcrfpy.Color(255, 0, 0)
        if 'point4' in locals():
            point4.tilesprite = 5
        print("✓ All returned GridPoint objects are valid")
    except Exception as e:
        print(f"✗ GridPoint objects validation failed: {e}")
    
    print(f"\nSummary: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED!")
        sys.exit(1)

# Run timer callback to execute tests after render loop starts
def run_test(elapsed):
    test_grid_at_arguments()

# Set a timer to run the test
mcrfpy.setTimer("test", run_test, 100)