#!/usr/bin/env python3
"""Simple test to isolate drawable issue
Refactored to use mcrfpy.step() for synchronous execution.
"""
import mcrfpy
import sys

# Initialize scene
test = mcrfpy.Scene("test")
test.activate()
mcrfpy.step(0.01)

try:
    # Test basic functionality
    frame = mcrfpy.Frame(pos=(10, 10), size=(100, 100))
    print(f"Frame created: visible={frame.visible}, opacity={frame.opacity}")

    bounds = frame.get_bounds()
    print(f"Bounds: {bounds}")

    frame.move(5, 5)
    print("Move completed")

    frame.resize(150, 150)
    print("Resize completed")

    print("PASS - No crash!")
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}")
    print("FAIL")
    sys.exit(1)
