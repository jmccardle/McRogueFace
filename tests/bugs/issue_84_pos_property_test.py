#!/usr/bin/env python3
"""
Test for Issue #84: Add pos property to Frame and Sprite

This test verifies that Frame and Sprite now have a 'pos' property that
returns and accepts Vector objects, similar to Caption and Entity.
"""

import mcrfpy
import sys

def test_frame_pos_property():
    """Test pos property on Frame"""
    print("=== Testing Frame pos Property ===")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Get pos property
    tests_total += 1
    try:
        frame = mcrfpy.Frame(10, 20, 100, 50)
        pos = frame.pos
        if hasattr(pos, 'x') and hasattr(pos, 'y') and pos.x == 10 and pos.y == 20:
            print(f"✓ PASS: frame.pos returns Vector({pos.x}, {pos.y})")
            tests_passed += 1
        else:
            print(f"✗ FAIL: frame.pos incorrect: {pos}")
    except AttributeError as e:
        print(f"✗ FAIL: pos property not accessible: {e}")
    
    # Test 2: Set pos with Vector
    tests_total += 1
    try:
        vec = mcrfpy.Vector(30, 40)
        frame.pos = vec
        if frame.x == 30 and frame.y == 40:
            print(f"✓ PASS: frame.pos = Vector sets position correctly")
            tests_passed += 1
        else:
            print(f"✗ FAIL: pos setter failed: x={frame.x}, y={frame.y}")
    except Exception as e:
        print(f"✗ FAIL: pos setter with Vector error: {e}")
    
    # Test 3: Set pos with tuple
    tests_total += 1
    try:
        frame.pos = (50, 60)
        if frame.x == 50 and frame.y == 60:
            print(f"✓ PASS: frame.pos = tuple sets position correctly")
            tests_passed += 1
        else:
            print(f"✗ FAIL: pos setter with tuple failed: x={frame.x}, y={frame.y}")
    except Exception as e:
        print(f"✗ FAIL: pos setter with tuple error: {e}")
    
    # Test 4: Verify pos getter reflects changes
    tests_total += 1
    try:
        frame.x = 70
        frame.y = 80
        pos = frame.pos
        if pos.x == 70 and pos.y == 80:
            print(f"✓ PASS: pos property reflects x/y changes")
            tests_passed += 1
        else:
            print(f"✗ FAIL: pos doesn't reflect changes: {pos.x}, {pos.y}")
    except Exception as e:
        print(f"✗ FAIL: pos getter after change error: {e}")
    
    return tests_passed, tests_total

def test_sprite_pos_property():
    """Test pos property on Sprite"""
    print("\n=== Testing Sprite pos Property ===")
    
    tests_passed = 0
    tests_total = 0
    
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    
    # Test 1: Get pos property
    tests_total += 1
    try:
        sprite = mcrfpy.Sprite(10, 20, texture, 0, 1.0)
        pos = sprite.pos
        if hasattr(pos, 'x') and hasattr(pos, 'y') and pos.x == 10 and pos.y == 20:
            print(f"✓ PASS: sprite.pos returns Vector({pos.x}, {pos.y})")
            tests_passed += 1
        else:
            print(f"✗ FAIL: sprite.pos incorrect: {pos}")
    except AttributeError as e:
        print(f"✗ FAIL: pos property not accessible: {e}")
    
    # Test 2: Set pos with Vector
    tests_total += 1
    try:
        vec = mcrfpy.Vector(30, 40)
        sprite.pos = vec
        if sprite.x == 30 and sprite.y == 40:
            print(f"✓ PASS: sprite.pos = Vector sets position correctly")
            tests_passed += 1
        else:
            print(f"✗ FAIL: pos setter failed: x={sprite.x}, y={sprite.y}")
    except Exception as e:
        print(f"✗ FAIL: pos setter with Vector error: {e}")
    
    # Test 3: Set pos with tuple
    tests_total += 1
    try:
        sprite.pos = (50, 60)
        if sprite.x == 50 and sprite.y == 60:
            print(f"✓ PASS: sprite.pos = tuple sets position correctly")
            tests_passed += 1
        else:
            print(f"✗ FAIL: pos setter with tuple failed: x={sprite.x}, y={sprite.y}")
    except Exception as e:
        print(f"✗ FAIL: pos setter with tuple error: {e}")
    
    # Test 4: Verify pos getter reflects changes
    tests_total += 1
    try:
        sprite.x = 70
        sprite.y = 80
        pos = sprite.pos
        if pos.x == 70 and pos.y == 80:
            print(f"✓ PASS: pos property reflects x/y changes")
            tests_passed += 1
        else:
            print(f"✗ FAIL: pos doesn't reflect changes: {pos.x}, {pos.y}")
    except Exception as e:
        print(f"✗ FAIL: pos getter after change error: {e}")
    
    return tests_passed, tests_total

def test_consistency_with_caption_entity():
    """Test that pos property is consistent across all UI elements"""
    print("\n=== Testing Consistency with Caption/Entity ===")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Caption pos property (should already exist)
    tests_total += 1
    try:
        font = mcrfpy.Font("assets/JetbrainsMono.ttf")
        caption = mcrfpy.Caption((10, 20), "Test", font)
        pos = caption.pos
        if hasattr(pos, 'x') and hasattr(pos, 'y'):
            print(f"✓ PASS: Caption.pos works as expected")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Caption.pos doesn't return Vector")
    except Exception as e:
        print(f"✗ FAIL: Caption.pos error: {e}")
    
    # Test 2: Entity draw_pos property (should already exist)
    tests_total += 1
    try:
        entity = mcrfpy.Entity((10, 20))
        pos = entity.draw_pos
        if hasattr(pos, 'x') and hasattr(pos, 'y'):
            print(f"✓ PASS: Entity.draw_pos works as expected")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Entity.draw_pos doesn't return Vector")
    except Exception as e:
        print(f"✗ FAIL: Entity.draw_pos error: {e}")
    
    # Test 3: All pos properties return same type
    tests_total += 1
    try:
        texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
        frame = mcrfpy.Frame(10, 20, 100, 50)
        sprite = mcrfpy.Sprite(10, 20, texture, 0, 1.0)
        
        frame_pos = frame.pos
        sprite_pos = sprite.pos
        
        if (type(frame_pos).__name__ == type(sprite_pos).__name__ == 'Vector'):
            print(f"✓ PASS: All pos properties return Vector type")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Inconsistent pos property types")
    except Exception as e:
        print(f"✗ FAIL: Type consistency check error: {e}")
    
    return tests_passed, tests_total

def run_test(runtime):
    """Timer callback to run the test"""
    try:
        print("=== Testing pos Property for Frame and Sprite (Issue #84) ===\n")
        
        frame_passed, frame_total = test_frame_pos_property()
        sprite_passed, sprite_total = test_sprite_pos_property()
        consistency_passed, consistency_total = test_consistency_with_caption_entity()
        
        total_passed = frame_passed + sprite_passed + consistency_passed
        total_tests = frame_total + sprite_total + consistency_total
        
        print(f"\n=== SUMMARY ===")
        print(f"Frame tests: {frame_passed}/{frame_total}")
        print(f"Sprite tests: {sprite_passed}/{sprite_total}")
        print(f"Consistency tests: {consistency_passed}/{consistency_total}")
        print(f"Total tests passed: {total_passed}/{total_tests}")
        
        if total_passed == total_tests:
            print("\nIssue #84 FIXED: pos property added to Frame and Sprite!")
            print("\nOverall result: PASS")
        else:
            print("\nIssue #84: Some tests failed")
            print("\nOverall result: FAIL")
            
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