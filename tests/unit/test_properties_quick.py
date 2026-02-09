#!/usr/bin/env python3
"""Quick test of drawable properties"""
import mcrfpy
import sys

# Initialize scene
test = mcrfpy.Scene("test")
mcrfpy.current_scene = test

print("\n=== Testing Properties ===")

all_pass = True

# Test Frame
try:
    frame = mcrfpy.Frame(pos=(10, 10), size=(100, 100))
    print(f"Frame visible: {frame.visible}")
    frame.visible = False
    print(f"Frame visible after setting to False: {frame.visible}")

    print(f"Frame opacity: {frame.opacity}")
    frame.opacity = 0.5
    print(f"Frame opacity after setting to 0.5: {frame.opacity}")

    bounds = frame.bounds
    print(f"Frame bounds: pos={bounds[0]}, size={bounds[1]}")

    frame.x += 5
    frame.y += 5
    bounds2 = frame.bounds
    print(f"Frame bounds after move: pos={bounds2[0]}, size={bounds2[1]}")

    print("+ Frame properties work!")
except Exception as e:
    print(f"x Frame failed: {e}")
    all_pass = False

# Test Entity
try:
    entity = mcrfpy.Entity()
    print(f"\nEntity visible: {entity.visible}")
    entity.visible = False
    print(f"Entity visible after setting to False: {entity.visible}")

    print(f"Entity opacity: {entity.opacity}")
    entity.opacity = 0.7
    print(f"Entity opacity after setting to 0.7: {entity.opacity}")

    print("+ Entity properties work!")
except Exception as e:
    print(f"x Entity failed: {e}")
    all_pass = False

if all_pass:
    print("\nPASS", file=sys.stderr)
    sys.exit(0)
else:
    print("\nFAIL", file=sys.stderr)
    sys.exit(1)
