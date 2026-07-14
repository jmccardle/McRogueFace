#!/usr/bin/env python3
"""Test script to verify the profiling metrics system

Updated for the #350 headless model: mcrfpy.step(dt) is the only clock (timers never
fire on their own), and step() never renders -- render counters (draw_calls,
ui_elements, visible_elements) are only published by an actual render pass, which we
force with automation.screenshot().
"""

import mcrfpy
from mcrfpy import automation
import sys
import os
import tempfile

# Track success across callbacks
success = True
done = False

SHOT = os.path.join(tempfile.gettempdir(), "test_metrics.png")


def test_metrics(timer, runtime):
    """Test the metrics after the timer fires"""
    global success
    print("\nRunning metrics test...")

    # step() never renders, so force a render pass to publish the render counters.
    automation.screenshot(SHOT)

    # Get metrics
    metrics = mcrfpy.get_metrics()

    print("\nPerformance Metrics:")
    print(f"  Frame Time: {metrics['frame_time']:.2f} ms")
    print(f"  Avg Frame Time: {metrics['avg_frame_time']:.2f} ms")
    print(f"  FPS: {metrics['fps']}")
    print(f"  Draw Calls: {metrics['draw_calls']}")
    print(f"  UI Elements: {metrics['ui_elements']}")
    print(f"  Visible Elements: {metrics['visible_elements']}")
    print(f"  Current Frame: {metrics['current_frame']}")
    print(f"  Runtime: {metrics['runtime']:.2f} seconds")

    # Test that metrics are reasonable

    # Frame time should be positive
    if metrics['frame_time'] <= 0:
        print("  FAIL: Frame time should be positive")
        success = False
    else:
        print("  PASS: Frame time is positive")

    # FPS should be reasonable (between 1 and 20000 in headless mode)
    # In headless mode, FPS can be very high since there's no vsync
    if metrics['fps'] < 1 or metrics['fps'] > 20000:
        print(f"  FAIL: FPS {metrics['fps']} is unreasonable")
        success = False
    else:
        print(f"  PASS: FPS {metrics['fps']} is reasonable")

    # UI elements count -- a render happened, so the scene's drawables were counted
    if metrics['ui_elements'] <= 0:
        print(f"  FAIL: UI elements count {metrics['ui_elements']} should be positive after a render")
        success = False
    else:
        print(f"  PASS: UI element count {metrics['ui_elements']} is valid")

    # Draw calls should be positive after a render
    if metrics['draw_calls'] <= 0:
        print(f"  FAIL: Draw calls {metrics['draw_calls']} should be positive after a render")
        success = False
    else:
        print(f"  PASS: Draw call count {metrics['draw_calls']} is valid")

    # Visible elements should be <= total elements (one frame is invisible)
    if metrics['visible_elements'] > metrics['ui_elements']:
        print("  FAIL: Visible elements > total elements")
        success = False
    else:
        print("  PASS: Visible element count is valid")

    # Current frame should be > 0
    if metrics['current_frame'] <= 0:
        print("  FAIL: Current frame should be > 0")
        success = False
    else:
        print("  PASS: Current frame is positive")

    # Runtime should be > 0
    if metrics['runtime'] <= 0:
        print("  FAIL: Runtime should be > 0")
        success = False
    else:
        print("  PASS: Runtime is positive")

    # Test metrics update over multiple frames
    print("\n\nTesting metrics over multiple frames...")

    # Store initial metrics for comparison
    initial_frame = metrics['current_frame']
    initial_runtime = metrics['runtime']

    # Schedule another check after 100ms of simulated time
    def check_later(timer2, runtime2):
        global success, done
        metrics2 = mcrfpy.get_metrics()

        print(f"\nMetrics after 100ms:")
        print(f"  Frame Time: {metrics2['frame_time']:.2f} ms")
        print(f"  Avg Frame Time: {metrics2['avg_frame_time']:.2f} ms")
        print(f"  FPS: {metrics2['fps']}")
        print(f"  Current Frame: {metrics2['current_frame']}")

        # Frame count should have increased
        if metrics2['current_frame'] > initial_frame:
            print("  PASS: Frame count increased")
        else:
            print("  FAIL: Frame count did not increase")
            success = False

        # Runtime should have increased
        if metrics2['runtime'] > initial_runtime:
            print("  PASS: Runtime increased")
        else:
            print("  FAIL: Runtime did not increase")
            success = False

        done = True

    mcrfpy.Timer("check_later", check_later, 100, once=True)


# Set up test scene
print("Setting up metrics test scene...")
metrics_test = mcrfpy.Scene("metrics_test")
metrics_test.activate()

# Add some UI elements
ui = metrics_test.children

# Create various UI elements
frame1 = mcrfpy.Frame(pos=(10, 10), size=(200, 150))
frame1.fill_color = mcrfpy.Color(100, 100, 100, 128)
ui.append(frame1)

caption1 = mcrfpy.Caption(pos=(50, 50), text="Test Caption")
ui.append(caption1)

sprite1 = mcrfpy.Sprite(pos=(100, 100))
ui.append(sprite1)

# Invisible element (should not count as visible)
frame2 = mcrfpy.Frame(pos=(300, 10), size=(100, 100))
frame2.visible = False
ui.append(frame2)

# Grid ctor is keyword-based now; grid_size= describes a new GridData.
grid = mcrfpy.Grid(grid_size=(10, 10), pos=(10, 200), size=(200, 200))
ui.append(grid)

print(f"Created {len(ui)} UI elements (1 invisible)")

# Schedule test to run after 50ms of simulated time
mcrfpy.Timer("test", test_metrics, 50, once=True)

# step() is the clock in headless mode: drive time until both timers have fired.
for _ in range(200):
    if done:
        break
    mcrfpy.step(0.016)

if os.path.exists(SHOT):
    os.remove(SHOT)

print("\n" + "=" * 50)
if not done:
    print("FAIL: timer callbacks never completed")
    success = False

if success:
    print("ALL METRICS TESTS PASSED!")
    print("PASS")
    sys.exit(0)
else:
    print("SOME METRICS TESTS FAILED!")
    sys.exit(1)
