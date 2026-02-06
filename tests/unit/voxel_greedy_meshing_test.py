#!/usr/bin/env python3
"""Unit tests for Milestone 13: Greedy Meshing

Tests that greedy meshing produces correct mesh geometry with reduced vertex count.
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

# =============================================================================
# Test greedy meshing property
# =============================================================================

print("\n=== Testing greedy_meshing property ===")

vg = mcrfpy.VoxelGrid((8, 8, 8), cell_size=1.0)
test("Default greedy_meshing is False", vg.greedy_meshing == False)

vg.greedy_meshing = True
test("Can enable greedy_meshing", vg.greedy_meshing == True)

vg.greedy_meshing = False
test("Can disable greedy_meshing", vg.greedy_meshing == False)

# =============================================================================
# Test vertex count reduction
# =============================================================================

print("\n=== Testing vertex count reduction ===")

# Create a solid 4x4x4 cube - this should benefit greatly from greedy meshing
# Non-greedy: 6 faces per voxel for exposed faces = many quads
# Greedy: 6 large quads (one per side)

vg2 = mcrfpy.VoxelGrid((4, 4, 4), cell_size=1.0)
stone = vg2.add_material("stone", (128, 128, 128))
vg2.fill((stone))  # Fill entire grid

# Get vertex count with standard meshing
vg2.greedy_meshing = False
vg2.rebuild_mesh()
standard_vertices = vg2.vertex_count
print(f"  Standard meshing: {standard_vertices} vertices")

# Get vertex count with greedy meshing
vg2.greedy_meshing = True
vg2.rebuild_mesh()
greedy_vertices = vg2.vertex_count
print(f"  Greedy meshing: {greedy_vertices} vertices")

# For a solid 4x4x4 cube, standard meshing creates:
# Each face of the cube is 4x4 = 16 voxel faces
# 6 cube faces * 16 faces/side * 6 vertices/face = 576 vertices
# Greedy meshing creates:
# 6 cube faces * 1 merged quad * 6 vertices/quad = 36 vertices

test("Greedy meshing reduces vertex count", greedy_vertices < standard_vertices)
test("Solid cube greedy: 36 vertices (6 faces * 6 verts)", greedy_vertices == 36)

# =============================================================================
# Test larger solid block
# =============================================================================

print("\n=== Testing larger solid block ===")

vg3 = mcrfpy.VoxelGrid((16, 16, 16), cell_size=1.0)
stone3 = vg3.add_material("stone", (128, 128, 128))
vg3.fill(stone3)

vg3.greedy_meshing = False
vg3.rebuild_mesh()
standard_verts_large = vg3.vertex_count
print(f"  Standard: {standard_verts_large} vertices")

vg3.greedy_meshing = True
vg3.rebuild_mesh()
greedy_verts_large = vg3.vertex_count
print(f"  Greedy: {greedy_verts_large} vertices")

# 16x16 faces = 256 quads per side -> 1 quad per side with greedy
# Reduction factor should be significant
reduction_factor = standard_verts_large / greedy_verts_large if greedy_verts_large > 0 else 0
print(f"  Reduction factor: {reduction_factor:.1f}x")

test("Large block greedy: still 36 vertices", greedy_verts_large == 36)
test("Significant vertex reduction (>10x)", reduction_factor > 10)

# =============================================================================
# Test checkerboard pattern (worst case for greedy)
# =============================================================================

print("\n=== Testing checkerboard pattern (greedy stress test) ===")

vg4 = mcrfpy.VoxelGrid((4, 4, 4), cell_size=1.0)
stone4 = vg4.add_material("stone", (128, 128, 128))

# Create checkerboard pattern - no adjacent same-material voxels
for z in range(4):
    for y in range(4):
        for x in range(4):
            if (x + y + z) % 2 == 0:
                vg4.set(x, y, z, stone4)

vg4.greedy_meshing = False
vg4.rebuild_mesh()
standard_checker = vg4.vertex_count
print(f"  Standard: {standard_checker} vertices")

vg4.greedy_meshing = True
vg4.rebuild_mesh()
greedy_checker = vg4.vertex_count
print(f"  Greedy: {greedy_checker} vertices")

# In checkerboard, greedy meshing can't merge much, so counts should be similar
test("Checkerboard: greedy meshing works (produces vertices)", greedy_checker > 0)
# Greedy might still reduce a bit due to row merging
test("Checkerboard: greedy <= standard", greedy_checker <= standard_checker)

# =============================================================================
# Test different materials (no cross-material merging)
# =============================================================================

print("\n=== Testing multi-material (no cross-material merging) ===")

vg5 = mcrfpy.VoxelGrid((4, 4, 4), cell_size=1.0)
red = vg5.add_material("red", (255, 0, 0))
blue = vg5.add_material("blue", (0, 0, 255))

# Half red, half blue
vg5.fill_box((0, 0, 0), (1, 3, 3), red)
vg5.fill_box((2, 0, 0), (3, 3, 3), blue)

vg5.greedy_meshing = True
vg5.rebuild_mesh()
multi_material_verts = vg5.vertex_count
print(f"  Multi-material greedy: {multi_material_verts} vertices")

# Should have 6 quads per material half = 12 quads = 72 vertices
# But there's a shared face between them that gets culled
# Actually: each 2x4x4 block has 5 exposed faces (not the shared internal face)
# So 5 + 5 = 10 quads = 60 vertices, but may be more due to the contact face
test("Multi-material produces vertices", multi_material_verts > 0)

# =============================================================================
# Test hollow box (interior faces)
# =============================================================================

print("\n=== Testing hollow box ===")

vg6 = mcrfpy.VoxelGrid((8, 8, 8), cell_size=1.0)
stone6 = vg6.add_material("stone", (128, 128, 128))
vg6.fill_box_hollow((0, 0, 0), (7, 7, 7), stone6, thickness=1)

vg6.greedy_meshing = False
vg6.rebuild_mesh()
standard_hollow = vg6.vertex_count
print(f"  Standard: {standard_hollow} vertices")

vg6.greedy_meshing = True
vg6.rebuild_mesh()
greedy_hollow = vg6.vertex_count
print(f"  Greedy: {greedy_hollow} vertices")

# Hollow box has 6 outer faces and 6 inner faces
# Greedy should merge each face into one quad
# Expected: 12 quads * 6 verts = 72 vertices
test("Hollow box: greedy reduces vertices", greedy_hollow < standard_hollow)

# =============================================================================
# Test floor slab (single layer)
# =============================================================================

print("\n=== Testing floor slab (single layer) ===")

vg7 = mcrfpy.VoxelGrid((10, 1, 10), cell_size=1.0)
floor_mat = vg7.add_material("floor", (100, 80, 60))
vg7.fill(floor_mat)

vg7.greedy_meshing = False
vg7.rebuild_mesh()
standard_floor = vg7.vertex_count
print(f"  Standard: {standard_floor} vertices")

vg7.greedy_meshing = True
vg7.rebuild_mesh()
greedy_floor = vg7.vertex_count
print(f"  Greedy: {greedy_floor} vertices")

# Floor slab: 10x10 top face + 10x10 bottom face + 4 edge faces (10x1 each)
# Greedy: 6 quads = 36 vertices
test("Floor slab: greedy = 36 vertices", greedy_floor == 36)

# =============================================================================
# Test that mesh is marked dirty when property changes
# =============================================================================

print("\n=== Testing dirty flag behavior ===")

vg8 = mcrfpy.VoxelGrid((4, 4, 4), cell_size=1.0)
stone8 = vg8.add_material("stone", (128, 128, 128))
vg8.fill(stone8)

# Build mesh first
vg8.greedy_meshing = False
vg8.rebuild_mesh()
first_count = vg8.vertex_count

# Change greedy_meshing - mesh should be marked dirty
vg8.greedy_meshing = True
# Rebuild
vg8.rebuild_mesh()
second_count = vg8.vertex_count

test("Changing greedy_meshing affects vertex count", first_count != second_count)

# =============================================================================
# Summary
# =============================================================================

print(f"\n=== Results: {tests_passed} passed, {tests_failed} failed ===")

if tests_failed > 0:
    sys.exit(1)
else:
    print("All tests passed!")
    sys.exit(0)
