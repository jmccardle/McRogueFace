#!/usr/bin/env python3
"""Debug grid creation error"""

import mcrfpy
import sys
import traceback

print("Testing grid creation with detailed error...")

# Create scene first
mcrfpy.createScene("test")

# Try to create grid and get detailed error
try:
    grid = mcrfpy.Grid(0, 0, grid_size=(10, 10))
    print("✓ Created grid successfully")
except Exception as e:
    print(f"✗ Grid creation failed with exception: {type(e).__name__}: {e}")
    traceback.print_exc()
    
    # Try to get more info
    import sys
    exc_info = sys.exc_info()
    print(f"\nException type: {exc_info[0]}")
    print(f"Exception value: {exc_info[1]}")
    print(f"Traceback: {exc_info[2]}")

sys.exit(0)