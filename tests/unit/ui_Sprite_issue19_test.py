#!/usr/bin/env python3
"""Test for Sprite texture methods - Related to issue #19"""
import mcrfpy
import sys

print("Testing Sprite texture methods (Issue #19)...")

failures = []

def check(condition, message):
    if condition:
        print(f"PASS: {message}")
    else:
        print(f"FAIL: {message}")
        failures.append(message)

# Create test scene
sprite_texture_test = mcrfpy.Scene("sprite_texture_test")
sprite_texture_test.activate()
ui = sprite_texture_test.children

# Create sprites
# Current Sprite ctor: Sprite(pos=None, texture=None, sprite_index=0, **kwargs)
sprite1 = mcrfpy.Sprite(pos=(10, 10), texture=mcrfpy.default_texture, sprite_index=0, scale=2.0)
sprite2 = mcrfpy.Sprite(pos=(100, 10), texture=mcrfpy.default_texture, sprite_index=5, scale=2.0)

ui.append(sprite1)
ui.append(sprite2)

check(len(ui) == 2, "both sprites appended to the scene")

# Test getting texture
texture1 = sprite1.texture
texture2 = sprite2.texture
print(f"Got textures: {texture1}, {texture2}")
check(isinstance(texture1, mcrfpy.Texture) and isinstance(texture2, mcrfpy.Texture),
      "Sprite.texture returns a Texture")
# Texture wrappers do not compare by identity; compare the underlying source.
check(texture2.source == mcrfpy.default_texture.source,
      "sprite texture is the default texture that was passed in")

# Test setting texture (Issue #19 asked for a texture setter; it now EXISTS,
# so the old "texture must be read-only" expectation is inverted here.)
other_texture = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16)
sprite1.sprite_index = 0
sprite1.texture = other_texture
check(sprite1.texture.source == other_texture.source,
      "Sprite.texture setter swaps the texture (Issue #19)")
check(sprite1.bounds[1].x == other_texture.sprite_width * sprite1.scale,
      "swapped texture drives the sprite's rendered size")

# Restore the default texture
sprite1.texture = mcrfpy.default_texture
check(sprite1.texture.source == mcrfpy.default_texture.source,
      "Sprite.texture setter restores the default texture")

# Test sprite_index property
print(f"Sprite2 sprite_index: {sprite2.sprite_index}")
check(sprite2.sprite_index == 5, "sprite_index reflects the constructor argument")
sprite2.sprite_index = 10
print(f"sprite_index set to: {sprite2.sprite_index}")
check(sprite2.sprite_index == 10, "sprite_index setter takes effect")

# Test sprite index validation (Issue #33)
try:
    sprite2.sprite_index = 9999
    check(False, "out-of-range sprite_index must raise (Issue #33)")
except ValueError as e:
    print(f"Sprite index validation works: {e}")
    check(True, "out-of-range sprite_index raises ValueError (Issue #33)")
check(sprite2.sprite_index == 10, "rejected sprite_index leaves the old value intact")

# Create grid of sprites to show different indices
y_offset = 100
for i in range(12):  # Show first 12 sprites
    sprite = mcrfpy.Sprite(pos=(10 + (i % 6) * 40, y_offset + (i // 6) * 40),
                           texture=mcrfpy.default_texture, sprite_index=i, scale=2.0)
    ui.append(sprite)

check(len(ui) == 14, "12 additional sprites appended")
check(all(ui[2 + i].sprite_index == i for i in range(12)),
      "each sprite in the grid kept its own sprite_index")

caption = mcrfpy.Caption(pos=(10, 200),
                         text="Issue #19: Sprite texture setter",
                         fill_color=mcrfpy.Color(255, 255, 255))
ui.append(caption)

if failures:
    print(f"FAILED ({len(failures)} checks): {failures}")
    sys.exit(1)

print("PASS")
sys.exit(0)
