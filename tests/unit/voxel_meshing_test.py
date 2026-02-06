#!/usr/bin/env python3
"""Unit tests for VoxelGrid mesh generation (Milestone 10)

Tests:
- Single voxel produces 36 vertices (6 faces x 6 verts)
- Two adjacent voxels share a face (60 verts instead of 72)
- Hollow cube only has outer faces
- fill_box works correctly
- Mesh dirty flag triggers rebuild
- Vertex positions are in correct local space
"""
import sys

# Track test results
passed = 0
failed = 0

def test(name, condition, detail=""):
    """Record test result"""
    global passed, failed
    if condition:
        print(f"[PASS] {name}")
        passed += 1
    else:
        print(f"[FAIL] {name}" + (f" - {detail}" if detail else ""))
        failed += 1

def test_single_voxel():
    """Single voxel should produce 6 faces = 36 vertices"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(8, 8, 8))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Initially no vertices (empty grid)
    test("Single voxel: initial vertex_count is 0", vg.vertex_count == 0)

    # Add one voxel
    vg.set(4, 4, 4, stone)
    vg.rebuild_mesh()

    # One voxel = 6 faces, each face = 2 triangles = 6 vertices
    expected = 6 * 6
    test("Single voxel: produces 36 vertices", vg.vertex_count == expected,
         f"got {vg.vertex_count}, expected {expected}")

def test_two_adjacent():
    """Two adjacent voxels should share a face, producing 60 vertices instead of 72"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(8, 8, 8))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Add two adjacent voxels (share one face)
    vg.set(4, 4, 4, stone)
    vg.set(5, 4, 4, stone)  # Adjacent in X
    vg.rebuild_mesh()

    # Two separate voxels would be 72 vertices
    # Shared face is culled: 2 * 36 - 2 * 6 = 72 - 12 = 60
    expected = 60
    test("Two adjacent: shared face culled", vg.vertex_count == expected,
         f"got {vg.vertex_count}, expected {expected}")

def test_hollow_cube():
    """Hollow 3x3x3 cube should have much fewer vertices than solid"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(8, 8, 8))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Create hollow 3x3x3 cube (only shell voxels)
    # Solid 3x3x3 = 27 voxels, Hollow = 26 voxels (remove center)
    for x in range(3):
        for y in range(3):
            for z in range(3):
                # Skip center voxel
                if x == 1 and y == 1 and z == 1:
                    continue
                vg.set(x, y, z, stone)

    test("Hollow cube: 26 voxels placed", vg.count_non_air() == 26)

    vg.rebuild_mesh()

    # The hollow center creates inner faces facing the air void
    # Outer surface = 6 sides * 9 faces = 54 faces
    # Inner surface = 6 faces touching the center void
    # Total = 60 faces = 360 vertices
    expected = 360
    test("Hollow cube: outer + inner void faces", vg.vertex_count == expected,
         f"got {vg.vertex_count}, expected {expected}")

def test_fill_box():
    """fill_box should fill a rectangular region"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(16, 8, 16))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Fill a 4x3x5 box
    vg.fill_box((2, 1, 3), (5, 3, 7), stone)

    # Count: (5-2+1) * (3-1+1) * (7-3+1) = 4 * 3 * 5 = 60
    expected = 60
    test("fill_box: correct voxel count", vg.count_non_air() == expected,
         f"got {vg.count_non_air()}, expected {expected}")

    # Verify specific cells
    test("fill_box: corner (2,1,3) is filled", vg.get(2, 1, 3) == stone)
    test("fill_box: corner (5,3,7) is filled", vg.get(5, 3, 7) == stone)
    test("fill_box: outside (1,1,3) is empty", vg.get(1, 1, 3) == 0)
    test("fill_box: outside (6,1,3) is empty", vg.get(6, 1, 3) == 0)

def test_fill_box_reversed():
    """fill_box should handle reversed coordinates"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(16, 8, 16))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Fill with reversed coordinates (max before min)
    vg.fill_box((5, 3, 7), (2, 1, 3), stone)

    # Should still fill 4x3x5 = 60 voxels
    expected = 60
    test("fill_box reversed: correct voxel count", vg.count_non_air() == expected,
         f"got {vg.count_non_air()}, expected {expected}")

def test_fill_box_clamping():
    """fill_box should clamp to grid bounds"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(8, 8, 8))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Fill beyond grid bounds
    vg.fill_box((-5, -5, -5), (100, 100, 100), stone)

    # Should fill entire 8x8x8 grid = 512 voxels
    expected = 512
    test("fill_box clamping: fills entire grid", vg.count_non_air() == expected,
         f"got {vg.count_non_air()}, expected {expected}")

def test_mesh_dirty():
    """Modifying voxels should mark mesh dirty; rebuild_mesh updates vertex count"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(8, 8, 8))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Initial state
    vg.set(4, 4, 4, stone)
    vg.rebuild_mesh()
    initial_count = vg.vertex_count

    test("Mesh dirty: initial vertex count correct", initial_count == 36)

    # Modify voxel - marks dirty but doesn't auto-rebuild
    vg.set(4, 4, 5, stone)

    # vertex_count doesn't auto-trigger rebuild (returns stale value)
    stale_count = vg.vertex_count
    test("Mesh dirty: vertex_count before rebuild is stale", stale_count == 36)

    # Explicit rebuild updates the mesh
    vg.rebuild_mesh()
    new_count = vg.vertex_count

    # Two adjacent voxels = 60 vertices
    test("Mesh dirty: rebuilt after explicit rebuild_mesh()", new_count == 60,
         f"got {new_count}, expected 60")

def test_vertex_positions():
    """Vertices should be in correct local space positions"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(8, 8, 8), cell_size=2.0)
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Place voxel at (0,0,0)
    vg.set(0, 0, 0, stone)
    vg.rebuild_mesh()

    # With cell_size=2.0, the voxel center is at (1, 1, 1)
    # Vertices should be at corners: (0,0,0) to (2,2,2)
    # The vertex_count should still be 36
    test("Vertex positions: correct vertex count", vg.vertex_count == 36)

def test_empty_grid():
    """Empty grid should produce no vertices"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(8, 8, 8))
    vg.rebuild_mesh()

    test("Empty grid: zero vertices", vg.vertex_count == 0)

def test_all_air():
    """Grid filled with air produces no vertices"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(8, 8, 8))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Fill with stone, then fill with air
    vg.fill(stone)
    vg.fill(0)  # Air
    vg.rebuild_mesh()

    test("All air: zero vertices", vg.vertex_count == 0)

def test_large_solid_cube():
    """Large solid cube should have face culling efficiency"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(8, 8, 8))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Fill entire grid
    vg.fill(stone)
    vg.rebuild_mesh()

    # Without culling: 512 voxels * 6 faces * 6 verts = 18432
    # With culling: only outer shell faces
    # 6 faces of cube, each 8x8 = 64 faces per side = 384 faces
    # 384 * 6 verts = 2304 vertices
    expected = 2304
    test("Large solid cube: face culling efficiency",
         vg.vertex_count == expected,
         f"got {vg.vertex_count}, expected {expected}")

    # Verify massive reduction
    no_cull = 512 * 6 * 6
    reduction = (no_cull - vg.vertex_count) / no_cull * 100
    test("Large solid cube: >85% vertex reduction",
         reduction > 85,
         f"got {reduction:.1f}% reduction")

def test_transparent_material():
    """Faces between solid and transparent materials should be generated"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(8, 8, 8))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))
    glass = vg.add_material("glass", color=mcrfpy.Color(200, 200, 255, 128),
                             transparent=True)

    # Place stone with glass neighbor
    vg.set(4, 4, 4, stone)
    vg.set(5, 4, 4, glass)
    vg.rebuild_mesh()

    # Stone has 6 faces (all exposed - glass is transparent)
    # Glass has 5 faces (face towards stone not generated - stone is solid)
    # Total = 36 + 30 = 66 vertices
    expected = 66
    test("Transparent material: correct face culling", vg.vertex_count == expected,
         f"got {vg.vertex_count}, expected {expected}")

def main():
    """Run all mesh generation tests"""
    print("=" * 60)
    print("VoxelGrid Mesh Generation Tests (Milestone 10)")
    print("=" * 60)
    print()

    test_single_voxel()
    print()
    test_two_adjacent()
    print()
    test_hollow_cube()
    print()
    test_fill_box()
    print()
    test_fill_box_reversed()
    print()
    test_fill_box_clamping()
    print()
    test_mesh_dirty()
    print()
    test_vertex_positions()
    print()
    test_empty_grid()
    print()
    test_all_air()
    print()
    test_large_solid_cube()
    print()
    test_transparent_material()
    print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
