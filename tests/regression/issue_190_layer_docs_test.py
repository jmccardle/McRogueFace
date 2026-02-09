#!/usr/bin/env python3
"""Test for issue #190: Expanded TileLayer and ColorLayer __init__ documentation.

This test verifies that the documentation for ColorLayer and TileLayer
contains the expected key phrases and is comprehensive.
"""
import mcrfpy
import sys

def test_colorlayer_docs():
    """Test ColorLayer documentation completeness."""
    doc = mcrfpy.ColorLayer.__doc__

    if not doc:
        print("FAIL: ColorLayer.__doc__ is empty or None")
        return False

    print("=== ColorLayer Documentation ===")
    print(doc)
    print()

    # Check for key phrases
    required_phrases = [
        "grid_size",
        "z_index",
        "RGBA",
        "at(x, y)",
        "set(x, y",
        "fill(",
        "add_layer",
        "Example",
    ]

    missing = []
    for phrase in required_phrases:
        if phrase not in doc:
            missing.append(phrase)

    if missing:
        print(f"FAIL: ColorLayer docs missing phrases: {missing}")
        return False

    print("ColorLayer documentation: PASS")
    return True

def test_tilelayer_docs():
    """Test TileLayer documentation completeness."""
    doc = mcrfpy.TileLayer.__doc__

    if not doc:
        print("FAIL: TileLayer.__doc__ is empty or None")
        return False

    print("=== TileLayer Documentation ===")
    print(doc)
    print()

    # Check for key phrases
    required_phrases = [
        "grid_size",
        "z_index",
        "texture",
        "at(x, y)",
        "set(x, y",
        "fill(",
        "-1",  # Special value for no tile
        "sprite",
        "add_layer",
        "Example",
    ]

    missing = []
    for phrase in required_phrases:
        if phrase not in doc:
            missing.append(phrase)

    if missing:
        print(f"FAIL: TileLayer docs missing phrases: {missing}")
        return False

    print("TileLayer documentation: PASS")
    return True

# Run tests
colorlayer_ok = test_colorlayer_docs()
tilelayer_ok = test_tilelayer_docs()

if colorlayer_ok and tilelayer_ok:
    print("\nAll documentation tests PASSED")
    sys.exit(0)
else:
    print("\nDocumentation tests FAILED")
    sys.exit(1)
