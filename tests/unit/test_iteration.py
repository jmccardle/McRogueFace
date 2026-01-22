#!/usr/bin/env python3
"""Test iteration works with hidden types"""
import sys
import mcrfpy

print("Step 1: Creating scene...")
scene = mcrfpy.Scene("test_scene")
print(f"  scene: {scene}")

print("Step 2: Getting children...")
ui = scene.children
print(f"  children: {ui}")

print("Step 3: Creating Frame...")
frame = mcrfpy.Frame(pos=(0,0), size=(50,50))
print(f"  frame: {frame}")

print("Step 4: Appending Frame...")
ui.append(frame)
print(f"  append succeeded, len={len(ui)}")

print("Step 5: Creating Caption...")
caption = mcrfpy.Caption(text="hi", pos=(0,0))
print(f"  caption: {caption}")

print("Step 6: Appending Caption...")
ui.append(caption)
print(f"  append succeeded, len={len(ui)}")

print("Step 7: Starting iteration...")
count = 0
for item in ui:
    count += 1
    print(f"  Item {count}: {item}")

print(f"Step 8: Iteration complete, {count} items")

if count == 2:
    print("PASS")
    sys.exit(0)
else:
    print(f"FAIL: expected 2 items, got {count}")
    sys.exit(1)
