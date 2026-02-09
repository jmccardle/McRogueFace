#!/usr/bin/env python3
"""
Test for Issue #99: Expose Texture and Font properties

This test verifies that Texture and Font objects now expose their properties
as read-only attributes.
"""

import mcrfpy
import sys

def test_texture_properties():
    """Test Texture properties"""
    print("=== Testing Texture Properties ===")

    tests_passed = 0
    tests_total = 0

    # Create a texture
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

    # Test 1: sprite_width property
    tests_total += 1
    try:
        width = texture.sprite_width
        if width == 16:
            print(f"PASS: sprite_width = {width}")
            tests_passed += 1
        else:
            print(f"FAIL: sprite_width = {width}, expected 16")
    except AttributeError as e:
        print(f"FAIL: sprite_width not accessible: {e}")

    # Test 2: sprite_height property
    tests_total += 1
    try:
        height = texture.sprite_height
        if height == 16:
            print(f"PASS: sprite_height = {height}")
            tests_passed += 1
        else:
            print(f"FAIL: sprite_height = {height}, expected 16")
    except AttributeError as e:
        print(f"FAIL: sprite_height not accessible: {e}")

    # Test 3: sheet_width property
    tests_total += 1
    try:
        sheet_w = texture.sheet_width
        if isinstance(sheet_w, int) and sheet_w > 0:
            print(f"PASS: sheet_width = {sheet_w}")
            tests_passed += 1
        else:
            print(f"FAIL: sheet_width invalid: {sheet_w}")
    except AttributeError as e:
        print(f"FAIL: sheet_width not accessible: {e}")

    # Test 4: sheet_height property
    tests_total += 1
    try:
        sheet_h = texture.sheet_height
        if isinstance(sheet_h, int) and sheet_h > 0:
            print(f"PASS: sheet_height = {sheet_h}")
            tests_passed += 1
        else:
            print(f"FAIL: sheet_height invalid: {sheet_h}")
    except AttributeError as e:
        print(f"FAIL: sheet_height not accessible: {e}")

    # Test 5: sprite_count property
    tests_total += 1
    try:
        count = texture.sprite_count
        expected = texture.sheet_width * texture.sheet_height
        if count == expected:
            print(f"PASS: sprite_count = {count} (sheet_width * sheet_height)")
            tests_passed += 1
        else:
            print(f"FAIL: sprite_count = {count}, expected {expected}")
    except AttributeError as e:
        print(f"FAIL: sprite_count not accessible: {e}")

    # Test 6: source property
    tests_total += 1
    try:
        source = texture.source
        if "kenney_tinydungeon.png" in source:
            print(f"PASS: source = '{source}'")
            tests_passed += 1
        else:
            print(f"FAIL: source unexpected: '{source}'")
    except AttributeError as e:
        print(f"FAIL: source not accessible: {e}")

    # Test 7: Properties are read-only
    tests_total += 1
    try:
        texture.sprite_width = 32  # Should fail
        print("FAIL: sprite_width should be read-only")
    except AttributeError as e:
        print(f"PASS: sprite_width is read-only: {e}")
        tests_passed += 1

    return tests_passed, tests_total

def test_font_properties():
    """Test Font properties"""
    print("\n=== Testing Font Properties ===")

    tests_passed = 0
    tests_total = 0

    # Create a font
    font = mcrfpy.Font("assets/JetbrainsMono.ttf")

    # Test 1: family property
    tests_total += 1
    try:
        family = font.family
        if isinstance(family, str) and len(family) > 0:
            print(f"PASS: family = '{family}'")
            tests_passed += 1
        else:
            print(f"FAIL: family invalid: '{family}'")
    except AttributeError as e:
        print(f"FAIL: family not accessible: {e}")

    # Test 2: source property
    tests_total += 1
    try:
        source = font.source
        if "JetbrainsMono.ttf" in source:
            print(f"PASS: source = '{source}'")
            tests_passed += 1
        else:
            print(f"FAIL: source unexpected: '{source}'")
    except AttributeError as e:
        print(f"FAIL: source not accessible: {e}")

    # Test 3: Properties are read-only
    tests_total += 1
    try:
        font.family = "Arial"  # Should fail
        print("FAIL: family should be read-only")
    except AttributeError as e:
        print(f"PASS: family is read-only: {e}")
        tests_passed += 1

    return tests_passed, tests_total

def test_property_introspection():
    """Test that properties appear in dir()"""
    print("\n=== Testing Property Introspection ===")

    tests_passed = 0
    tests_total = 0

    # Test Texture properties in dir()
    tests_total += 1
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    texture_props = dir(texture)
    expected_texture_props = ['sprite_width', 'sprite_height', 'sheet_width', 'sheet_height', 'sprite_count', 'source']

    missing = [p for p in expected_texture_props if p not in texture_props]
    if not missing:
        print("PASS: All Texture properties appear in dir()")
        tests_passed += 1
    else:
        print(f"FAIL: Missing Texture properties in dir(): {missing}")

    # Test Font properties in dir()
    tests_total += 1
    font = mcrfpy.Font("assets/JetbrainsMono.ttf")
    font_props = dir(font)
    expected_font_props = ['family', 'source']

    missing = [p for p in expected_font_props if p not in font_props]
    if not missing:
        print("PASS: All Font properties appear in dir()")
        tests_passed += 1
    else:
        print(f"FAIL: Missing Font properties in dir(): {missing}")

    return tests_passed, tests_total

# Set up the test scene
test = mcrfpy.Scene("test")
mcrfpy.current_scene = test

try:
    print("=== Testing Texture and Font Properties (Issue #99) ===\n")

    texture_passed, texture_total = test_texture_properties()
    font_passed, font_total = test_font_properties()
    intro_passed, intro_total = test_property_introspection()

    total_passed = texture_passed + font_passed + intro_passed
    total_tests = texture_total + font_total + intro_total

    print(f"\n=== SUMMARY ===")
    print(f"Texture tests: {texture_passed}/{texture_total}")
    print(f"Font tests: {font_passed}/{font_total}")
    print(f"Introspection tests: {intro_passed}/{intro_total}")
    print(f"Total tests passed: {total_passed}/{total_tests}")

    if total_passed == total_tests:
        print("\nIssue #99 FIXED: Texture and Font properties exposed successfully!")
        print("\nOverall result: PASS")
    else:
        print("\nIssue #99: Some tests failed")
        print("\nOverall result: FAIL")

except Exception as e:
    print(f"\nTest error: {e}")
    import traceback
    traceback.print_exc()
    print("\nOverall result: FAIL")

sys.exit(0)
