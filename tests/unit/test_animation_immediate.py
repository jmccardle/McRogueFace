#!/usr/bin/env python3
"""
Test Animation creation without timer
"""

import mcrfpy

print("1. Creating scene...")
test = mcrfpy.Scene("test")
test.activate()

print("2. Getting UI...")
ui = test.children

print("3. Creating frame...")
frame = mcrfpy.Frame(pos=(100, 100), size=(200, 200))
ui.append(frame)

print("4. Creating Animation object...")
try:
    anim = mcrfpy.Animation("x", 500.0, 2000, "easeInOut")
    print("5. Animation created successfully!")
except Exception as e:
    print(f"5. Animation creation failed: {e}")

print("6. Starting animation...")
try:
    anim.start(frame)
    print("7. Animation started!")
except Exception as e:
    print(f"7. Animation start failed: {e}")

print("8. Script completed without crash!")