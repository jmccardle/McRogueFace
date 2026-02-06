# animation_test.py - Unit tests for Entity3D skeletal animation

import mcrfpy
import sys

def test_entity3d_animation_defaults():
    """Test Entity3D animation property defaults"""
    entity = mcrfpy.Entity3D()

    # Default animation state
    assert entity.anim_clip == "", f"Expected empty anim_clip, got '{entity.anim_clip}'"
    assert entity.anim_time == 0.0, f"Expected anim_time=0.0, got {entity.anim_time}"
    assert entity.anim_speed == 1.0, f"Expected anim_speed=1.0, got {entity.anim_speed}"
    assert entity.anim_loop == True, f"Expected anim_loop=True, got {entity.anim_loop}"
    assert entity.anim_paused == False, f"Expected anim_paused=False, got {entity.anim_paused}"
    assert entity.anim_frame == 0, f"Expected anim_frame=0, got {entity.anim_frame}"

    # Auto-animate defaults
    assert entity.auto_animate == True, f"Expected auto_animate=True, got {entity.auto_animate}"
    assert entity.walk_clip == "walk", f"Expected walk_clip='walk', got '{entity.walk_clip}'"
    assert entity.idle_clip == "idle", f"Expected idle_clip='idle', got '{entity.idle_clip}'"

    print("[PASS] test_entity3d_animation_defaults")

def test_entity3d_animation_properties():
    """Test setting Entity3D animation properties"""
    entity = mcrfpy.Entity3D()

    # Set animation clip
    entity.anim_clip = "test_anim"
    assert entity.anim_clip == "test_anim", f"Expected 'test_anim', got '{entity.anim_clip}'"

    # Set animation time
    entity.anim_time = 1.5
    assert abs(entity.anim_time - 1.5) < 0.001, f"Expected anim_time~=1.5, got {entity.anim_time}"

    # Set animation speed
    entity.anim_speed = 2.0
    assert abs(entity.anim_speed - 2.0) < 0.001, f"Expected anim_speed~=2.0, got {entity.anim_speed}"

    # Set loop
    entity.anim_loop = False
    assert entity.anim_loop == False, f"Expected anim_loop=False, got {entity.anim_loop}"

    # Set paused
    entity.anim_paused = True
    assert entity.anim_paused == True, f"Expected anim_paused=True, got {entity.anim_paused}"

    print("[PASS] test_entity3d_animation_properties")

def test_entity3d_auto_animate():
    """Test Entity3D auto-animate settings"""
    entity = mcrfpy.Entity3D()

    # Disable auto-animate
    entity.auto_animate = False
    assert entity.auto_animate == False

    # Set custom clip names
    entity.walk_clip = "run"
    entity.idle_clip = "stand"
    assert entity.walk_clip == "run"
    assert entity.idle_clip == "stand"

    print("[PASS] test_entity3d_auto_animate")

def test_entity3d_animation_callback():
    """Test Entity3D animation complete callback"""
    entity = mcrfpy.Entity3D()
    callback_called = [False]
    callback_args = [None, None]

    def on_complete(ent, clip_name):
        callback_called[0] = True
        callback_args[0] = ent
        callback_args[1] = clip_name

    # Set callback
    entity.on_anim_complete = on_complete
    assert entity.on_anim_complete is not None

    # Clear callback
    entity.on_anim_complete = None
    # Should not raise error even though callback is None

    print("[PASS] test_entity3d_animation_callback")

def test_entity3d_animation_callback_invalid():
    """Test that non-callable is rejected for animation callback"""
    entity = mcrfpy.Entity3D()

    try:
        entity.on_anim_complete = "not a function"
        assert False, "Should have raised TypeError"
    except TypeError:
        pass

    print("[PASS] test_entity3d_animation_callback_invalid")

def test_entity3d_with_model():
    """Test Entity3D animation with a non-skeletal model"""
    entity = mcrfpy.Entity3D()
    cube = mcrfpy.Model3D.cube()

    entity.model = cube

    # Setting animation clip on non-skeletal model should not crash
    entity.anim_clip = "walk"  # Should just do nothing gracefully
    assert entity.anim_clip == "walk"  # The property is set even if model has no animation

    # Frame should be 0 since there's no skeleton
    assert entity.anim_frame == 0

    print("[PASS] test_entity3d_with_model")

def test_entity3d_animation_negative_speed():
    """Test that animation speed can be negative (reverse playback)"""
    entity = mcrfpy.Entity3D()

    entity.anim_speed = -1.0
    assert abs(entity.anim_speed - (-1.0)) < 0.001

    entity.anim_speed = 0.0
    assert entity.anim_speed == 0.0

    print("[PASS] test_entity3d_animation_negative_speed")

def run_all_tests():
    """Run all animation tests"""
    tests = [
        test_entity3d_animation_defaults,
        test_entity3d_animation_properties,
        test_entity3d_auto_animate,
        test_entity3d_animation_callback,
        test_entity3d_animation_callback_invalid,
        test_entity3d_with_model,
        test_entity3d_animation_negative_speed,
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
