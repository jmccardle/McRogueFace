#!/usr/bin/env python3
"""Test mcrfpy default resources."""
import mcrfpy
import sys

scene = mcrfpy.Scene("test")
scene.activate()
mcrfpy.step(0.01)

print("Checking mcrfpy defaults:")

try:
    dt = mcrfpy.default_texture
    print(f"  default_texture = {dt}")
except AttributeError as e:
    print(f"  default_texture: NOT FOUND")

try:
    df = mcrfpy.default_font
    print(f"  default_font = {df}")
except AttributeError as e:
    print(f"  default_font: NOT FOUND")

# Also check what other module-level attributes exist
print("\nAll mcrfpy attributes starting with 'default':")
for attr in dir(mcrfpy):
    if 'default' in attr.lower():
        print(f"  {attr}")

sys.exit(0)
