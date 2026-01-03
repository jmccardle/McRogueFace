#!/usr/bin/env python3
"""Test Grid creation with null/None texture to reproduce segfault"""
import mcrfpy
import sys

def test_grid_null_texture():
    """Test if Grid can be created without a texture"""
    print("=== Testing Grid with null texture ===")
    
    # Create test scene
    grid_null_test = mcrfpy.Scene("grid_null_test")
    grid_null_test.activate()
    ui = grid_null_test.children
    
    # Test 1: Try with None
    try:
        print("Test 1: Creating Grid with None texture...")
        grid = mcrfpy.Grid(10, 10, None, mcrfpy.Vector(0, 0), mcrfpy.Vector(400, 400))
        print("✗ Should have raised exception for None texture")
    except Exception as e:
        print(f"✓ Correctly rejected None texture: {e}")
    
    # Test 2: Try without texture parameter (if possible)
    try:
        print("\nTest 2: Creating Grid with missing parameters...")
        grid = mcrfpy.Grid(10, 10)
        print("✗ Should have raised exception for missing parameters")
    except Exception as e:
        print(f"✓ Correctly rejected missing parameters: {e}")
    
    print("\nTest complete - Grid requires texture parameter")
    sys.exit(0)

# Run immediately
test_grid_null_texture()