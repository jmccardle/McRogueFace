# animated_model_test.py - Test loading actual animated glTF models
# Tests skeleton and animation data loading from real files

import mcrfpy
import sys
import os

def test_rigged_simple():
    """Test loading RiggedSimple - a cylinder with 2 bones"""
    print("Loading RiggedSimple.glb...")
    model = mcrfpy.Model3D("../assets/models/RiggedSimple.glb")

    print(f"  has_skeleton: {model.has_skeleton}")
    print(f"  bone_count: {model.bone_count}")
    print(f"  animation_clips: {model.animation_clips}")
    print(f"  vertex_count: {model.vertex_count}")
    print(f"  triangle_count: {model.triangle_count}")
    print(f"  mesh_count: {model.mesh_count}")

    assert model.has_skeleton == True, f"Expected has_skeleton=True, got {model.has_skeleton}"
    assert model.bone_count > 0, f"Expected bone_count > 0, got {model.bone_count}"
    assert len(model.animation_clips) > 0, f"Expected animation clips, got {model.animation_clips}"

    print("[PASS] test_rigged_simple")

def test_cesium_man():
    """Test loading CesiumMan - animated humanoid figure"""
    print("Loading CesiumMan.glb...")
    model = mcrfpy.Model3D("../assets/models/CesiumMan.glb")

    print(f"  has_skeleton: {model.has_skeleton}")
    print(f"  bone_count: {model.bone_count}")
    print(f"  animation_clips: {model.animation_clips}")
    print(f"  vertex_count: {model.vertex_count}")
    print(f"  triangle_count: {model.triangle_count}")
    print(f"  mesh_count: {model.mesh_count}")

    assert model.has_skeleton == True, f"Expected has_skeleton=True, got {model.has_skeleton}"
    assert model.bone_count > 0, f"Expected bone_count > 0, got {model.bone_count}"
    assert len(model.animation_clips) > 0, f"Expected animation clips, got {model.animation_clips}"

    print("[PASS] test_cesium_man")

def test_entity_with_animated_model():
    """Test Entity3D with an animated model attached"""
    print("Testing Entity3D with animated model...")

    model = mcrfpy.Model3D("../assets/models/RiggedSimple.glb")
    entity = mcrfpy.Entity3D()
    entity.model = model

    # Check animation clips are available
    clips = model.animation_clips
    print(f"  Available clips: {clips}")

    if clips:
        # Set animation clip
        entity.anim_clip = clips[0]
        assert entity.anim_clip == clips[0], f"Expected clip '{clips[0]}', got '{entity.anim_clip}'"

        # Test animation time progression
        entity.anim_time = 0.5
        assert abs(entity.anim_time - 0.5) < 0.001, f"Expected anim_time~=0.5, got {entity.anim_time}"

        # Test speed
        entity.anim_speed = 2.0
        assert abs(entity.anim_speed - 2.0) < 0.001, f"Expected anim_speed~=2.0, got {entity.anim_speed}"

    print("[PASS] test_entity_with_animated_model")

def run_all_tests():
    """Run all animated model tests"""
    tests = [
        test_rigged_simple,
        test_cesium_man,
        test_entity_with_animated_model,
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
