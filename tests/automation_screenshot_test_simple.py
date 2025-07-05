#!/usr/bin/env python3
"""Simple test for mcrfpy.automation.screenshot()"""
import mcrfpy
from mcrfpy import automation
import os
import sys

# Create a simple scene
mcrfpy.createScene("test")
mcrfpy.setScene("test")

# Take a screenshot immediately
try:
    filename = "test_screenshot.png"
    result = automation.screenshot(filename)
    print(f"Screenshot result: {result}")
    
    # Check if file exists
    if os.path.exists(filename):
        size = os.path.getsize(filename)
        print(f"PASS - Screenshot saved: {filename} ({size} bytes)")
    else:
        print(f"FAIL - Screenshot file not created: {filename}")
except Exception as e:
    print(f"FAIL - Screenshot error: {e}")
    import traceback
    traceback.print_exc()

# Exit immediately
sys.exit(0)