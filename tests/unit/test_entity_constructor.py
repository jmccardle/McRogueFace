#!/usr/bin/env python3
import mcrfpy

# Create scene and grid
test = mcrfpy.Scene("test")
ui = test.children

# Create texture and grid
texture = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16)
grid = mcrfpy.Grid(5, 5, texture)
ui.append(grid)

# Test Entity constructor
try:
    # Based on usage in ui_Grid_test.py
    entity = mcrfpy.Entity(mcrfpy.Vector(2, 2), texture, 84, grid)
    print("Entity created with 4 args: position, texture, sprite_index, grid")
except Exception as e:
    print(f"4 args failed: {e}")
    try:
        # Maybe it's just position, texture, sprite_index
        entity = mcrfpy.Entity((2, 2), texture, 84)
        print("Entity created with 3 args: position, texture, sprite_index")
    except Exception as e2:
        print(f"3 args failed: {e2}")

mcrfpy.exit()