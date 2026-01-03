#!/usr/bin/env python3
"""Test grid creation step by step"""

import mcrfpy
import sys

print("Testing grid creation...")

# First create scene
try:
    test = mcrfpy.Scene("test")
    print("✓ Created scene")
except Exception as e:
    print(f"✗ Failed to create scene: {e}")
    sys.exit(1)

# Try different grid creation methods
print("\nTesting grid creation methods:")

# Method 1: Position and grid_size as tuples
try:
    grid1 = mcrfpy.Grid(x=0, y=0, grid_size=(10, 10))
    print("✓ Method 1: Grid(x=0, y=0, grid_size=(10, 10))")
except Exception as e:
    print(f"✗ Method 1 failed: {e}")

# Method 2: Just grid_size
try:
    grid2 = mcrfpy.Grid(grid_size=(10, 10))
    print("✓ Method 2: Grid(grid_size=(10, 10))")
except Exception as e:
    print(f"✗ Method 2 failed: {e}")

# Method 3: Old style with grid_x, grid_y
try:
    grid3 = mcrfpy.Grid(grid_x=10, grid_y=10)
    print("✓ Method 3: Grid(grid_x=10, grid_y=10)")
except Exception as e:
    print(f"✗ Method 3 failed: {e}")

# Method 4: Positional args
try:
    grid4 = mcrfpy.Grid(0, 0, (10, 10))
    print("✓ Method 4: Grid(0, 0, (10, 10))")
except Exception as e:
    print(f"✗ Method 4 failed: {e}")

print("\nDone.")
sys.exit(0)