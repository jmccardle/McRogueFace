# skeleton_test.py - Unit tests for skeletal animation in Model3D

import mcrfpy
import sys

def test_model_skeleton_default():
    """Test that procedural models don't have skeletons"""
    cube = mcrfpy.Model3D.cube(1.0)

    assert cube.has_skeleton == False, f"Expected cube.has_skeleton=False, got {cube.has_skeleton}"
    assert cube.bone_count == 0, f"Expected cube.bone_count=0, got {cube.bone_count}"
    assert cube.animation_clips == [], f"Expected empty animation_clips, got {cube.animation_clips}"

    print("[PASS] test_model_skeleton_default")

def test_model_animation_clips_empty():
    """Test that models without skeleton have no animation clips"""
    sphere = mcrfpy.Model3D.sphere(0.5)

    clips = sphere.animation_clips
    assert isinstance(clips, list), f"Expected list, got {type(clips)}"
    assert len(clips) == 0, f"Expected 0 clips, got {len(clips)}"

    print("[PASS] test_model_animation_clips_empty")

def test_model_properties():
    """Test Model3D skeleton-related property access"""
    plane = mcrfpy.Model3D.plane(2.0, 2.0)

    # These should all work without error
    _ = plane.has_skeleton
    _ = plane.bone_count
    _ = plane.animation_clips
    _ = plane.name
    _ = plane.vertex_count
    _ = plane.triangle_count
    _ = plane.mesh_count
    _ = plane.bounds

    print("[PASS] test_model_properties")

def test_model_repr_no_skeleton():
    """Test Model3D repr for non-skeletal model"""
    cube = mcrfpy.Model3D.cube()
    r = repr(cube)

    assert "Model3D" in r, f"Expected 'Model3D' in repr, got {r}"
    assert "skeletal" not in r, f"Non-skeletal model should not say 'skeletal' in repr"

    print("[PASS] test_model_repr_no_skeleton")

def run_all_tests():
    """Run all skeleton tests"""
    tests = [
        test_model_skeleton_default,
        test_model_animation_clips_empty,
        test_model_properties,
        test_model_repr_no_skeleton,
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
