#!/usr/bin/env python3
"""Test for Sprite texture methods - Related to issue #19"""
import mcrfpy

print("Testing Sprite texture methods (Issue #19)...")

# Create test scene
sprite_texture_test = mcrfpy.Scene("sprite_texture_test")
sprite_texture_test.activate()
ui = sprite_texture_test.children

# Create sprites
# Based on sprite2 syntax: Sprite(x, y, texture, sprite_index, scale)
sprite1 = mcrfpy.Sprite(10, 10, mcrfpy.default_texture, 0, 2.0)
sprite2 = mcrfpy.Sprite(100, 10, mcrfpy.default_texture, 5, 2.0)

ui.append(sprite1)
ui.append(sprite2)

# Test getting texture
try:
    texture1 = sprite1.texture
    texture2 = sprite2.texture
    print(f"✓ Got textures: {texture1}, {texture2}")
    
    if texture2 == mcrfpy.default_texture:
        print("✓ Texture matches default_texture")
except Exception as e:
    print(f"✗ Failed to get texture: {e}")

# Test setting texture (Issue #19 - get/set texture methods)
try:
    # This should fail as texture is read-only currently
    sprite1.texture = mcrfpy.default_texture
    print("✗ Texture setter should not exist (Issue #19)")
except AttributeError:
    print("✓ Texture is read-only (Issue #19 requests setter)")
except Exception as e:
    print(f"✗ Unexpected error setting texture: {e}")

# Test sprite_number property
try:
    print(f"Sprite2 sprite_number: {sprite2.sprite_number}")
    sprite2.sprite_number = 10
    print(f"✓ Changed sprite_number to: {sprite2.sprite_number}")
except Exception as e:
    print(f"✗ sprite_number property failed: {e}")

# Test sprite index validation (Issue #33)
try:
    # Try to set invalid sprite index
    sprite2.sprite_number = 9999
    print("✗ Should validate sprite index against texture range (Issue #33)")
except Exception as e:
    print(f"✓ Sprite index validation works: {e}")

# Create grid of sprites to show different indices
y_offset = 100
for i in range(12):  # Show first 12 sprites
    sprite = mcrfpy.Sprite(10 + (i % 6) * 40, y_offset + (i // 6) * 40,
                          mcrfpy.default_texture, i, 2.0)
    ui.append(sprite)

caption = mcrfpy.Caption(mcrfpy.Vector(10, 200),
                        text="Issue #19: Sprites need texture setter",
                        fill_color=mcrfpy.Color(255, 255, 255))
ui.append(caption)

print("PASS")