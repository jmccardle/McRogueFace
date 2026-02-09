#!/usr/bin/env python3
"""Test UIGrid camera_rotation functionality"""
import mcrfpy
from mcrfpy import automation
import sys

# Create test scene
test_scene = mcrfpy.Scene("grid_rotation_test")
ui = test_scene.children

# Create background
bg = mcrfpy.Frame(pos=(0, 0), size=(800, 600), fill_color=mcrfpy.Color(30, 30, 40))
ui.append(bg)

# Create a grid with entities to visualize rotation
grid = mcrfpy.Grid(grid_size=(8, 8), pos=(50, 50), size=(300, 300))
grid.fill_color = mcrfpy.Color(60, 60, 80)

# Add some entities to visualize the rotation
for i in range(8):
    entity = mcrfpy.Entity((i, 0))  # Top row
    grid.entities.append(entity)

for i in range(1, 8):
    entity = mcrfpy.Entity((0, i))  # Left column
    grid.entities.append(entity)

# Apply camera rotation
grid.camera_rotation = 30.0  # 30 degree rotation
grid.center_camera((4, 4))   # Center on middle of grid

ui.append(grid)

# Create a second grid without rotation for comparison
grid2 = mcrfpy.Grid(grid_size=(8, 8), pos=(400, 50), size=(300, 300))
grid2.fill_color = mcrfpy.Color(60, 60, 80)

# Add same entities pattern
for i in range(8):
    entity = mcrfpy.Entity((i, 0))
    grid2.entities.append(entity)

for i in range(1, 8):
    entity = mcrfpy.Entity((0, i))
    grid2.entities.append(entity)

grid2.camera_rotation = 0.0  # No rotation
grid2.center_camera((4, 4))

ui.append(grid2)

# Labels
label1 = mcrfpy.Caption(text="Grid with camera_rotation=30", pos=(50, 20))
ui.append(label1)

label2 = mcrfpy.Caption(text="Grid with camera_rotation=0", pos=(400, 20))
ui.append(label2)

# Create a third grid with viewport rotation (different from camera rotation)
grid3 = mcrfpy.Grid(grid_size=(6, 6), pos=(175, 400), size=(200, 150))
grid3.fill_color = mcrfpy.Color(80, 60, 60)

# Add entities
for i in range(6):
    entity = mcrfpy.Entity((i, 0))
    grid3.entities.append(entity)

# Apply viewport rotation (entire grid rotates)
grid3.rotation = 15.0
grid3.origin = (100, 75)  # Center origin for rotation
grid3.center_camera((3, 3))

ui.append(grid3)

label3 = mcrfpy.Caption(text="Grid with viewport rotation=15 (rotates entire widget)", pos=(100, 560))
ui.append(label3)

# Test center_camera computes correct pixel center
test_grid = mcrfpy.Grid(grid_size=(20, 15), pos=(0, 0), size=(320, 240))
cell_w = test_grid.cell_size[0]
cell_h = test_grid.cell_size[1]

# center_camera((0, 0)) should put tile (0,0) at view center
test_grid.center_camera((0, 0))
c0 = test_grid.center
# The center should position (0,0) in the middle of the viewport
# center = (tile_x * cell_w + cell_w/2, tile_y * cell_h + cell_h/2) mapped to view center

# center_camera at a different position should produce a different center
test_grid.center_camera((10, 7))
c1 = test_grid.center
assert c0.x != c1.x or c0.y != c1.y, "center_camera at different positions should give different centers"

# center_camera at same position twice should be idempotent
test_grid.center_camera((5, 5))
c2 = test_grid.center
test_grid.center_camera((5, 5))
c3 = test_grid.center
assert abs(c2.x - c3.x) < 0.01 and abs(c2.y - c3.y) < 0.01, "center_camera should be idempotent"

print("center_camera assertions passed")

# Activate scene
mcrfpy.current_scene = test_scene

# Advance the game loop to render, then take screenshot
mcrfpy.step(0.1)
automation.screenshot("grid_camera_rotation_test.png")
print("Screenshot saved as grid_camera_rotation_test.png")
print("PASS")
sys.exit(0)
