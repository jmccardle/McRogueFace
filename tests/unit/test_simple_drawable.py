#!/usr/bin/env python3
"""Simple test for drawable properties"""
import mcrfpy
import sys

# Initialize scene
test = mcrfpy.Scene("test")
mcrfpy.current_scene = test

try:
    # Test basic functionality
    frame = mcrfpy.Frame(pos=(10, 10), size=(100, 100))
    print(f"Frame created: visible={frame.visible}, opacity={frame.opacity}")

    bounds = frame.bounds
    print(f"Bounds: pos={bounds[0]}, size={bounds[1]}")

    # Test position change
    frame.x = 15
    frame.y = 15
    bounds2 = frame.bounds
    print(f"Bounds after pos change: pos={bounds2[0]}, size={bounds2[1]}")

    # Test size change
    frame.w = 150
    frame.h = 150
    bounds3 = frame.bounds
    print(f"Bounds after resize: pos={bounds3[0]}, size={bounds3[1]}")

    print("PASS", file=sys.stderr)
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}")
    print("FAIL", file=sys.stderr)
    sys.exit(1)
