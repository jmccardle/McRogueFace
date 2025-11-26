#!/usr/bin/env python3
"""Simple test for Color setter fix"""

import mcrfpy

print("Testing Color fix...")

# Test 1: Create grid
try:
    mcrfpy.createScene("test")
    grid = mcrfpy.Grid(grid_x=5, grid_y=5)
    print("✓ Grid created")
except Exception as e:
    print(f"✗ Grid creation failed: {e}")
    exit(1)

# Test 2: Set color with tuple
try:
    grid.at(0, 0).color = (100, 100, 100)
    print("✓ Tuple color assignment works")
except Exception as e:
    print(f"✗ Tuple assignment failed: {e}")

# Test 3: Set color with Color object
try:
    grid.at(0, 0).color = mcrfpy.Color(200, 200, 200)
    print("✓ Color object assignment works!")
except Exception as e:
    print(f"✗ Color assignment failed: {e}")

print("Done.")