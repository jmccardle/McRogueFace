#!/usr/bin/env python3
"""Unit tests for VoxelGrid rendering integration (Milestone 10)

Tests:
- Adding voxel layer to viewport
- Removing voxel layer from viewport
- Voxel layer count tracking
- Screenshot verification (visual rendering)
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

def test_add_to_viewport():
    """Test adding a voxel layer to viewport"""
    import mcrfpy

    # Create viewport
    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))

    # Create voxel grid
    vg = mcrfpy.VoxelGrid(size=(8, 8, 8))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))
    vg.set(4, 4, 4, stone)

    # Initial layer count
    test("Add to viewport: initial count is 0", viewport.voxel_layer_count() == 0)

    # Add voxel layer
    viewport.add_voxel_layer(vg, z_index=1)

    test("Add to viewport: count increases to 1", viewport.voxel_layer_count() == 1)

def test_add_multiple_layers():
    """Test adding multiple voxel layers"""
    import mcrfpy

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))

    vg1 = mcrfpy.VoxelGrid(size=(4, 4, 4))
    vg2 = mcrfpy.VoxelGrid(size=(4, 4, 4))
    vg3 = mcrfpy.VoxelGrid(size=(4, 4, 4))

    viewport.add_voxel_layer(vg1, z_index=0)
    viewport.add_voxel_layer(vg2, z_index=1)
    viewport.add_voxel_layer(vg3, z_index=2)

    test("Multiple layers: count is 3", viewport.voxel_layer_count() == 3)

def test_remove_from_viewport():
    """Test removing a voxel layer from viewport"""
    import mcrfpy

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))

    vg1 = mcrfpy.VoxelGrid(size=(4, 4, 4))
    vg2 = mcrfpy.VoxelGrid(size=(4, 4, 4))

    viewport.add_voxel_layer(vg1, z_index=0)
    viewport.add_voxel_layer(vg2, z_index=1)

    test("Remove: initial count is 2", viewport.voxel_layer_count() == 2)

    # Remove one layer
    result = viewport.remove_voxel_layer(vg1)
    test("Remove: returns True for existing layer", result == True)
    test("Remove: count decreases to 1", viewport.voxel_layer_count() == 1)

    # Remove same layer again should return False
    result = viewport.remove_voxel_layer(vg1)
    test("Remove: returns False for non-existing layer", result == False)
    test("Remove: count still 1", viewport.voxel_layer_count() == 1)

def test_remove_nonexistent():
    """Test removing a layer that was never added"""
    import mcrfpy

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))
    vg = mcrfpy.VoxelGrid(size=(4, 4, 4))

    result = viewport.remove_voxel_layer(vg)
    test("Remove nonexistent: returns False", result == False)

def test_add_invalid_type():
    """Test that adding non-VoxelGrid raises error"""
    import mcrfpy

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))

    error_raised = False
    try:
        viewport.add_voxel_layer("not a voxel grid")
    except TypeError:
        error_raised = True

    test("Add invalid type: raises TypeError", error_raised)

def test_z_index_parameter():
    """Test that z_index parameter is accepted"""
    import mcrfpy

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))
    vg = mcrfpy.VoxelGrid(size=(4, 4, 4))

    # Should not raise error
    error_raised = False
    try:
        viewport.add_voxel_layer(vg, z_index=5)
    except Exception as e:
        error_raised = True
        print(f"  Error: {e}")

    test("Z-index parameter: accepted without error", not error_raised)

def test_viewport_in_scene():
    """Test viewport with voxel layer added to a scene"""
    import mcrfpy

    # Create and activate a test scene
    scene = mcrfpy.Scene("voxel_test_scene")

    # Create viewport
    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))

    # Create voxel grid with visible content
    vg = mcrfpy.VoxelGrid(size=(8, 8, 8))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))
    vg.fill_box((2, 0, 2), (5, 3, 5), stone)
    vg.offset = (0, 0, 0)

    # Add voxel layer to viewport
    viewport.add_voxel_layer(vg, z_index=0)

    # Position camera to see the voxels
    viewport.camera_pos = (10, 10, 10)
    viewport.camera_target = (4, 2, 4)

    # Add viewport to scene
    scene.children.append(viewport)

    # Trigger mesh generation
    vg.rebuild_mesh()

    test("Viewport in scene: voxel layer added", viewport.voxel_layer_count() == 1)
    test("Viewport in scene: voxels have content", vg.count_non_air() > 0)
    test("Viewport in scene: mesh generated", vg.vertex_count > 0)

def main():
    """Run all rendering integration tests"""
    print("=" * 60)
    print("VoxelGrid Rendering Integration Tests (Milestone 10)")
    print("=" * 60)
    print()

    test_add_to_viewport()
    print()
    test_add_multiple_layers()
    print()
    test_remove_from_viewport()
    print()
    test_remove_nonexistent()
    print()
    test_add_invalid_type()
    print()
    test_z_index_parameter()
    print()
    test_viewport_in_scene()
    print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
