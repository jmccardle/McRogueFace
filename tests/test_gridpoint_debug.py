#!/usr/bin/env python3
import sys
import mcrfpy
print("1 - Loading texture", flush=True)
texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)
print("2 - Creating grid", flush=True)
grid = mcrfpy.Grid(grid_size=(10, 10), texture=texture, pos=(0, 0), size=(160, 160))
print("3 - Getting grid point at (3, 5)", flush=True)
point = grid.at(3, 5)
print(f"4 - Point: {point}", flush=True)
print("5 - Getting grid_pos", flush=True)
grid_pos = point.grid_pos
print(f"6 - grid_pos: {grid_pos}", flush=True)
print("PASS", flush=True)
sys.exit(0)
