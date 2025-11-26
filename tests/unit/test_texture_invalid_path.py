#!/usr/bin/env python3
"""Test that creating a Texture with an invalid file path raises an error instead of segfaulting."""

import sys
try:
    import mcrfpy
except ImportError as e:
    print(f"Failed to import mcrfpy: {e}", file=sys.stderr)
    sys.exit(1)

# Test 1: Try to create a texture with a non-existent file
print("Test 1: Creating texture with non-existent file...")
try:
    texture = mcrfpy.Texture("this_file_does_not_exist.png", 16, 16)
    print("FAIL: Expected IOError but texture was created successfully")
    print(f"Texture: {texture}")
except IOError as e:
    print("PASS: Got expected IOError:", e)
except Exception as e:
    print(f"FAIL: Got unexpected exception type {type(e).__name__}: {e}")

# Test 2: Try to create a texture with an empty filename
print("\nTest 2: Creating texture with empty filename...")
try:
    texture = mcrfpy.Texture("", 16, 16)
    print("FAIL: Expected IOError but texture was created successfully")
except IOError as e:
    print("PASS: Got expected IOError:", e)
except Exception as e:
    print(f"FAIL: Got unexpected exception type {type(e).__name__}: {e}")

# Test 3: Verify a valid texture still works
print("\nTest 3: Creating texture with valid file (if exists)...")
try:
    # Try a common test asset path
    texture = mcrfpy.Texture("assets/sprites/tileset.png", 16, 16)
    print("PASS: Valid texture created successfully")
    print(f"  Sheet dimensions: {texture.sheet_width}x{texture.sheet_height}")
    print(f"  Sprite count: {texture.sprite_count}")
except IOError as e:
    # This is OK if the asset doesn't exist in the test environment
    print("INFO: Test texture file not found (expected in test environment):", e)
except Exception as e:
    print(f"FAIL: Unexpected error with valid path: {type(e).__name__}: {e}")

print("\nAll tests completed. No segfault occurred!")