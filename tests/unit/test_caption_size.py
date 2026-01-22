#!/usr/bin/env python3
"""Test Caption size/w/h properties"""
import sys
import mcrfpy

print("Testing Caption size/w/h properties...")

font = mcrfpy.Font("assets/JetbrainsMono.ttf")
caption = mcrfpy.Caption(text="Test Caption", pos=(100, 100), font=font)
print(f"Caption created: {caption}")

# Test size property
print("Testing size property...")
size = caption.size
print(f"size type: {type(size)}")
print(f"size value: {size}")

if not hasattr(size, 'x'):
    print(f"FAIL: size should be Vector, got {type(size)}")
    sys.exit(1)

print(f"size.x={size.x}, size.y={size.y}")

if size.x <= 0 or size.y <= 0:
    print(f"FAIL: size should be positive, got ({size.x}, {size.y})")
    sys.exit(1)

# Test w property
print("Testing w property...")
w = caption.w
print(f"w type: {type(w)}, value: {w}")

if not isinstance(w, float):
    print(f"FAIL: w should be float, got {type(w)}")
    sys.exit(1)

if w <= 0:
    print(f"FAIL: w should be positive, got {w}")
    sys.exit(1)

# Test h property
print("Testing h property...")
h = caption.h
print(f"h type: {type(h)}, value: {h}")

if not isinstance(h, float):
    print(f"FAIL: h should be float, got {type(h)}")
    sys.exit(1)

if h <= 0:
    print(f"FAIL: h should be positive, got {h}")
    sys.exit(1)

# Verify w and h match size
if abs(w - size.x) >= 0.001:
    print(f"FAIL: w ({w}) should match size.x ({size.x})")
    sys.exit(1)

if abs(h - size.y) >= 0.001:
    print(f"FAIL: h ({h}) should match size.y ({size.y})")
    sys.exit(1)

# Verify read-only
print("Checking that size/w/h are read-only...")
try:
    caption.size = mcrfpy.Vector(100, 100)
    print("FAIL: size should be read-only")
    sys.exit(1)
except AttributeError:
    print("  size is correctly read-only")

try:
    caption.w = 100
    print("FAIL: w should be read-only")
    sys.exit(1)
except AttributeError:
    print("  w is correctly read-only")

try:
    caption.h = 100
    print("FAIL: h should be read-only")
    sys.exit(1)
except AttributeError:
    print("  h is correctly read-only")

print("PASS: Caption size/w/h properties work correctly!")
sys.exit(0)
