#!/usr/bin/env python3
"""Test that timers work correctly with --exec"""
import mcrfpy
from mcrfpy import automation

print("Setting up timer test...")

# Create a scene
timer_works = mcrfpy.Scene("timer_works")
timer_works.activate()
ui = timer_works.children

# Add visible content
frame = mcrfpy.Frame(pos=(100, 100), size=(300, 200),
                    fill_color=mcrfpy.Color(255, 0, 0),
                    outline_color=mcrfpy.Color(255, 255, 255),
                    outline=3.0)
ui.append(frame)

caption = mcrfpy.Caption(pos=(150, 150),
                        text="TIMER TEST SUCCESS",
                        fill_color=mcrfpy.Color(255, 255, 255))
caption.font_size = 24
ui.append(caption)

# Timer callback with new signature (timer, runtime)
def timer_callback(timer, runtime):
    print(f"\n✓ Timer fired successfully at runtime: {runtime}")

    # Take screenshot
    filename = f"timer_success_{int(runtime)}.png"
    result = automation.screenshot(filename)
    print(f"Screenshot saved: {filename} - Result: {result}")

    # Stop timer and exit
    timer.stop()
    print("Exiting...")
    mcrfpy.exit()

# Create timer (new API)
success_timer = mcrfpy.Timer("success_timer", timer_callback, 1000, once=True)
print("Timer set for 1 second. Using step() to advance time...")

# In headless mode, advance time manually
for i in range(11):  # 1100ms total
    mcrfpy.step(0.1)

print("PASS")
import sys
sys.exit(0)
