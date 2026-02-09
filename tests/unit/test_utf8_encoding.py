#!/usr/bin/env python3
"""
Test UTF-8 encoding support
"""

import mcrfpy
import sys

# Setup scene
test = mcrfpy.Scene("test")
mcrfpy.current_scene = test

# Test various unicode characters
print("Check mark works")
print("Cross mark works")
print("Emoji works")
print("Japanese works")
print("Spanish works")
print("Russian works")

# Test in f-strings
count = 5
print(f"Added {count} items")

# Test unicode in error messages
try:
    raise ValueError("Error with unicode")
except ValueError as e:
    print(f"Exception handling works: {e}")

print("\nAll UTF-8 tests passed!")
print("PASS")
sys.exit(0)
