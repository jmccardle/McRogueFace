#!/usr/bin/env python3
"""Simple module test"""
import sys
import mcrfpy

print("Step 1: Module loaded")

# Test window singleton exists (#184)
print("Step 2: Checking window...")
has_window = hasattr(mcrfpy, 'window')
print(f"  has window: {has_window}")

if has_window:
    print("Step 3: Getting window...")
    window = mcrfpy.window
    print(f"  window: {window}")
    print("Step 4: Checking resolution...")
    res = window.resolution
    print(f"  resolution: {res}")

print("PASS")
sys.exit(0)
