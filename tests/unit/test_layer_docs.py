#!/usr/bin/env python3
"""Test layer documentation"""
import sys
import mcrfpy

print("Testing layer documentation (#190)...")

# Verify layer types exist and have docstrings
print("Checking TileLayer...")
if not hasattr(mcrfpy, 'TileLayer'):
    print("FAIL: TileLayer should exist")
    sys.exit(1)

print("Checking ColorLayer...")
if not hasattr(mcrfpy, 'ColorLayer'):
    print("FAIL: ColorLayer should exist")
    sys.exit(1)

# Check that docstrings exist and contain useful info
tile_doc = mcrfpy.TileLayer.__doc__
color_doc = mcrfpy.ColorLayer.__doc__

print(f"TileLayer.__doc__ length: {len(tile_doc) if tile_doc else 0}")
print(f"ColorLayer.__doc__ length: {len(color_doc) if color_doc else 0}")

if tile_doc is None or len(tile_doc) < 50:
    print(f"FAIL: TileLayer should have substantial docstring")
    sys.exit(1)

if color_doc is None or len(color_doc) < 50:
    print(f"FAIL: ColorLayer should have substantial docstring")
    sys.exit(1)

print("PASS: Layer documentation exists!")
sys.exit(0)
