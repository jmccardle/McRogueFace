#!/usr/bin/env python3
"""Test that creating a Texture with an invalid file path raises an error instead of segfaulting."""

import sys
try:
    import mcrfpy
except ImportError as e:
    print(f"Failed to import mcrfpy: {e}", file=sys.stderr)
    sys.exit(1)

failures = []

# Test 1: Try to create a texture with a non-existent file
print("Test 1: Creating texture with non-existent file...")
try:
    texture = mcrfpy.Texture("this_file_does_not_exist.png", 16, 16)
    failures.append("Test 1: Expected IOError but texture was created successfully")
    print("FAIL: Expected IOError but texture was created successfully")
    print(f"Texture: {texture}")
except IOError as e:
    print("PASS: Got expected IOError:", e)
except Exception as e:
    failures.append(f"Test 1: Got unexpected exception type {type(e).__name__}: {e}")
    print(f"FAIL: Got unexpected exception type {type(e).__name__}: {e}")

# Test 2: Try to create a texture with an empty filename
print("\nTest 2: Creating texture with empty filename...")
try:
    texture = mcrfpy.Texture("", 16, 16)
    failures.append("Test 2: Expected IOError but texture was created successfully")
    print("FAIL: Expected IOError but texture was created successfully")
except IOError as e:
    print("PASS: Got expected IOError:", e)
except Exception as e:
    failures.append(f"Test 2: Got unexpected exception type {type(e).__name__}: {e}")
    print(f"FAIL: Got unexpected exception type {type(e).__name__}: {e}")

# Test 3: Verify a valid texture still works
# (the old path assets/sprites/tileset.png never existed, so this check used to be
#  skipped as "INFO"; use a real shipped asset so it actually exercises the good path)
print("\nTest 3: Creating texture with valid file...")
try:
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    print("PASS: Valid texture created successfully")
    print(f"  Sheet dimensions: {texture.sheet_width}x{texture.sheet_height}")
    print(f"  Sprite count: {texture.sprite_count}")
    if texture.sprite_width != 16 or texture.sprite_height != 16:
        failures.append(
            f"Test 3: expected 16x16 sprites, got "
            f"{texture.sprite_width}x{texture.sprite_height}"
        )
    if texture.sheet_width <= 0 or texture.sheet_height <= 0:
        failures.append("Test 3: sheet dimensions should be positive")
    if texture.sprite_count != texture.sheet_width * texture.sheet_height:
        failures.append(
            f"Test 3: sprite_count {texture.sprite_count} != "
            f"sheet_width * sheet_height ({texture.sheet_width * texture.sheet_height})"
        )
except Exception as e:
    failures.append(f"Test 3: Unexpected error with valid path: {type(e).__name__}: {e}")
    print(f"FAIL: Unexpected error with valid path: {type(e).__name__}: {e}")

print("\nAll tests completed. No segfault occurred!")

if failures:
    for f in failures:
        print(f"FAILURE: {f}")
    sys.exit(1)

print("PASS")
sys.exit(0)
