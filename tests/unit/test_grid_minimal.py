#!/usr/bin/env python3
"""
Minimal test to isolate Grid tuple initialization issue
"""

import mcrfpy

# This should cause the issue
print("Creating Grid with tuple (5, 5)...")
grid = mcrfpy.Grid((5, 5))
print("Success!")