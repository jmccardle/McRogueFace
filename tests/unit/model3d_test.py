# model3d_test.py - Unit test for Model3D 3D model resource

import mcrfpy
import sys

def test_model3d_cube():
    """Test Model3D.cube() creates valid model"""
    cube = mcrfpy.Model3D.cube(2.0)

    assert cube.name == "cube", f"Expected name='cube', got '{cube.name}'"
    assert cube.vertex_count == 24, f"Expected 24 vertices, got {cube.vertex_count}"
    assert cube.triangle_count == 12, f"Expected 12 triangles, got {cube.triangle_count}"
    assert cube.has_skeleton == False, f"Expected has_skeleton=False, got {cube.has_skeleton}"
    assert cube.mesh_count == 1, f"Expected 1 mesh, got {cube.mesh_count}"

    # Check bounds for size=2.0 cube
    bounds = cube.bounds
    assert bounds is not None, "Bounds should not be None"
    min_b, max_b = bounds
    assert min_b == (-1.0, -1.0, -1.0), f"Expected min=(-1,-1,-1), got {min_b}"
    assert max_b == (1.0, 1.0, 1.0), f"Expected max=(1,1,1), got {max_b}"

    print("[PASS] test_model3d_cube")

def test_model3d_cube_default_size():
    """Test Model3D.cube() with default size"""
    cube = mcrfpy.Model3D.cube()

    # Default size is 1.0, so bounds should be -0.5 to 0.5
    bounds = cube.bounds
    min_b, max_b = bounds
    assert abs(min_b[0] - (-0.5)) < 0.001, f"Expected min.x=-0.5, got {min_b[0]}"
    assert abs(max_b[0] - 0.5) < 0.001, f"Expected max.x=0.5, got {max_b[0]}"

    print("[PASS] test_model3d_cube_default_size")

def test_model3d_plane():
    """Test Model3D.plane() creates valid model"""
    plane = mcrfpy.Model3D.plane(4.0, 2.0, 2)

    assert plane.name == "plane", f"Expected name='plane', got '{plane.name}'"
    # 2 segments = 3x3 grid = 9 vertices
    assert plane.vertex_count == 9, f"Expected 9 vertices, got {plane.vertex_count}"
    # 2x2 quads = 8 triangles
    assert plane.triangle_count == 8, f"Expected 8 triangles, got {plane.triangle_count}"
    assert plane.has_skeleton == False, f"Expected has_skeleton=False"

    # Bounds should be width/2, 0, depth/2
    bounds = plane.bounds
    min_b, max_b = bounds
    assert abs(min_b[0] - (-2.0)) < 0.001, f"Expected min.x=-2, got {min_b[0]}"
    assert abs(max_b[0] - 2.0) < 0.001, f"Expected max.x=2, got {max_b[0]}"
    assert abs(min_b[2] - (-1.0)) < 0.001, f"Expected min.z=-1, got {min_b[2]}"
    assert abs(max_b[2] - 1.0) < 0.001, f"Expected max.z=1, got {max_b[2]}"

    print("[PASS] test_model3d_plane")

def test_model3d_plane_default():
    """Test Model3D.plane() with default parameters"""
    plane = mcrfpy.Model3D.plane()

    # Default is 1x1 with 1 segment = 4 vertices, 2 triangles
    assert plane.vertex_count == 4, f"Expected 4 vertices, got {plane.vertex_count}"
    assert plane.triangle_count == 2, f"Expected 2 triangles, got {plane.triangle_count}"

    print("[PASS] test_model3d_plane_default")

def test_model3d_sphere():
    """Test Model3D.sphere() creates valid model"""
    sphere = mcrfpy.Model3D.sphere(1.0, 8, 6)

    assert sphere.name == "sphere", f"Expected name='sphere', got '{sphere.name}'"
    # vertices = (segments+1) * (rings+1) = 9 * 7 = 63
    assert sphere.vertex_count == 63, f"Expected 63 vertices, got {sphere.vertex_count}"
    # triangles = 2 * segments * rings = 2 * 8 * 6 = 96
    assert sphere.triangle_count == 96, f"Expected 96 triangles, got {sphere.triangle_count}"

    # Bounds should be radius in all directions
    bounds = sphere.bounds
    min_b, max_b = bounds
    assert abs(min_b[0] - (-1.0)) < 0.001, f"Expected min.x=-1, got {min_b[0]}"
    assert abs(max_b[0] - 1.0) < 0.001, f"Expected max.x=1, got {max_b[0]}"

    print("[PASS] test_model3d_sphere")

def test_model3d_sphere_default():
    """Test Model3D.sphere() with default parameters"""
    sphere = mcrfpy.Model3D.sphere()

    # Default radius=0.5, segments=16, rings=12
    # vertices = 17 * 13 = 221
    assert sphere.vertex_count == 221, f"Expected 221 vertices, got {sphere.vertex_count}"
    # triangles = 2 * 16 * 12 = 384
    assert sphere.triangle_count == 384, f"Expected 384 triangles, got {sphere.triangle_count}"

    print("[PASS] test_model3d_sphere_default")

def test_model3d_empty():
    """Test creating empty Model3D"""
    empty = mcrfpy.Model3D()

    assert empty.name == "unnamed", f"Expected name='unnamed', got '{empty.name}'"
    assert empty.vertex_count == 0, f"Expected 0 vertices, got {empty.vertex_count}"
    assert empty.triangle_count == 0, f"Expected 0 triangles, got {empty.triangle_count}"
    assert empty.mesh_count == 0, f"Expected 0 meshes, got {empty.mesh_count}"

    print("[PASS] test_model3d_empty")

def test_model3d_repr():
    """Test Model3D string representation"""
    cube = mcrfpy.Model3D.cube()
    repr_str = repr(cube)

    assert "Model3D" in repr_str, f"Expected 'Model3D' in repr, got {repr_str}"
    assert "cube" in repr_str, f"Expected 'cube' in repr, got {repr_str}"
    assert "24" in repr_str, f"Expected vertex count in repr, got {repr_str}"

    print("[PASS] test_model3d_repr")

def test_entity3d_model_property():
    """Test Entity3D.model property"""
    e = mcrfpy.Entity3D(pos=(0, 0))

    # Initially no model
    assert e.model is None, f"Expected model=None, got {e.model}"

    # Assign model
    cube = mcrfpy.Model3D.cube()
    e.model = cube
    assert e.model is not None, "Expected model to be set"
    assert e.model.name == "cube", f"Expected model.name='cube', got {e.model.name}"

    # Swap model
    sphere = mcrfpy.Model3D.sphere()
    e.model = sphere
    assert e.model.name == "sphere", f"Expected model.name='sphere', got {e.model.name}"

    # Clear model
    e.model = None
    assert e.model is None, f"Expected model=None after clearing"

    print("[PASS] test_entity3d_model_property")

def test_entity3d_model_type_error():
    """Test Entity3D.model raises TypeError for invalid input"""
    e = mcrfpy.Entity3D()

    try:
        e.model = "not a model"
        print("[FAIL] test_entity3d_model_type_error: Expected TypeError")
        return
    except TypeError:
        pass

    try:
        e.model = 123
        print("[FAIL] test_entity3d_model_type_error: Expected TypeError")
        return
    except TypeError:
        pass

    print("[PASS] test_entity3d_model_type_error")

def test_entity3d_with_model_in_viewport():
    """Test Entity3D with model in a Viewport3D"""
    vp = mcrfpy.Viewport3D()
    vp.set_grid_size(16, 16)

    # Create entity with model
    cube = mcrfpy.Model3D.cube(0.5)
    e = mcrfpy.Entity3D(pos=(8, 8))
    e.model = cube

    # Add to viewport
    vp.entities.append(e)

    # Verify model is preserved
    retrieved = vp.entities[0]
    assert retrieved.model is not None, "Expected model to be preserved"
    assert retrieved.model.name == "cube", f"Expected model.name='cube', got {retrieved.model.name}"

    print("[PASS] test_entity3d_with_model_in_viewport")

def run_all_tests():
    """Run all Model3D tests"""
    tests = [
        test_model3d_cube,
        test_model3d_cube_default_size,
        test_model3d_plane,
        test_model3d_plane_default,
        test_model3d_sphere,
        test_model3d_sphere_default,
        test_model3d_empty,
        test_model3d_repr,
        test_entity3d_model_property,
        test_entity3d_model_type_error,
        test_entity3d_with_model_in_viewport,
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
            print(f"[ERROR] {test.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n=== Results: {passed} passed, {failed} failed ===")
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
