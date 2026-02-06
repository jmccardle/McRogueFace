# mesh_instance_test.py - Unit test for MeshLayer mesh instances and Viewport3D mesh APIs

import mcrfpy
import sys

def test_viewport3d_add_mesh():
    """Test adding meshes to Viewport3D layers"""
    vp = mcrfpy.Viewport3D()

    # Add a mesh layer first
    vp.add_layer("ground", z_index=0)

    # Create a model to place (simple cube primitive)
    model = mcrfpy.Model3D()

    # Add mesh instance at position
    result = vp.add_mesh("ground", model, pos=(5.0, 0.0, 5.0))

    # Should return the index of the added mesh
    assert result is not None, "Expected add_mesh to return something"
    assert isinstance(result, int), f"Expected int index, got {type(result)}"
    assert result == 0, f"Expected first mesh index 0, got {result}"

    print("[PASS] test_viewport3d_add_mesh")

def test_viewport3d_add_mesh_with_transform():
    """Test adding meshes with rotation and scale"""
    vp = mcrfpy.Viewport3D()
    vp.add_layer("buildings", z_index=0)

    model = mcrfpy.Model3D()

    # Add with rotation (in degrees as per API)
    idx1 = vp.add_mesh("buildings", model, pos=(10.0, 0.0, 10.0), rotation=90)
    assert idx1 == 0, f"Expected first mesh index 0, got {idx1}"

    # Add with scale
    idx2 = vp.add_mesh("buildings", model, pos=(15.0, 0.0, 15.0), scale=2.0)
    assert idx2 == 1, f"Expected second mesh index 1, got {idx2}"

    # Add with both rotation and scale
    idx3 = vp.add_mesh("buildings", model, pos=(5.0, 0.0, 5.0), rotation=45, scale=0.5)
    assert idx3 == 2, f"Expected third mesh index 2, got {idx3}"

    print("[PASS] test_viewport3d_add_mesh_with_transform")

def test_viewport3d_clear_meshes():
    """Test clearing meshes from a layer"""
    vp = mcrfpy.Viewport3D()
    vp.add_layer("objects", z_index=0)

    model = mcrfpy.Model3D()

    # Add several meshes
    vp.add_mesh("objects", model, pos=(1.0, 0.0, 1.0))
    vp.add_mesh("objects", model, pos=(2.0, 0.0, 2.0))
    vp.add_mesh("objects", model, pos=(3.0, 0.0, 3.0))

    # Clear meshes from layer
    vp.clear_meshes("objects")

    # Add a new mesh - should get index 0 since list was cleared
    idx = vp.add_mesh("objects", model, pos=(0.0, 0.0, 0.0))
    assert idx == 0, f"Expected index 0 after clear, got {idx}"

    print("[PASS] test_viewport3d_clear_meshes")

def test_viewport3d_place_blocking():
    """Test placing blocking information on the navigation grid"""
    vp = mcrfpy.Viewport3D()

    # Initialize navigation grid first
    vp.set_grid_size(width=16, depth=16)

    # Place blocking cell (unwalkable, non-transparent)
    vp.place_blocking(grid_pos=(5, 5), footprint=(1, 1))

    # Place larger blocking footprint
    vp.place_blocking(grid_pos=(10, 10), footprint=(2, 2))

    # Place blocking with custom walkability
    vp.place_blocking(grid_pos=(0, 0), footprint=(3, 3), walkable=False, transparent=True)

    # Verify the cells were marked (check via VoxelPoint)
    cell = vp.at(5, 5)
    assert cell.walkable == False, f"Expected cell (5,5) unwalkable, got walkable={cell.walkable}"

    cell_transparent = vp.at(0, 0)
    assert cell_transparent.transparent == True, f"Expected cell (0,0) transparent"

    print("[PASS] test_viewport3d_place_blocking")

def test_viewport3d_mesh_layer_operations():
    """Test various mesh layer operations"""
    vp = mcrfpy.Viewport3D()

    # Create multiple layers
    vp.add_layer("floor", z_index=0)
    vp.add_layer("walls", z_index=1)
    vp.add_layer("props", z_index=2)

    model = mcrfpy.Model3D()

    # Add meshes to different layers
    vp.add_mesh("floor", model, pos=(0.0, 0.0, 0.0))
    vp.add_mesh("walls", model, pos=(1.0, 1.0, 0.0), rotation=0, scale=1.5)
    vp.add_mesh("props", model, pos=(2.0, 0.0, 2.0), scale=0.25)

    # Clear only one layer
    vp.clear_meshes("walls")

    # Other layers should be unaffected
    # (Can verify by adding to them and checking indices)
    idx_floor = vp.add_mesh("floor", model, pos=(5.0, 0.0, 5.0))
    assert idx_floor == 1, f"Expected floor mesh index 1, got {idx_floor}"

    idx_walls = vp.add_mesh("walls", model, pos=(5.0, 0.0, 5.0))
    assert idx_walls == 0, f"Expected walls mesh index 0 after clear, got {idx_walls}"

    print("[PASS] test_viewport3d_mesh_layer_operations")

def test_auto_layer_creation():
    """Test that add_mesh auto-creates layers if they don't exist"""
    vp = mcrfpy.Viewport3D()
    model = mcrfpy.Model3D()

    # Add mesh to a layer that doesn't exist yet - should auto-create it
    idx = vp.add_mesh("auto_created", model, pos=(0.0, 0.0, 0.0))
    assert idx == 0, f"Expected index 0 for auto-created layer, got {idx}"

    # Verify the layer was created
    layer = vp.get_layer("auto_created")
    assert layer is not None, "Expected auto_created layer to exist"

    print("[PASS] test_auto_layer_creation")

def test_invalid_layer_clear():
    """Test error handling for clearing non-existent layers"""
    vp = mcrfpy.Viewport3D()

    # Try to clear meshes from non-existent layer
    try:
        vp.clear_meshes("nonexistent")
        # If it doesn't raise, it might just silently succeed (which is fine too)
        print("[PASS] test_invalid_layer_clear (no exception)")
        return
    except (ValueError, KeyError, RuntimeError):
        print("[PASS] test_invalid_layer_clear (exception raised)")
        return

def run_all_tests():
    """Run all mesh instance tests"""
    tests = [
        test_viewport3d_add_mesh,
        test_viewport3d_add_mesh_with_transform,
        test_viewport3d_clear_meshes,
        test_viewport3d_place_blocking,
        test_viewport3d_mesh_layer_operations,
        test_auto_layer_creation,
        test_invalid_layer_clear,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__}: {e}")
            failed += 1

    print(f"\n=== Results: {passed} passed, {failed} failed ===")
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
