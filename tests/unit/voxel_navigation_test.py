#!/usr/bin/env python3
"""Unit tests for Milestone 12: VoxelGrid Navigation Projection

Tests VoxelGrid.project_column() and Viewport3D voxel-to-nav projection methods.
"""

import mcrfpy
import sys

# Test counters
tests_passed = 0
tests_failed = 0

def test(name, condition):
    """Simple test helper"""
    global tests_passed, tests_failed
    if condition:
        tests_passed += 1
        print(f"  PASS: {name}")
    else:
        tests_failed += 1
        print(f"  FAIL: {name}")

def approx_eq(a, b, epsilon=0.001):
    """Approximate floating-point equality"""
    return abs(a - b) < epsilon

# =============================================================================
# Test projectColumn() on VoxelGrid
# =============================================================================

print("\n=== Testing VoxelGrid.project_column() ===")

# Test 1: Empty grid - all air
vg = mcrfpy.VoxelGrid((10, 10, 10), cell_size=1.0)
nav = vg.project_column(5, 5)
test("Empty grid - height is 0", approx_eq(nav['height'], 0.0))
test("Empty grid - not walkable (no floor)", nav['walkable'] == False)
test("Empty grid - transparent", nav['transparent'] == True)
test("Empty grid - default path cost", approx_eq(nav['path_cost'], 1.0))

# Test 2: Simple floor
vg2 = mcrfpy.VoxelGrid((10, 10, 10), cell_size=1.0)
stone = vg2.add_material("stone", (128, 128, 128))
vg2.fill_box((0, 0, 0), (9, 0, 9), stone)  # Floor at y=0
nav2 = vg2.project_column(5, 5)
test("Floor at y=0 - height is 1.0 (top of floor voxel)", approx_eq(nav2['height'], 1.0))
test("Floor at y=0 - walkable", nav2['walkable'] == True)
test("Floor at y=0 - not transparent (has solid voxel)", nav2['transparent'] == False)

# Test 3: Solid column extending to top - no headroom at boundary
vg3 = mcrfpy.VoxelGrid((10, 10, 10), cell_size=1.0)
stone3 = vg3.add_material("stone", (128, 128, 128))
vg3.fill_box((0, 0, 0), (9, 0, 9), stone3)  # Floor at y=0
vg3.fill_box((0, 2, 0), (9, 9, 9), stone3)  # Solid block from y=2 to y=9
nav3 = vg3.project_column(5, 5, headroom=2)
# Scan finds y=9 as topmost floor (boundary has "air above" but no actual headroom)
# Height = 10.0 (top of y=9 voxel), no air above means airCount=0, so not walkable
test("Top boundary floor - height at top", approx_eq(nav3['height'], 10.0))
test("Top boundary floor - not walkable (no headroom)", nav3['walkable'] == False)

# Test 4: Single floor slab with plenty of headroom
vg4 = mcrfpy.VoxelGrid((10, 10, 10), cell_size=1.0)
stone4 = vg4.add_material("stone", (128, 128, 128))
vg4.fill_box((0, 2, 0), (9, 2, 9), stone4)  # Floor slab at y=2 (air below, 7 voxels air above)
nav4 = vg4.project_column(5, 5, headroom=2)
test("Floor slab at y=2 - height is 3.0", approx_eq(nav4['height'], 3.0))
test("Floor slab - walkable (7 voxels headroom)", nav4['walkable'] == True)

# Test 5: Custom headroom thresholds
nav4_h1 = vg4.project_column(5, 5, headroom=1)
test("Headroom=1 - walkable", nav4_h1['walkable'] == True)
nav4_h7 = vg4.project_column(5, 5, headroom=7)
test("Headroom=7 - walkable (exactly 7 air voxels)", nav4_h7['walkable'] == True)
nav4_h8 = vg4.project_column(5, 5, headroom=8)
test("Headroom=8 - not walkable (only 7 air)", nav4_h8['walkable'] == False)

# Test 6: Multi-level floor (finds topmost walkable)
vg5 = mcrfpy.VoxelGrid((10, 10, 10), cell_size=1.0)
stone5 = vg5.add_material("stone", (128, 128, 128))
vg5.fill_box((0, 0, 0), (9, 0, 9), stone5)  # Bottom floor at y=0
vg5.fill_box((0, 5, 0), (9, 5, 9), stone5)  # Upper floor at y=5
nav5 = vg5.project_column(5, 5)
test("Multi-level - finds top floor", approx_eq(nav5['height'], 6.0))
test("Multi-level - walkable", nav5['walkable'] == True)

# Test 7: Transparent material
vg6 = mcrfpy.VoxelGrid((10, 10, 10), cell_size=1.0)
glass = vg6.add_material("glass", (200, 200, 255), transparent=True)
vg6.set(5, 5, 5, glass)
nav6 = vg6.project_column(5, 5)
test("Transparent voxel - column is transparent", nav6['transparent'] == True)

# Test 8: Non-transparent material
vg7 = mcrfpy.VoxelGrid((10, 10, 10), cell_size=1.0)
wall = vg7.add_material("wall", (100, 100, 100), transparent=False)
vg7.set(5, 5, 5, wall)
nav7 = vg7.project_column(5, 5)
test("Opaque voxel - column not transparent", nav7['transparent'] == False)

# Test 9: Path cost from material
vg8 = mcrfpy.VoxelGrid((10, 10, 10), cell_size=1.0)
mud = vg8.add_material("mud", (139, 90, 43), path_cost=2.0)
vg8.fill_box((0, 0, 0), (9, 0, 9), mud)  # Floor of mud
nav8 = vg8.project_column(5, 5)
test("Mud floor - path cost is 2.0", approx_eq(nav8['path_cost'], 2.0))

# Test 10: Cell size affects height
vg9 = mcrfpy.VoxelGrid((10, 10, 10), cell_size=2.0)
stone9 = vg9.add_material("stone", (128, 128, 128))
vg9.fill_box((0, 0, 0), (9, 0, 9), stone9)  # Floor at y=0
nav9 = vg9.project_column(5, 5)
test("Cell size 2.0 - height is 2.0", approx_eq(nav9['height'], 2.0))

# Test 11: Out of bounds returns default
nav_oob = vg.project_column(-1, 5)
test("Out of bounds - not walkable", nav_oob['walkable'] == False)
test("Out of bounds - height 0", approx_eq(nav_oob['height'], 0.0))

# =============================================================================
# Test Viewport3D voxel-to-nav projection
# =============================================================================

print("\n=== Testing Viewport3D voxel-to-nav projection ===")

# Create viewport with navigation grid
vp = mcrfpy.Viewport3D(pos=(0, 0), size=(640, 480))
vp.set_grid_size(20, 20)
vp.cell_size = 1.0

# Test 12: Initial nav grid state
cell = vp.at(10, 10)
test("Initial nav cell - walkable", cell.walkable == True)
test("Initial nav cell - transparent", cell.transparent == True)
test("Initial nav cell - height 0", approx_eq(cell.height, 0.0))
test("Initial nav cell - cost 1", approx_eq(cell.cost, 1.0))

# Test 13: Project simple voxel grid
vg_nav = mcrfpy.VoxelGrid((10, 5, 10), cell_size=1.0)
stone_nav = vg_nav.add_material("stone", (128, 128, 128))
vg_nav.fill_box((0, 0, 0), (9, 0, 9), stone_nav)  # Floor
vg_nav.offset = (5, 0, 5)  # Position grid at (5, 0, 5) in world

vp.add_voxel_layer(vg_nav)
vp.project_voxel_to_nav(vg_nav, headroom=2)

# Check cell within grid footprint
cell_in = vp.at(10, 10)  # World (10, 10) = voxel grid local (5, 5)
test("Projected cell - walkable (floor present)", cell_in.walkable == True)
test("Projected cell - height is 1.0", approx_eq(cell_in.height, 1.0))
test("Projected cell - not transparent", cell_in.transparent == False)

# Check cell outside grid footprint (unchanged)
cell_out = vp.at(0, 0)  # Outside voxel grid area
test("Outside cell - still walkable (unchanged)", cell_out.walkable == True)
test("Outside cell - height still 0", approx_eq(cell_out.height, 0.0))

# Test 14: Clear voxel nav region
vp.clear_voxel_nav_region(vg_nav)
cell_cleared = vp.at(10, 10)
test("Cleared cell - walkable reset to true", cell_cleared.walkable == True)
test("Cleared cell - height reset to 0", approx_eq(cell_cleared.height, 0.0))
test("Cleared cell - transparent reset to true", cell_cleared.transparent == True)

# Test 15: Project with walls (blocking)
vg_wall = mcrfpy.VoxelGrid((10, 5, 10), cell_size=1.0)
stone_wall = vg_wall.add_material("stone", (128, 128, 128))
vg_wall.fill_box((0, 0, 0), (9, 4, 9), stone_wall)  # Solid block (no air above floor)
vg_wall.offset = (0, 0, 0)

vp2 = mcrfpy.Viewport3D(pos=(0, 0), size=(640, 480))
vp2.set_grid_size(20, 20)
vp2.add_voxel_layer(vg_wall)
vp2.project_voxel_to_nav(vg_wall)

cell_wall = vp2.at(5, 5)
test("Solid block - height at top", approx_eq(cell_wall.height, 5.0))
test("Solid block - not transparent", cell_wall.transparent == False)

# Test 16: project_all_voxels_to_nav with multiple layers
vp3 = mcrfpy.Viewport3D(pos=(0, 0), size=(640, 480))
vp3.set_grid_size(20, 20)

# First layer - lower priority
vg_layer1 = mcrfpy.VoxelGrid((20, 5, 20), cell_size=1.0)
dirt = vg_layer1.add_material("dirt", (139, 90, 43))
vg_layer1.fill_box((0, 0, 0), (19, 0, 19), dirt)  # Floor everywhere

# Second layer - higher priority, partial coverage
vg_layer2 = mcrfpy.VoxelGrid((5, 5, 5), cell_size=1.0)
stone_l2 = vg_layer2.add_material("stone", (128, 128, 128))
vg_layer2.fill_box((0, 0, 0), (4, 2, 4), stone_l2)  # Higher floor
vg_layer2.offset = (5, 0, 5)

vp3.add_voxel_layer(vg_layer1, z_index=0)
vp3.add_voxel_layer(vg_layer2, z_index=1)
vp3.project_all_voxels_to_nav()

cell_dirt = vp3.at(0, 0)  # Only dirt layer
cell_stone = vp3.at(7, 7)  # Stone layer overlaps (higher z_index)
test("Multi-layer - dirt area height is 1", approx_eq(cell_dirt.height, 1.0))
test("Multi-layer - stone area height is 3 (higher layer)", approx_eq(cell_stone.height, 3.0))

# Test 17: Viewport projection with different headroom values
vg_low = mcrfpy.VoxelGrid((10, 5, 10), cell_size=1.0)
stone_low = vg_low.add_material("stone", (128, 128, 128))
vg_low.fill_box((0, 0, 0), (9, 0, 9), stone_low)  # Floor at y=0
# Grid has height=5, so floor at y=0 has 4 air voxels above (y=1,2,3,4)

vp4 = mcrfpy.Viewport3D(pos=(0, 0), size=(640, 480))
vp4.set_grid_size(20, 20)
vp4.add_voxel_layer(vg_low)

vp4.project_voxel_to_nav(vg_low, headroom=1)
test("Headroom 1 - walkable (4 air voxels)", vp4.at(5, 5).walkable == True)

vp4.project_voxel_to_nav(vg_low, headroom=4)
test("Headroom 4 - walkable (exactly 4 air)", vp4.at(5, 5).walkable == True)

vp4.project_voxel_to_nav(vg_low, headroom=5)
test("Headroom 5 - not walkable (only 4 air)", vp4.at(5, 5).walkable == False)

# Test 18: Grid offset in world space
vg_offset = mcrfpy.VoxelGrid((5, 5, 5), cell_size=1.0)
stone_off = vg_offset.add_material("stone", (128, 128, 128))
vg_offset.fill_box((0, 0, 0), (4, 0, 4), stone_off)
vg_offset.offset = (10, 5, 10)  # Y offset = 5

vp5 = mcrfpy.Viewport3D(pos=(0, 0), size=(640, 480))
vp5.set_grid_size(20, 20)
vp5.add_voxel_layer(vg_offset)
vp5.project_voxel_to_nav(vg_offset)

cell_off = vp5.at(12, 12)
test("Y-offset grid - height includes offset", approx_eq(cell_off.height, 6.0))  # floor 1 + offset 5

# =============================================================================
# Summary
# =============================================================================

print(f"\n=== Results: {tests_passed} passed, {tests_failed} failed ===")

if tests_failed > 0:
    sys.exit(1)
else:
    print("All tests passed!")
    sys.exit(0)
