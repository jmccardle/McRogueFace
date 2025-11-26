#!/usr/bin/env python3
"""Test if closing stdin prevents the >>> prompt"""
import mcrfpy
import sys
import os

print("=== Testing stdin theory ===")
print(f"stdin.isatty(): {sys.stdin.isatty()}")
print(f"stdin fileno: {sys.stdin.fileno()}")

# Set up a basic scene
mcrfpy.createScene("stdin_test")
mcrfpy.setScene("stdin_test")

# Try to prevent interactive mode by closing stdin
print("\nAttempting to prevent interactive mode...")
try:
    # Method 1: Close stdin
    sys.stdin.close()
    print("Closed sys.stdin")
except:
    print("Failed to close sys.stdin")

try:
    # Method 2: Redirect stdin to /dev/null
    devnull = open(os.devnull, 'r')
    os.dup2(devnull.fileno(), 0)
    print("Redirected stdin to /dev/null")
except:
    print("Failed to redirect stdin")

print("\nScript complete. If >>> still appears, the issue is elsewhere.")