#!/usr/bin/env python3
"""Comprehensive test of all constructor signatures"""

import mcrfpy
import sys

def test_frame_combinations():
    print("Testing Frame constructors...")
    
    # No args
    f1 = mcrfpy.Frame()
    assert f1.x == 0 and f1.y == 0 and f1.w == 0 and f1.h == 0
    
    # Positional only
    f2 = mcrfpy.Frame((10, 20), (100, 200))
    assert f2.x == 10 and f2.y == 20 and f2.w == 100 and f2.h == 200
    
    # Mix positional and keyword
    f3 = mcrfpy.Frame((5, 5), size=(50, 50), fill_color=(255, 0, 0), name="red_frame")
    assert f3.x == 5 and f3.y == 5 and f3.w == 50 and f3.h == 50 and f3.name == "red_frame"
    
    # Keyword only
    f4 = mcrfpy.Frame(x=15, y=25, w=150, h=250, outline=2.0, visible=True, opacity=0.5)
    assert f4.x == 15 and f4.y == 25 and f4.w == 150 and f4.h == 250
    assert f4.outline == 2.0 and f4.visible and abs(f4.opacity - 0.5) < 0.0001
    
    print("  Frame: all constructor variations work")

def test_grid_combinations():
    print("Testing Grid constructors...")
    
    # No args (should default to 2x2)
    g1 = mcrfpy.Grid()
    assert g1.grid_w == 2 and g1.grid_h == 2
    
    # Positional args
    g2 = mcrfpy.Grid((0, 0), (320, 320), (10, 10))
    assert g2.x == 0 and g2.y == 0 and g2.grid_w == 10 and g2.grid_h == 10
    
    # Mix with keywords
    g3 = mcrfpy.Grid(pos=(50, 50), grid_w=20, grid_h=15, zoom=2.0, name="zoomed_grid")
    assert g3.x == 50 and g3.y == 50 and g3.grid_w == 20 and g3.grid_h == 15
    assert g3.zoom == 2.0 and g3.name == "zoomed_grid"
    
    print(" Grid: all constructor variations work")

def test_sprite_combinations():
    print("Testing Sprite constructors...")
    
    # No args
    s1 = mcrfpy.Sprite()
    assert s1.x == 0 and s1.y == 0 and s1.sprite_index == 0
    
    # Positional with None texture
    s2 = mcrfpy.Sprite((100, 150), None, 5)
    assert s2.x == 100 and s2.y == 150 and s2.sprite_index == 5
    
    # Keywords only
    s3 = mcrfpy.Sprite(x=200, y=250, sprite_index=10, scale=2.0, name="big_sprite")
    assert s3.x == 200 and s3.y == 250 and s3.sprite_index == 10
    assert s3.scale == 2.0 and s3.name == "big_sprite"
    
    # Scale variations
    s4 = mcrfpy.Sprite(scale_x=2.0, scale_y=3.0)
    assert s4.scale_x == 2.0 and s4.scale_y == 3.0
    
    print(" Sprite: all constructor variations work")

def test_caption_combinations():
    print("Testing Caption constructors...")
    
    # No args
    c1 = mcrfpy.Caption()
    assert c1.text == "" and c1.x == 0 and c1.y == 0
    
    # Positional args
    c2 = mcrfpy.Caption((50, 100), None, "Hello World")
    assert c2.x == 50 and c2.y == 100 and c2.text == "Hello World"
    
    # Keywords only
    c3 = mcrfpy.Caption(text="Test", font_size=24, fill_color=(0, 255, 0), name="green_text")
    assert c3.text == "Test" and c3.font_size == 24 and c3.name == "green_text"
    
    # Mix positional and keywords
    c4 = mcrfpy.Caption((10, 10), text="Mixed", outline=1.0, opacity=0.8)
    assert c4.x == 10 and c4.y == 10 and c4.text == "Mixed"
    assert c4.outline == 1.0 and abs(c4.opacity - 0.8) < 0.0001
    
    print(" Caption: all constructor variations work")

def test_entity_combinations():
    print("Testing Entity constructors...")

    # No args
    e1 = mcrfpy.Entity()
    assert e1.grid_x == 0 and e1.grid_y == 0 and e1.sprite_index == 0

    # Positional args (grid coordinates)
    e2 = mcrfpy.Entity((5, 10), None, 3)
    assert e2.grid_x == 5 and e2.grid_y == 10 and e2.sprite_index == 3

    # Keywords only - Entity uses grid_pos, not x/y directly
    e3 = mcrfpy.Entity(grid_pos=(15, 20), sprite_index=7, name="player", visible=True)
    assert e3.grid_x == 15 and e3.grid_y == 20 and e3.sprite_index == 7
    assert e3.name == "player" and e3.visible

    print("  Entity: all constructor variations work")

def test_edge_cases():
    print("Testing edge cases...")
    
    # Empty strings
    c = mcrfpy.Caption(text="", name="")
    assert c.text == "" and c.name == ""
    
    # Zero values
    f = mcrfpy.Frame(pos=(0, 0), size=(0, 0), opacity=0.0, z_index=0)
    assert f.x == 0 and f.y == 0 and f.w == 0 and f.h == 0
    
    # None values where allowed
    s = mcrfpy.Sprite(texture=None)
    c = mcrfpy.Caption(font=None)
    e = mcrfpy.Entity(texture=None)
    
    print(" Edge cases: all handled correctly")

# Run all tests
try:
    test_frame_combinations()
    test_grid_combinations()
    test_sprite_combinations()
    test_caption_combinations()
    test_entity_combinations()
    test_edge_cases()
    
    print("\nPASS: All comprehensive constructor tests passed!")
    sys.exit(0)
    
except Exception as e:
    print(f"\nFAIL: Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)