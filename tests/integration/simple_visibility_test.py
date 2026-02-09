#!/usr/bin/env python3
"""Simple visibility test without entity append"""

import mcrfpy
import sys

print("Simple visibility test...")

# Create scene and grid
simple = mcrfpy.Scene("simple")
print("Scene created")

grid = mcrfpy.Grid(grid_w=5, grid_h=5)
print("Grid created")

# Create entity with grid association
entity = mcrfpy.Entity((2, 2), grid=grid)
print(f"Entity created at ({entity.x}, {entity.y})")

# Check if gridstate is initialized
print(f"Gridstate length: {len(entity.gridstate)}")

# Try to access at method
try:
    state = entity.at(0, 0)
    print(f"at(0,0) returned: {state}")
    print(f"visible: {state.visible}, discovered: {state.discovered}")
except Exception as e:
    print(f"Error in at(): {e}")

# Try update_visibility
try:
    entity.update_visibility()
    print("update_visibility() succeeded")
except Exception as e:
    print(f"Error in update_visibility(): {e}")

print("Test complete")
sys.exit(0)