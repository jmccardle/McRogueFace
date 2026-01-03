#!/usr/bin/env python3
"""
Simple test for Issue #37: Verify script loading works from executable directory
"""

import sys
import os
import mcrfpy

# This script runs as --exec, which means it's loaded after Python initialization
# and after game.py. If we got here, script loading is working.

print("Issue #37 test: Script execution verified")
print(f"Current working directory: {os.getcwd()}")
print(f"Script location: {__file__}")

# Create a simple scene to verify everything is working
issue37_test = mcrfpy.Scene("issue37_test")

print("PASS: Issue #37 - Script loading working correctly")
sys.exit(0)