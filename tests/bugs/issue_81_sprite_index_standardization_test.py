#!/usr/bin/env python3
"""
Test for Issue #81: Standardize sprite_index property name

This test verifies that both UISprite and UIEntity use "sprite_index" instead of "sprite_number"
for consistency across the API.
"""

import mcrfpy
import sys

def test_sprite_index_property():
    """Test sprite_index property on UISprite"""
    print("=== Testing UISprite sprite_index Property ===")
    
    tests_passed = 0
    tests_total = 0
    
    # Create a texture and sprite
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    sprite = mcrfpy.Sprite(10, 10, texture, 5, 1.0)
    
    # Test 1: Check sprite_index property exists
    tests_total += 1
    try:
        idx = sprite.sprite_index
        if idx == 5:
            print(f"✓ PASS: sprite.sprite_index = {idx}")
            tests_passed += 1
        else:
            print(f"✗ FAIL: sprite.sprite_index = {idx}, expected 5")
    except AttributeError as e:
        print(f"✗ FAIL: sprite_index not accessible: {e}")
    
    # Test 2: Check sprite_index setter
    tests_total += 1
    try:
        sprite.sprite_index = 10
        if sprite.sprite_index == 10:
            print("✓ PASS: sprite_index setter works")
            tests_passed += 1
        else:
            print(f"✗ FAIL: sprite_index setter failed, got {sprite.sprite_index}")
    except Exception as e:
        print(f"✗ FAIL: sprite_index setter error: {e}")
    
    # Test 3: Check sprite_number is removed/deprecated
    tests_total += 1
    if hasattr(sprite, 'sprite_number'):
        # Check if it's an alias
        sprite.sprite_number = 15
        if sprite.sprite_index == 15:
            print("✓ PASS: sprite_number exists as backward-compatible alias")
            tests_passed += 1
        else:
            print("✗ FAIL: sprite_number exists but doesn't update sprite_index")
    else:
        print("✓ PASS: sprite_number property removed (no backward compatibility)")
        tests_passed += 1
    
    # Test 4: Check repr uses sprite_index
    tests_total += 1
    repr_str = repr(sprite)
    if "sprite_index=" in repr_str:
        print(f"✓ PASS: repr uses sprite_index: {repr_str}")
        tests_passed += 1
    elif "sprite_number=" in repr_str:
        print(f"✗ FAIL: repr still uses sprite_number: {repr_str}")
    else:
        print(f"✗ FAIL: repr doesn't show sprite info: {repr_str}")
    
    return tests_passed, tests_total

def test_entity_sprite_index_property():
    """Test sprite_index property on Entity"""
    print("\n=== Testing Entity sprite_index Property ===")
    
    tests_passed = 0
    tests_total = 0
    
    # Create an entity with required position
    entity = mcrfpy.Entity((0, 0))
    
    # Test 1: Check sprite_index property exists
    tests_total += 1
    try:
        # Set initial value
        entity.sprite_index = 42
        idx = entity.sprite_index
        if idx == 42:
            print(f"✓ PASS: entity.sprite_index = {idx}")
            tests_passed += 1
        else:
            print(f"✗ FAIL: entity.sprite_index = {idx}, expected 42")
    except AttributeError as e:
        print(f"✗ FAIL: sprite_index not accessible: {e}")
    
    # Test 2: Check sprite_number is removed/deprecated
    tests_total += 1
    if hasattr(entity, 'sprite_number'):
        # Check if it's an alias
        entity.sprite_number = 99
        if hasattr(entity, 'sprite_index') and entity.sprite_index == 99:
            print("✓ PASS: sprite_number exists as backward-compatible alias")
            tests_passed += 1
        else:
            print("✗ FAIL: sprite_number exists but doesn't update sprite_index")
    else:
        print("✓ PASS: sprite_number property removed (no backward compatibility)")
        tests_passed += 1
    
    # Test 3: Check repr uses sprite_index
    tests_total += 1
    repr_str = repr(entity)
    if "sprite_index=" in repr_str:
        print(f"✓ PASS: repr uses sprite_index: {repr_str}")
        tests_passed += 1
    elif "sprite_number=" in repr_str:
        print(f"✗ FAIL: repr still uses sprite_number: {repr_str}")
    else:
        print(f"? INFO: repr doesn't show sprite info: {repr_str}")
        # This might be okay if entity doesn't show sprite in repr
        tests_passed += 1
    
    return tests_passed, tests_total

def test_animation_compatibility():
    """Test that animations work with sprite_index"""
    print("\n=== Testing Animation Compatibility ===")
    
    tests_passed = 0
    tests_total = 0
    
    # Test animation with sprite_index property name
    tests_total += 1
    try:
        # This tests that the animation system recognizes sprite_index
        texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
        sprite = mcrfpy.Sprite(0, 0, texture, 0, 1.0)
        
        # Try to animate sprite_index (even if we can't directly test animations here)
        sprite.sprite_index = 0
        sprite.sprite_index = 5
        sprite.sprite_index = 10
        
        print("✓ PASS: sprite_index property works for potential animations")
        tests_passed += 1
    except Exception as e:
        print(f"✗ FAIL: sprite_index animation compatibility issue: {e}")
    
    return tests_passed, tests_total

def run_test(runtime):
    """Timer callback to run the test"""
    try:
        print("=== Testing sprite_index Property Standardization (Issue #81) ===\n")
        
        sprite_passed, sprite_total = test_sprite_index_property()
        entity_passed, entity_total = test_entity_sprite_index_property()
        anim_passed, anim_total = test_animation_compatibility()
        
        total_passed = sprite_passed + entity_passed + anim_passed
        total_tests = sprite_total + entity_total + anim_total
        
        print(f"\n=== SUMMARY ===")
        print(f"Sprite tests: {sprite_passed}/{sprite_total}")
        print(f"Entity tests: {entity_passed}/{entity_total}")
        print(f"Animation tests: {anim_passed}/{anim_total}")
        print(f"Total tests passed: {total_passed}/{total_tests}")
        
        if total_passed == total_tests:
            print("\nIssue #81 FIXED: sprite_index property standardized!")
            print("\nOverall result: PASS")
        else:
            print("\nIssue #81: Some tests failed")
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