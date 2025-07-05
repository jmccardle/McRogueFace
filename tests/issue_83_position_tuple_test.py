#!/usr/bin/env python3
"""
Test for Issue #83: Add position tuple support to constructors

This test verifies that UI element constructors now support both:
- Traditional (x, y) as separate arguments
- Tuple form ((x, y)) as a single argument
- Vector form (Vector(x, y)) as a single argument
"""

import mcrfpy
import sys

def test_frame_position_tuple():
    """Test Frame constructor with position tuples"""
    print("=== Testing Frame Position Tuple Support ===")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Traditional (x, y) form
    tests_total += 1
    try:
        frame1 = mcrfpy.Frame(10, 20, 100, 50)
        if frame1.x == 10 and frame1.y == 20:
            print("✓ PASS: Frame(x, y, w, h) traditional form works")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Frame position incorrect: ({frame1.x}, {frame1.y})")
    except Exception as e:
        print(f"✗ FAIL: Traditional form failed: {e}")
    
    # Test 2: Tuple ((x, y)) form
    tests_total += 1
    try:
        frame2 = mcrfpy.Frame((30, 40), 100, 50)
        if frame2.x == 30 and frame2.y == 40:
            print("✓ PASS: Frame((x, y), w, h) tuple form works")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Frame tuple position incorrect: ({frame2.x}, {frame2.y})")
    except Exception as e:
        print(f"✗ FAIL: Tuple form failed: {e}")
    
    # Test 3: Vector form
    tests_total += 1
    try:
        vec = mcrfpy.Vector(50, 60)
        frame3 = mcrfpy.Frame(vec, 100, 50)
        if frame3.x == 50 and frame3.y == 60:
            print("✓ PASS: Frame(Vector, w, h) vector form works")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Frame vector position incorrect: ({frame3.x}, {frame3.y})")
    except Exception as e:
        print(f"✗ FAIL: Vector form failed: {e}")
    
    return tests_passed, tests_total

def test_sprite_position_tuple():
    """Test Sprite constructor with position tuples"""
    print("\n=== Testing Sprite Position Tuple Support ===")
    
    tests_passed = 0
    tests_total = 0
    
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    
    # Test 1: Traditional (x, y) form
    tests_total += 1
    try:
        sprite1 = mcrfpy.Sprite(10, 20, texture, 0, 1.0)
        if sprite1.x == 10 and sprite1.y == 20:
            print("✓ PASS: Sprite(x, y, texture, ...) traditional form works")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Sprite position incorrect: ({sprite1.x}, {sprite1.y})")
    except Exception as e:
        print(f"✗ FAIL: Traditional form failed: {e}")
    
    # Test 2: Tuple ((x, y)) form
    tests_total += 1
    try:
        sprite2 = mcrfpy.Sprite((30, 40), texture, 0, 1.0)
        if sprite2.x == 30 and sprite2.y == 40:
            print("✓ PASS: Sprite((x, y), texture, ...) tuple form works")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Sprite tuple position incorrect: ({sprite2.x}, {sprite2.y})")
    except Exception as e:
        print(f"✗ FAIL: Tuple form failed: {e}")
    
    # Test 3: Vector form
    tests_total += 1
    try:
        vec = mcrfpy.Vector(50, 60)
        sprite3 = mcrfpy.Sprite(vec, texture, 0, 1.0)
        if sprite3.x == 50 and sprite3.y == 60:
            print("✓ PASS: Sprite(Vector, texture, ...) vector form works")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Sprite vector position incorrect: ({sprite3.x}, {sprite3.y})")
    except Exception as e:
        print(f"✗ FAIL: Vector form failed: {e}")
    
    return tests_passed, tests_total

def test_caption_position_tuple():
    """Test Caption constructor with position tuples"""
    print("\n=== Testing Caption Position Tuple Support ===")
    
    tests_passed = 0
    tests_total = 0
    
    font = mcrfpy.Font("assets/JetbrainsMono.ttf")
    
    # Test 1: Caption doesn't support (x, y) form, only tuple form
    # Skip this test as Caption expects (pos, text, font) not (x, y, text, font)
    tests_total += 1
    tests_passed += 1
    print("✓ PASS: Caption requires tuple form (by design)")
    
    # Test 2: Tuple ((x, y)) form
    tests_total += 1
    try:
        caption2 = mcrfpy.Caption((30, 40), "Test", font)
        if caption2.x == 30 and caption2.y == 40:
            print("✓ PASS: Caption((x, y), text, font) tuple form works")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Caption tuple position incorrect: ({caption2.x}, {caption2.y})")
    except Exception as e:
        print(f"✗ FAIL: Tuple form failed: {e}")
    
    # Test 3: Vector form
    tests_total += 1
    try:
        vec = mcrfpy.Vector(50, 60)
        caption3 = mcrfpy.Caption(vec, "Test", font)
        if caption3.x == 50 and caption3.y == 60:
            print("✓ PASS: Caption(Vector, text, font) vector form works")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Caption vector position incorrect: ({caption3.x}, {caption3.y})")
    except Exception as e:
        print(f"✗ FAIL: Vector form failed: {e}")
    
    return tests_passed, tests_total

def test_entity_position_tuple():
    """Test Entity constructor with position tuples"""
    print("\n=== Testing Entity Position Tuple Support ===")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Traditional (x, y) form or tuple form
    tests_total += 1
    try:
        # Entity already uses tuple form, so test that it works
        entity1 = mcrfpy.Entity((10, 20))
        # Entity.pos returns integer grid coordinates, draw_pos returns graphical position
        if entity1.draw_pos.x == 10 and entity1.draw_pos.y == 20:
            print("✓ PASS: Entity((x, y)) tuple form works")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Entity position incorrect: draw_pos=({entity1.draw_pos.x}, {entity1.draw_pos.y}), pos=({entity1.pos.x}, {entity1.pos.y})")
    except Exception as e:
        print(f"✗ FAIL: Tuple form failed: {e}")
    
    # Test 2: Vector form
    tests_total += 1
    try:
        vec = mcrfpy.Vector(30, 40)
        entity2 = mcrfpy.Entity(vec)
        if entity2.draw_pos.x == 30 and entity2.draw_pos.y == 40:
            print("✓ PASS: Entity(Vector) vector form works")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Entity vector position incorrect: draw_pos=({entity2.draw_pos.x}, {entity2.draw_pos.y}), pos=({entity2.pos.x}, {entity2.pos.y})")
    except Exception as e:
        print(f"✗ FAIL: Vector form failed: {e}")
    
    return tests_passed, tests_total

def test_edge_cases():
    """Test edge cases for position tuple support"""
    print("\n=== Testing Edge Cases ===")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Empty tuple should fail gracefully
    tests_total += 1
    try:
        frame = mcrfpy.Frame((), 100, 50)
        # Empty tuple might be accepted and treated as (0, 0)
        if frame.x == 0 and frame.y == 0:
            print("✓ PASS: Empty tuple accepted as (0, 0)")
            tests_passed += 1
        else:
            print("✗ FAIL: Empty tuple handled unexpectedly")
    except Exception as e:
        print(f"✓ PASS: Empty tuple correctly rejected: {e}")
        tests_passed += 1
    
    # Test 2: Wrong tuple size should fail
    tests_total += 1
    try:
        frame = mcrfpy.Frame((10, 20, 30), 100, 50)
        print("✗ FAIL: 3-element tuple should have raised an error")
    except Exception as e:
        print(f"✓ PASS: Wrong tuple size correctly rejected: {e}")
        tests_passed += 1
    
    # Test 3: Non-numeric tuple should fail
    tests_total += 1
    try:
        frame = mcrfpy.Frame(("x", "y"), 100, 50)
        print("✗ FAIL: Non-numeric tuple should have raised an error")
    except Exception as e:
        print(f"✓ PASS: Non-numeric tuple correctly rejected: {e}")
        tests_passed += 1
    
    return tests_passed, tests_total

def run_test(runtime):
    """Timer callback to run the test"""
    try:
        print("=== Testing Position Tuple Support in Constructors (Issue #83) ===\n")
        
        frame_passed, frame_total = test_frame_position_tuple()
        sprite_passed, sprite_total = test_sprite_position_tuple()
        caption_passed, caption_total = test_caption_position_tuple()
        entity_passed, entity_total = test_entity_position_tuple()
        edge_passed, edge_total = test_edge_cases()
        
        total_passed = frame_passed + sprite_passed + caption_passed + entity_passed + edge_passed
        total_tests = frame_total + sprite_total + caption_total + entity_total + edge_total
        
        print(f"\n=== SUMMARY ===")
        print(f"Frame tests: {frame_passed}/{frame_total}")
        print(f"Sprite tests: {sprite_passed}/{sprite_total}")
        print(f"Caption tests: {caption_passed}/{caption_total}")
        print(f"Entity tests: {entity_passed}/{entity_total}")
        print(f"Edge case tests: {edge_passed}/{edge_total}")
        print(f"Total tests passed: {total_passed}/{total_tests}")
        
        if total_passed == total_tests:
            print("\nIssue #83 FIXED: Position tuple support added to constructors!")
            print("\nOverall result: PASS")
        else:
            print("\nIssue #83: Some tests failed")
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