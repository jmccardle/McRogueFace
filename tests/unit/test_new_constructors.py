#!/usr/bin/env python3
"""Test the new constructor signatures for mcrfpy classes"""

import mcrfpy

def test_frame():
    # Test no-arg constructor
    f1 = mcrfpy.Frame()
    assert f1.x == 0 and f1.y == 0
    print("✓ Frame() works")
    
    # Test positional args
    f2 = mcrfpy.Frame((10, 20), (100, 50))
    assert f2.x == 10 and f2.y == 20 and f2.w == 100 and f2.h == 50
    print("✓ Frame(pos, size) works")
    
    # Test keyword args
    f3 = mcrfpy.Frame(pos=(30, 40), size=(200, 100), fill_color=(255, 0, 0))
    assert f3.x == 30 and f3.y == 40 and f3.w == 200 and f3.h == 100
    print("✓ Frame with keywords works")

def test_grid():
    # Test no-arg constructor (should default to 2x2)
    g1 = mcrfpy.Grid()
    assert g1.grid_x == 2 and g1.grid_y == 2
    print("✓ Grid() works with 2x2 default")
    
    # Test positional args
    g2 = mcrfpy.Grid((10, 10), (320, 320), (20, 20))
    assert g2.x == 10 and g2.y == 10 and g2.grid_x == 20 and g2.grid_y == 20
    print("✓ Grid(pos, size, grid_size) works")

def test_sprite():
    # Test no-arg constructor
    s1 = mcrfpy.Sprite()
    assert s1.x == 0 and s1.y == 0
    print("✓ Sprite() works")
    
    # Test positional args
    s2 = mcrfpy.Sprite((50, 60), None, 5)
    assert s2.x == 50 and s2.y == 60 and s2.sprite_index == 5
    print("✓ Sprite(pos, texture, sprite_index) works")

def test_caption():
    # Test no-arg constructor
    c1 = mcrfpy.Caption()
    assert c1.text == ""
    print("✓ Caption() works")
    
    # Test positional args
    c2 = mcrfpy.Caption((100, 100), None, "Hello World")
    assert c2.x == 100 and c2.y == 100 and c2.text == "Hello World"
    print("✓ Caption(pos, font, text) works")

def test_entity():
    # Test no-arg constructor
    e1 = mcrfpy.Entity()
    assert e1.x == 0 and e1.y == 0
    print("✓ Entity() works")
    
    # Test positional args
    e2 = mcrfpy.Entity((5, 10), None, 3)
    assert e2.x == 5 and e2.y == 10 and e2.sprite_index == 3
    print("✓ Entity(grid_pos, texture, sprite_index) works")

# Run all tests
try:
    test_frame()
    test_grid()
    test_sprite()
    test_caption()
    test_entity()
    print("\n✅ All constructor tests passed!")
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()