#!/usr/bin/env python3
"""Test #111: Click Events in Headless Mode"""

import mcrfpy
from mcrfpy import automation
import sys

# Track callback invocations
click_count = 0
click_positions = []

def test_headless_click():
    """Test that clicks work in headless mode via automation API"""
    print("Testing headless click events...")

    test_click = mcrfpy.Scene("test_click")
    ui = test_click.children
    test_click.activate()

    # Create a frame at known position
    frame = mcrfpy.Frame(pos=(100, 100), size=(200, 200))
    ui.append(frame)

    # Track only "start" events (press) - click() sends both press and release
    start_clicks = []

    def on_click_handler(x, y, button, action):
        if action == "start":
            start_clicks.append((x, y, button, action))
            print(f"    Click received: x={x}, y={y}, button={button}, action={action}")

    frame.on_click = on_click_handler

    # Use automation to click inside the frame
    print("  Clicking inside frame at (150, 150)...")
    automation.click(150, 150)

    # Give time for events to process
    def check_results(timer, runtime):
        if len(start_clicks) >= 1:
            print(f"  - Click received: {len(start_clicks)} click(s)")
            # Verify position
            pos = start_clicks[0]
            assert pos[0] == 150, f"Expected x=150, got {pos[0]}"
            assert pos[1] == 150, f"Expected y=150, got {pos[1]}"
            print(f"  - Position correct: ({pos[0]}, {pos[1]})")
            print("  - headless click: PASS")
            print("\n=== All Headless Click tests passed! ===")
            sys.exit(0)
        else:
            print(f"  - No clicks received: FAIL")
            sys.exit(1)

    mcrfpy.Timer("check_click", check_results, 200, once=True)


def test_click_miss():
    """Test that clicks outside an element don't trigger its callback"""
    print("Testing click miss (outside element)...")

    global click_count, click_positions
    click_count = 0
    click_positions = []

    test_miss = mcrfpy.Scene("test_miss")
    ui = test_miss.children
    test_miss.activate()

    # Create a frame at known position
    frame = mcrfpy.Frame(pos=(100, 100), size=(100, 100))
    ui.append(frame)

    miss_count = [0]  # Use list to avoid global

    def on_click_handler(x, y, button, action):
        miss_count[0] += 1
        print(f"    Unexpected click received at ({x}, {y})")

    frame.on_click = on_click_handler

    # Click outside the frame
    print("  Clicking outside frame at (50, 50)...")
    automation.click(50, 50)

    def check_miss_results(timer, runtime):
        if miss_count[0] == 0:
            print("  - No click on miss: PASS")
            # Now run the main click test
            test_headless_click()
        else:
            print(f"  - Unexpected {miss_count[0]} click(s): FAIL")
            sys.exit(1)

    mcrfpy.Timer("check_miss", check_miss_results, 200, once=True)


def test_position_tracking():
    """Test that automation.position() returns simulated position"""
    print("Testing position tracking...")

    # Move to a specific position
    automation.moveTo(123, 456)

    # Check position
    pos = automation.position()
    print(f"  Position after moveTo(123, 456): {pos}")

    assert pos[0] == 123, f"Expected x=123, got {pos[0]}"
    assert pos[1] == 456, f"Expected y=456, got {pos[1]}"

    print("  - position tracking: PASS")


if __name__ == "__main__":
    try:
        test_position_tracking()
        test_click_miss()  # This will chain to test_headless_click on success
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
