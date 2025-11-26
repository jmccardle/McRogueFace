#!/usr/bin/env python3
"""Test the name parameter in constructors"""

import mcrfpy

# Test Frame with name parameter
try:
    frame1 = mcrfpy.Frame(name="test_frame")
    print(f"✓ Frame with name: {frame1.name}")
except Exception as e:
    print(f"✗ Frame with name failed: {e}")

# Test Grid with name parameter
try:
    grid1 = mcrfpy.Grid(name="test_grid")
    print(f"✓ Grid with name: {grid1.name}")
except Exception as e:
    print(f"✗ Grid with name failed: {e}")

# Test Sprite with name parameter
try:
    sprite1 = mcrfpy.Sprite(name="test_sprite")
    print(f"✓ Sprite with name: {sprite1.name}")
except Exception as e:
    print(f"✗ Sprite with name failed: {e}")

# Test Caption with name parameter
try:
    caption1 = mcrfpy.Caption(name="test_caption")
    print(f"✓ Caption with name: {caption1.name}")
except Exception as e:
    print(f"✗ Caption with name failed: {e}")

# Test Entity with name parameter
try:
    entity1 = mcrfpy.Entity(name="test_entity")
    print(f"✓ Entity with name: {entity1.name}")
except Exception as e:
    print(f"✗ Entity with name failed: {e}")

# Test with mixed positional and name
try:
    frame2 = mcrfpy.Frame((10, 10), (100, 100), name="positioned_frame")
    print(f"✓ Frame with positional args and name: pos=({frame2.x}, {frame2.y}), size=({frame2.w}, {frame2.h}), name={frame2.name}")
except Exception as e:
    print(f"✗ Frame with positional and name failed: {e}")

print("\n✅ All name parameter tests complete!")