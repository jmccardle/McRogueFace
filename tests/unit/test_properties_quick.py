#!/usr/bin/env python3
"""Quick test of drawable properties
Refactored to use mcrfpy.step() for synchronous execution.
"""
import mcrfpy
import sys

# Initialize scene
test = mcrfpy.Scene("test")
test.activate()
mcrfpy.step(0.01)

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

    bounds = frame.get_bounds()
    print(f"Frame bounds: {bounds}")

    frame.move(5, 5)
    bounds2 = frame.get_bounds()
    print(f"Frame bounds after move(5,5): {bounds2}")

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

    bounds = entity.get_bounds()
    print(f"Entity bounds: {bounds}")

    entity.move(3, 3)
    print(f"Entity position after move(3,3): ({entity.x}, {entity.y})")

    print("+ Entity properties work!")
except Exception as e:
    print(f"x Entity failed: {e}")
    all_pass = False

if all_pass:
    print("\nPASS")
    sys.exit(0)
else:
    print("\nFAIL")
    sys.exit(1)
