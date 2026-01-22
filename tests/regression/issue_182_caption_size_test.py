#!/usr/bin/env python3
"""Test for issue #182: Caption size, w, and h read-only properties.

This test verifies that:
1. Caption.size returns a Vector with the text dimensions
2. Caption.w and Caption.h return float values matching size.x and size.y
3. All three properties are read-only (setting raises AttributeError)
"""

import mcrfpy
import sys

def test_caption_size_properties():
    """Test Caption size, w, and h properties."""

    # Create a caption with some text
    caption = mcrfpy.Caption(text="Hello World", pos=(100, 100), font_size=24)

    # Test 1: size property exists and returns a Vector
    size = caption.size
    print(f"caption.size = {size}")

    # Verify it's a Vector
    assert hasattr(size, 'x') and hasattr(size, 'y'), "size should be a Vector with x and y attributes"
    print(f"  size.x = {size.x}, size.y = {size.y}")

    # Test 2: size values are positive (text has non-zero dimensions)
    assert size.x > 0, f"size.x should be positive, got {size.x}"
    assert size.y > 0, f"size.y should be positive, got {size.y}"
    print("  size values are positive: PASS")

    # Test 3: w and h properties exist and return floats
    w = caption.w
    h = caption.h
    print(f"caption.w = {w}, caption.h = {h}")

    assert isinstance(w, float), f"w should be a float, got {type(w)}"
    assert isinstance(h, float), f"h should be a float, got {type(h)}"
    print("  w and h are floats: PASS")

    # Test 4: w and h match size.x and size.y
    assert abs(w - size.x) < 0.001, f"w ({w}) should match size.x ({size.x})"
    assert abs(h - size.y) < 0.001, f"h ({h}) should match size.y ({size.y})"
    print("  w/h match size.x/size.y: PASS")

    # Test 5: size is read-only
    try:
        caption.size = mcrfpy.Vector(50, 50)
        print("  ERROR: setting size should raise AttributeError")
        sys.exit(1)
    except AttributeError:
        print("  size is read-only: PASS")

    # Test 6: w is read-only
    try:
        caption.w = 100.0
        print("  ERROR: setting w should raise AttributeError")
        sys.exit(1)
    except AttributeError:
        print("  w is read-only: PASS")

    # Test 7: h is read-only
    try:
        caption.h = 50.0
        print("  ERROR: setting h should raise AttributeError")
        sys.exit(1)
    except AttributeError:
        print("  h is read-only: PASS")

    # Test 8: Changing text changes the size
    old_w = caption.w
    caption.text = "Hello World! This is a much longer text."
    new_w = caption.w
    print(f"After changing text: old_w = {old_w}, new_w = {new_w}")
    assert new_w > old_w, f"Longer text should have larger width: {new_w} > {old_w}"
    print("  Changing text updates size: PASS")

    # Test 9: Empty caption has zero or near-zero size
    empty_caption = mcrfpy.Caption(text="", pos=(0, 0))
    print(f"Empty caption: w={empty_caption.w}, h={empty_caption.h}")
    # Note: Even empty text might have some height due to font metrics
    assert empty_caption.w == 0 or empty_caption.w < 1, f"Empty text should have ~zero width, got {empty_caption.w}"
    print("  Empty caption has minimal size: PASS")

    print("\nAll tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_caption_size_properties()
        print("PASS")
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
