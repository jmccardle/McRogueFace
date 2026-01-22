#!/usr/bin/env python3
"""Minimal test to check if module works"""
import sys
import mcrfpy

print("Module loaded successfully")
print(f"mcrfpy has window: {hasattr(mcrfpy, 'window')}")
print(f"mcrfpy.Frame exists: {hasattr(mcrfpy, 'Frame')}")
sys.exit(0)
