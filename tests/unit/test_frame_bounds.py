#!/usr/bin/env python3
"""Test Frame bounds"""
import sys
import mcrfpy

print("Testing Frame bounds...")
frame = mcrfpy.Frame(pos=(50, 100), size=(200, 150))

print(f"Frame created: {frame}")

# Test bounds returns tuple of Vectors
bounds = frame.bounds
print(f"bounds type: {type(bounds)}")
print(f"bounds value: {bounds}")

if not isinstance(bounds, tuple):
    print(f"FAIL: bounds should be tuple, got {type(bounds)}")
    sys.exit(1)

if len(bounds) != 2:
    print(f"FAIL: bounds should have 2 elements, got {len(bounds)}")
    sys.exit(1)

pos, size = bounds
print(f"pos type: {type(pos)}, value: {pos}")
print(f"size type: {type(size)}, value: {size}")

if not hasattr(pos, 'x'):
    print(f"FAIL: pos should be Vector (has no .x), got {type(pos)}")
    sys.exit(1)

print(f"pos.x={pos.x}, pos.y={pos.y}")
print(f"size.x={size.x}, size.y={size.y}")

# Test get_bounds() method is removed (#185)
if hasattr(frame, 'get_bounds'):
    print("FAIL: get_bounds() method should be removed")
    sys.exit(1)
else:
    print("PASS: get_bounds() method is removed")

print("PASS: Frame bounds test passed!")
sys.exit(0)
