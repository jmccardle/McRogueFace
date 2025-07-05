#!/usr/bin/env python3
"""Test for mcrfpy.automation.screenshot()"""
import mcrfpy
from mcrfpy import automation
from datetime import datetime
import os
import sys
import time

runs = 0
def test_screenshot(*args):
    """Test screenshot functionality"""
    #global runs
    #runs += 1
    #if runs < 2:
    #    print("tick")
    #    return
    #print("tock")
    #mcrfpy.delTimer("timer1")
    # Create a scene with some visual elements
    mcrfpy.createScene("screenshot_test")
    mcrfpy.setScene("screenshot_test")
    ui = mcrfpy.sceneUI("screenshot_test")
    
    # Add some colorful elements
    frame1 = mcrfpy.Frame(10, 10, 200, 150,
                         fill_color=mcrfpy.Color(255, 0, 0),
                         outline_color=mcrfpy.Color(255, 255, 255),
                         outline=3.0)
    ui.append(frame1)
    
    frame2 = mcrfpy.Frame(220, 10, 200, 150,
                         fill_color=mcrfpy.Color(0, 255, 0),
                         outline_color=mcrfpy.Color(0, 0, 0),
                         outline=2.0)
    ui.append(frame2)
    
    caption = mcrfpy.Caption(mcrfpy.Vector(10, 170),
                            text="Screenshot Test Scene",
                            fill_color=mcrfpy.Color(255, 255, 0))
    caption.size = 24
    ui.append(caption)
    
    # Test multiple screenshots
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filenames = []
    
    # Test 1: Basic screenshot
    try:
        filename1 = f"test_screenshot_basic_{timestamp}.png"
        result = automation.screenshot(filename1)
        filenames.append(filename1)
        print(f"✓ Basic screenshot saved: {filename1} (result: {result})")
    except Exception as e:
        print(f"✗ Basic screenshot failed: {e}")
        print("FAIL")
        sys.exit(1)
    
    # Test 2: Screenshot with special characters in filename
    try:
        filename2 = f"test_screenshot_special_chars_{timestamp}_test.png"
        result = automation.screenshot(filename2)
        filenames.append(filename2)
        print(f"✓ Screenshot with special filename saved: {filename2} (result: {result})")
    except Exception as e:
        print(f"✗ Special filename screenshot failed: {e}")
    
    # Test 3: Invalid filename (if applicable)
    try:
        result = automation.screenshot("")
        print(f"✗ Empty filename should fail but returned: {result}")
    except Exception as e:
        print(f"✓ Empty filename correctly rejected: {e}")
    
    # Check files exist immediately
    files_found = 0
    for filename in filenames:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"✓ File exists: {filename} ({size} bytes)")
            files_found += 1
        else:
            print(f"✗ File not found: {filename}")
    
    if files_found == len(filenames):
        print("PASS")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)

print("Set callback")
mcrfpy.setTimer("timer1", test_screenshot, 1000)
# Run the test immediately
#test_screenshot()

