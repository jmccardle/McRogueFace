#!/usr/bin/env python3
"""Test audio cleanup on exit"""
import mcrfpy
import sys

print("Testing audio cleanup...")

# Create a scene and immediately exit
test = mcrfpy.Scene("test")
print("Exiting now...")
sys.exit(0)