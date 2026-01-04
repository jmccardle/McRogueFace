#!/usr/bin/env python3
"""Test the new .animate() shorthand method on UIDrawable and UIEntity.

This tests issue #177 - ergonomic animation API.
"""
import mcrfpy
import sys

def test_frame_animate():
    """Test animate() on Frame"""
    frame = mcrfpy.Frame(pos=(100, 100), size=(200, 200))

    # Basic float property animation
    anim = frame.animate("x", 300.0, 1.0)
    assert anim is not None, "animate() should return an Animation object"

    # Color property animation
    anim2 = frame.animate("fill_color", (255, 0, 0, 255), 0.5)
    assert anim2 is not None

    # Vector property animation
    anim3 = frame.animate("position", (400.0, 400.0), 0.5)
    assert anim3 is not None

    print("  Frame animate() - PASS")

def test_caption_animate():
    """Test animate() on Caption"""
    caption = mcrfpy.Caption(text="Hello", pos=(50, 50))

    # Position animation
    anim = caption.animate("y", 200.0, 1.0)
    assert anim is not None

    # Font size animation
    anim2 = caption.animate("font_size", 24.0, 0.5)
    assert anim2 is not None

    print("  Caption animate() - PASS")

def test_sprite_animate():
    """Test animate() on Sprite"""
    # Create with default texture
    sprite = mcrfpy.Sprite(pos=(100, 100))

    # Scale animation
    anim = sprite.animate("scale", 2.0, 1.0)
    assert anim is not None

    # Sprite index animation
    anim2 = sprite.animate("sprite_index", 5, 0.5)
    assert anim2 is not None

    print("  Sprite animate() - PASS")

def test_grid_animate():
    """Test animate() on Grid"""
    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(50, 50), size=(300, 300))

    # Zoom animation
    anim = grid.animate("zoom", 2.0, 1.0)
    assert anim is not None

    # Center animation
    anim2 = grid.animate("center", (100.0, 100.0), 0.5)
    assert anim2 is not None

    print("  Grid animate() - PASS")

def test_entity_animate():
    """Test animate() on Entity"""
    grid = mcrfpy.Grid(grid_size=(20, 20))
    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)

    # Position animation
    anim = entity.animate("x", 10.0, 1.0)
    assert anim is not None

    anim2 = entity.animate("y", 15.0, 1.0)
    assert anim2 is not None

    # Sprite index animation
    anim3 = entity.animate("sprite_index", 3, 0.5)
    assert anim3 is not None

    print("  Entity animate() - PASS")

def test_invalid_property_raises():
    """Test that invalid property names raise ValueError"""
    frame = mcrfpy.Frame()

    try:
        frame.animate("invalid_property", 100.0, 1.0)
        print("  ERROR: Should have raised ValueError for invalid property")
        return False
    except ValueError as e:
        # Should contain the property name in the error message
        if "invalid_property" in str(e):
            print("  Invalid property detection - PASS")
            return True
        else:
            print(f"  ERROR: ValueError message doesn't mention property: {e}")
            return False
    except Exception as e:
        print(f"  ERROR: Wrong exception type: {type(e).__name__}: {e}")
        return False

def test_entity_invalid_property():
    """Test that invalid property names raise ValueError for Entity"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    entity = mcrfpy.Entity(grid=grid)

    try:
        entity.animate("invalid_property", 100.0, 1.0)
        print("  ERROR: Should have raised ValueError for invalid Entity property")
        return False
    except ValueError as e:
        if "invalid_property" in str(e):
            print("  Entity invalid property detection - PASS")
            return True
        else:
            print(f"  ERROR: ValueError message doesn't mention property: {e}")
            return False
    except Exception as e:
        print(f"  ERROR: Wrong exception type: {type(e).__name__}: {e}")
        return False

def test_easing_options():
    """Test various easing parameter formats"""
    frame = mcrfpy.Frame()

    # String easing
    anim1 = frame.animate("x", 100.0, 1.0, "easeInOut")
    assert anim1 is not None, "String easing should work"

    # Easing enum (if available)
    try:
        anim2 = frame.animate("x", 100.0, 1.0, mcrfpy.Easing.EaseIn)
        assert anim2 is not None, "Enum easing should work"
    except AttributeError:
        pass  # Easing enum might not exist

    # None for linear
    anim3 = frame.animate("x", 100.0, 1.0, None)
    assert anim3 is not None, "None easing (linear) should work"

    print("  Easing options - PASS")

def test_delta_mode():
    """Test delta=True for relative animations"""
    frame = mcrfpy.Frame(pos=(100, 100))

    # Absolute animation (default)
    anim1 = frame.animate("x", 200.0, 1.0, delta=False)
    assert anim1 is not None

    # Relative animation
    anim2 = frame.animate("x", 50.0, 1.0, delta=True)
    assert anim2 is not None

    print("  Delta mode - PASS")

def test_callback():
    """Test callback parameter"""
    frame = mcrfpy.Frame()
    callback_called = [False]  # Use list for mutability in closure

    def my_callback():
        callback_called[0] = True

    anim = frame.animate("x", 100.0, 0.01, callback=my_callback)
    assert anim is not None, "Animation with callback should be created"

    print("  Callback parameter - PASS")

def run_tests():
    """Run all tests"""
    print("Testing .animate() shorthand method:")

    all_passed = True

    # Test UIDrawable types
    try:
        test_frame_animate()
    except Exception as e:
        print(f"  Frame animate() - FAIL: {e}")
        all_passed = False

    try:
        test_caption_animate()
    except Exception as e:
        print(f"  Caption animate() - FAIL: {e}")
        all_passed = False

    try:
        test_sprite_animate()
    except Exception as e:
        print(f"  Sprite animate() - FAIL: {e}")
        all_passed = False

    try:
        test_grid_animate()
    except Exception as e:
        print(f"  Grid animate() - FAIL: {e}")
        all_passed = False

    try:
        test_entity_animate()
    except Exception as e:
        print(f"  Entity animate() - FAIL: {e}")
        all_passed = False

    # Test property validation
    if not test_invalid_property_raises():
        all_passed = False

    if not test_entity_invalid_property():
        all_passed = False

    # Test optional parameters
    try:
        test_easing_options()
    except Exception as e:
        print(f"  Easing options - FAIL: {e}")
        all_passed = False

    try:
        test_delta_mode()
    except Exception as e:
        print(f"  Delta mode - FAIL: {e}")
        all_passed = False

    try:
        test_callback()
    except Exception as e:
        print(f"  Callback parameter - FAIL: {e}")
        all_passed = False

    if all_passed:
        print("\nAll tests PASSED!")
        sys.exit(0)
    else:
        print("\nSome tests FAILED!")
        sys.exit(1)

# Run tests immediately (no timer needed for this test)
run_tests()

