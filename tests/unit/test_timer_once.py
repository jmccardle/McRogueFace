#!/usr/bin/env python3
"""
Test once=True timer functionality
Uses mcrfpy.step() to advance time in headless mode.
"""
import mcrfpy
import sys

once_count = 0
repeat_count = 0

def once_callback(timer, runtime):
    global once_count
    once_count += 1
    print(f"Once timer fired! Count: {once_count}, Timer.once: {timer.once}")

def repeat_callback(timer, runtime):
    global repeat_count
    repeat_count += 1
    print(f"Repeat timer fired! Count: {repeat_count}, Timer.once: {timer.once}")

# Set up the scene
test_scene = mcrfpy.Scene("test_scene")
test_scene.activate()

# Create timers
print("Creating once timer with once=True...")
once_timer = mcrfpy.Timer("once_timer", once_callback, 100, once=True)
print(f"Timer: {once_timer}, once={once_timer.once}")

print("\nCreating repeat timer with once=False (default)...")
repeat_timer = mcrfpy.Timer("repeat_timer", repeat_callback, 100)
print(f"Timer: {repeat_timer}, once={repeat_timer.once}")

# Advance time using step() to let timers fire
# Step 600ms total - once timer (100ms) fires once, repeat timer fires ~6 times
print("\nAdvancing time with step()...")
for i in range(6):
    mcrfpy.step(0.1)  # 100ms each

# Check results
print(f"\nFinal results:")
print(f"Once timer fired {once_count} times (expected: 1)")
print(f"Repeat timer fired {repeat_count} times (expected: 3+)")

if once_count == 1 and repeat_count >= 3:
    print("PASS: Once timer fired exactly once, repeat timer fired multiple times")
    sys.exit(0)
else:
    print("FAIL: Timer behavior incorrect")
    sys.exit(1)
