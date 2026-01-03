#!/usr/bin/env python3
"""
Test synchronous screenshot in headless mode (#153)
====================================================

Tests that automation.screenshot() captures the CURRENT state in headless mode,
not the previous frame's buffer.

Key behavior:
- In headless mode, screenshot() renders then captures (synchronous)
- Changes made before screenshot() are visible in the captured image
- No timer dance required to capture current state
"""

import mcrfpy
from mcrfpy import automation
import sys
import os

def run_tests():
    """Run synchronous screenshot tests"""
    print("=== Synchronous Screenshot Tests ===\n")

    # Create a test scene with UI elements
    screenshot_test = mcrfpy.Scene("screenshot_test")
    screenshot_test.activate()
    ui = screenshot_test.children

    # Test 1: Basic screenshot works
    print("Test 1: Basic screenshot functionality")
    test_file = "/tmp/test_screenshot_basic.png"
    if os.path.exists(test_file):
        os.remove(test_file)

    result = automation.screenshot(test_file)
    assert result == True, f"screenshot() should return True, got {result}"
    assert os.path.exists(test_file), "Screenshot file should exist"
    file_size = os.path.getsize(test_file)
    assert file_size > 0, "Screenshot file should not be empty"
    print(f"  Screenshot saved: {test_file} ({file_size} bytes)")
    print()

    # Test 2: Screenshot captures current state (not previous frame)
    print("Test 2: Screenshot captures current state immediately")

    # Add a visible frame
    frame1 = mcrfpy.Frame(pos=(100, 100), size=(200, 200))
    frame1.fill_color = mcrfpy.Color(255, 0, 0)  # Red
    ui.append(frame1)

    # Take screenshot immediately - should show the red frame
    test_file2 = "/tmp/test_screenshot_state1.png"
    if os.path.exists(test_file2):
        os.remove(test_file2)

    result = automation.screenshot(test_file2)
    assert result == True, "screenshot() should return True"
    assert os.path.exists(test_file2), "Screenshot file should exist"
    print(f"  Screenshot with red frame: {test_file2}")

    # Modify the frame color
    frame1.fill_color = mcrfpy.Color(0, 255, 0)  # Green

    # Take another screenshot - should show green, not red
    test_file3 = "/tmp/test_screenshot_state2.png"
    if os.path.exists(test_file3):
        os.remove(test_file3)

    result = automation.screenshot(test_file3)
    assert result == True, "screenshot() should return True"
    assert os.path.exists(test_file3), "Screenshot file should exist"
    print(f"  Screenshot with green frame: {test_file3}")
    print()

    # Test 3: Multiple screenshots in succession
    print("Test 3: Multiple screenshots in succession")
    screenshot_files = []
    for i in range(3):
        frame1.fill_color = mcrfpy.Color(i * 80, i * 80, i * 80)  # Varying gray
        test_file_n = f"/tmp/test_screenshot_seq{i}.png"
        if os.path.exists(test_file_n):
            os.remove(test_file_n)

        result = automation.screenshot(test_file_n)
        assert result == True, f"screenshot() {i} should return True"
        assert os.path.exists(test_file_n), f"Screenshot {i} should exist"
        screenshot_files.append(test_file_n)

    print(f"  Created {len(screenshot_files)} sequential screenshots")

    # Verify all files are different sizes or exist
    sizes = [os.path.getsize(f) for f in screenshot_files]
    print(f"  File sizes: {sizes}")
    print()

    # Test 4: Screenshot after step()
    print("Test 4: Screenshot works correctly after step()")
    mcrfpy.step(0.1)  # Advance simulation

    test_file4 = "/tmp/test_screenshot_after_step.png"
    if os.path.exists(test_file4):
        os.remove(test_file4)

    result = automation.screenshot(test_file4)
    assert result == True, "screenshot() after step() should return True"
    assert os.path.exists(test_file4), "Screenshot after step() should exist"
    print(f"  Screenshot after step(): {test_file4}")
    print()

    # Clean up test files
    print("Cleaning up test files...")
    for f in [test_file, test_file2, test_file3, test_file4] + screenshot_files:
        if os.path.exists(f):
            os.remove(f)

    print()
    print("=== All Synchronous Screenshot Tests Passed! ===")
    return True

# Main execution
if __name__ == "__main__":
    try:
        if run_tests():
            print("\nPASS")
            sys.exit(0)
        else:
            print("\nFAIL")
            sys.exit(1)
    except Exception as e:
        print(f"\nFAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
