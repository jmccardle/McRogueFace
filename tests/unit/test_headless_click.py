#!/usr/bin/env python3
"""Test #111: Click Events in Headless Mode"""
import mcrfpy
from mcrfpy import automation
import sys

errors = []

# Test 1: Click hit detection
print("Testing headless click events...")
test_click = mcrfpy.Scene("test_click")
mcrfpy.current_scene = test_click
ui = test_click.children

frame = mcrfpy.Frame(pos=(100, 100), size=(200, 200))
ui.append(frame)

start_clicks = []

def on_click_handler(pos, button, action):
    if action == mcrfpy.InputState.PRESSED:
        start_clicks.append((pos.x, pos.y))

frame.on_click = on_click_handler

# Click inside the frame
automation.click(150, 150)
mcrfpy.step(0.05)

if len(start_clicks) >= 1:
    if abs(start_clicks[0][0] - 150) > 1 or abs(start_clicks[0][1] - 150) > 1:
        errors.append(f"Click position wrong: expected ~(150,150), got {start_clicks[0]}")
else:
    errors.append("No click received on frame")

# Test 2: Click miss (outside element)
print("Testing click miss...")
test_miss = mcrfpy.Scene("test_miss")
mcrfpy.current_scene = test_miss
ui2 = test_miss.children

frame2 = mcrfpy.Frame(pos=(100, 100), size=(100, 100))
ui2.append(frame2)

miss_clicks = []

def on_miss_handler(pos, button, action):
    miss_clicks.append(1)

frame2.on_click = on_miss_handler

# Click outside the frame
automation.click(50, 50)
mcrfpy.step(0.05)

if len(miss_clicks) > 0:
    errors.append(f"Click outside frame should not trigger callback, got {len(miss_clicks)} events")

# Test 3: Position tracking
print("Testing position tracking...")
automation.moveTo(123, 456)
pos = automation.position()
if pos[0] != 123 or pos[1] != 456:
    errors.append(f"Position tracking: expected (123,456), got {pos}")

if errors:
    for err in errors:
        print(f"FAIL: {err}", file=sys.stderr)
    sys.exit(1)
else:
    print("PASS: headless click events", file=sys.stderr)
    sys.exit(0)
