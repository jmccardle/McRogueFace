#!/usr/bin/env python3
"""Test script to verify the profiling metrics system"""

import mcrfpy
import sys
import time

def test_metrics(runtime):
    """Test the metrics after timer starts"""
    print("\nRunning metrics test...")
    
    # Get metrics
    metrics = mcrfpy.getMetrics()
    
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
    success = True
    
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
    
    # UI elements count (may be 0 if scene hasn't rendered yet)
    if metrics['ui_elements'] < 0:
        print(f"  FAIL: UI elements count {metrics['ui_elements']} is negative")
        success = False
    else:
        print(f"  PASS: UI element count {metrics['ui_elements']} is valid")
    
    # Visible elements should be <= total elements
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
    
    # Schedule another check after 100ms
    def check_later(runtime2):
        metrics2 = mcrfpy.getMetrics()
        
        print(f"\nMetrics after 100ms:")
        print(f"  Frame Time: {metrics2['frame_time']:.2f} ms")
        print(f"  Avg Frame Time: {metrics2['avg_frame_time']:.2f} ms")
        print(f"  FPS: {metrics2['fps']}")
        print(f"  Current Frame: {metrics2['current_frame']}")
        
        # Frame count should have increased
        if metrics2['current_frame'] > metrics['current_frame']:
            print("  PASS: Frame count increased")
        else:
            print("  FAIL: Frame count did not increase")
            nonlocal success
            success = False
        
        # Runtime should have increased
        if metrics2['runtime'] > metrics['runtime']:
            print("  PASS: Runtime increased")
        else:
            print("  FAIL: Runtime did not increase")
            success = False
        
        print("\n" + "="*50)
        if success:
            print("ALL METRICS TESTS PASSED!")
        else:
            print("SOME METRICS TESTS FAILED!")
        
        sys.exit(0 if success else 1)
    
    mcrfpy.setTimer("check_later", check_later, 100)

# Set up test scene
print("Setting up metrics test scene...")
mcrfpy.createScene("metrics_test")
mcrfpy.setScene("metrics_test")

# Add some UI elements
ui = mcrfpy.sceneUI("metrics_test")

# Create various UI elements
frame1 = mcrfpy.Frame(10, 10, 200, 150)
frame1.fill_color = (100, 100, 100, 128)
ui.append(frame1)

caption1 = mcrfpy.Caption("Test Caption", 50, 50)
ui.append(caption1)

sprite1 = mcrfpy.Sprite(100, 100)
ui.append(sprite1)

# Invisible element (should not count as visible)
frame2 = mcrfpy.Frame(300, 10, 100, 100)
frame2.visible = False
ui.append(frame2)

grid = mcrfpy.Grid(10, 10, mcrfpy.default_texture, (10, 200), (200, 200))
ui.append(grid)

print(f"Created {len(ui)} UI elements (1 invisible)")

# Schedule test to run after render loop starts
mcrfpy.setTimer("test", test_metrics, 50)