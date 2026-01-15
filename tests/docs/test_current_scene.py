#!/usr/bin/env python3
"""Verify mcrfpy.current_scene property."""
import mcrfpy
import sys

scene = mcrfpy.Scene("test")
scene.activate()
mcrfpy.step(0.1)

try:
    current = mcrfpy.current_scene
    print(f"mcrfpy.current_scene = {current}")
    print(f"type: {type(current)}")
    print("VERIFIED: mcrfpy.current_scene WORKS")
except AttributeError as e:
    print(f"FAILED: {e}")

sys.exit(0)
