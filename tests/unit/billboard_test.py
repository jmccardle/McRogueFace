# billboard_test.py - Unit test for Billboard 3D camera-facing sprites

import mcrfpy
import sys

def test_billboard_creation():
    """Test basic Billboard creation and default properties"""
    bb = mcrfpy.Billboard()

    # Default sprite index
    assert bb.sprite_index == 0, f"Expected sprite_index=0, got {bb.sprite_index}"

    # Default position
    assert bb.pos == (0.0, 0.0, 0.0), f"Expected pos=(0,0,0), got {bb.pos}"

    # Default scale
    assert bb.scale == 1.0, f"Expected scale=1.0, got {bb.scale}"

    # Default facing mode
    assert bb.facing == "camera_y", f"Expected facing='camera_y', got {bb.facing}"

    # Default theta/phi (for fixed mode)
    assert bb.theta == 0.0, f"Expected theta=0.0, got {bb.theta}"
    assert bb.phi == 0.0, f"Expected phi=0.0, got {bb.phi}"

    # Default opacity and visibility
    assert bb.opacity == 1.0, f"Expected opacity=1.0, got {bb.opacity}"
    assert bb.visible == True, f"Expected visible=True, got {bb.visible}"

    print("[PASS] test_billboard_creation")

def test_billboard_with_kwargs():
    """Test Billboard creation with keyword arguments"""
    bb = mcrfpy.Billboard(
        sprite_index=5,
        pos=(10.0, 5.0, -3.0),
        scale=2.5,
        facing="camera",
        opacity=0.8
    )

    assert bb.sprite_index == 5, f"Expected sprite_index=5, got {bb.sprite_index}"
    assert bb.pos == (10.0, 5.0, -3.0), f"Expected pos=(10,5,-3), got {bb.pos}"
    assert bb.scale == 2.5, f"Expected scale=2.5, got {bb.scale}"
    assert bb.facing == "camera", f"Expected facing='camera', got {bb.facing}"
    assert abs(bb.opacity - 0.8) < 0.001, f"Expected opacity~=0.8, got {bb.opacity}"

    print("[PASS] test_billboard_with_kwargs")

def test_billboard_facing_modes():
    """Test all Billboard facing modes"""
    bb = mcrfpy.Billboard()

    # Test camera mode (full rotation to face camera)
    bb.facing = "camera"
    assert bb.facing == "camera", f"Expected facing='camera', got {bb.facing}"

    # Test camera_y mode (only Y-axis rotation, stays upright)
    bb.facing = "camera_y"
    assert bb.facing == "camera_y", f"Expected facing='camera_y', got {bb.facing}"

    # Test fixed mode (uses theta/phi angles)
    bb.facing = "fixed"
    assert bb.facing == "fixed", f"Expected facing='fixed', got {bb.facing}"

    print("[PASS] test_billboard_facing_modes")

def test_billboard_fixed_rotation():
    """Test fixed mode rotation angles (theta/phi)"""
    bb = mcrfpy.Billboard(facing="fixed")

    # Set theta (horizontal rotation)
    bb.theta = 1.5708  # ~90 degrees
    assert abs(bb.theta - 1.5708) < 0.001, f"Expected theta~=1.5708, got {bb.theta}"

    # Set phi (vertical tilt)
    bb.phi = 0.7854  # ~45 degrees
    assert abs(bb.phi - 0.7854) < 0.001, f"Expected phi~=0.7854, got {bb.phi}"

    print("[PASS] test_billboard_fixed_rotation")

def test_billboard_property_modification():
    """Test modifying Billboard properties after creation"""
    bb = mcrfpy.Billboard()

    # Modify position
    bb.pos = (5.0, 10.0, 15.0)
    assert bb.pos == (5.0, 10.0, 15.0), f"Expected pos=(5,10,15), got {bb.pos}"

    # Modify sprite index
    bb.sprite_index = 42
    assert bb.sprite_index == 42, f"Expected sprite_index=42, got {bb.sprite_index}"

    # Modify scale
    bb.scale = 0.5
    assert bb.scale == 0.5, f"Expected scale=0.5, got {bb.scale}"

    # Modify opacity
    bb.opacity = 0.25
    assert abs(bb.opacity - 0.25) < 0.001, f"Expected opacity~=0.25, got {bb.opacity}"

    # Modify visibility
    bb.visible = False
    assert bb.visible == False, f"Expected visible=False, got {bb.visible}"

    print("[PASS] test_billboard_property_modification")

def test_billboard_opacity_clamping():
    """Test that opacity is clamped to 0-1 range"""
    bb = mcrfpy.Billboard()

    # Test upper clamp
    bb.opacity = 2.0
    assert bb.opacity == 1.0, f"Expected opacity=1.0 after clamping, got {bb.opacity}"

    # Test lower clamp
    bb.opacity = -0.5
    assert bb.opacity == 0.0, f"Expected opacity=0.0 after clamping, got {bb.opacity}"

    print("[PASS] test_billboard_opacity_clamping")

def test_billboard_repr():
    """Test Billboard string representation"""
    bb = mcrfpy.Billboard(pos=(1.0, 2.0, 3.0), sprite_index=7, facing="camera")
    repr_str = repr(bb)

    # Check that repr contains expected information
    assert "Billboard" in repr_str, f"Expected 'Billboard' in repr, got {repr_str}"

    print("[PASS] test_billboard_repr")

def test_billboard_with_texture():
    """Test Billboard with texture assignment"""
    # Use default_texture which is always available
    tex = mcrfpy.default_texture
    bb = mcrfpy.Billboard(texture=tex, sprite_index=0)

    # Verify texture is assigned
    assert bb.texture is not None, "Expected texture to be assigned"
    assert bb.sprite_index == 0, f"Expected sprite_index=0, got {bb.sprite_index}"

    # Change sprite index
    bb.sprite_index = 10
    assert bb.sprite_index == 10, f"Expected sprite_index=10, got {bb.sprite_index}"

    # Test assigning texture via property
    bb2 = mcrfpy.Billboard()
    assert bb2.texture is None, "Expected no texture initially"
    bb2.texture = tex
    assert bb2.texture is not None, "Expected texture after assignment"

    # Test setting texture to None
    bb2.texture = None
    assert bb2.texture is None, "Expected None after clearing texture"

    print("[PASS] test_billboard_with_texture")

def test_viewport3d_billboard_methods():
    """Test Viewport3D billboard management methods"""
    vp = mcrfpy.Viewport3D()

    # Initial count should be 0
    assert vp.billboard_count() == 0, f"Expected 0, got {vp.billboard_count()}"

    # Add billboards
    bb1 = mcrfpy.Billboard(pos=(1, 0, 1), scale=1.0)
    vp.add_billboard(bb1)
    assert vp.billboard_count() == 1, f"Expected 1, got {vp.billboard_count()}"

    bb2 = mcrfpy.Billboard(pos=(2, 0, 2), scale=0.5)
    vp.add_billboard(bb2)
    assert vp.billboard_count() == 2, f"Expected 2, got {vp.billboard_count()}"

    # Get billboard by index
    retrieved = vp.get_billboard(0)
    assert retrieved.pos == (1.0, 0.0, 1.0), f"Expected (1,0,1), got {retrieved.pos}"

    # Modify retrieved billboard
    retrieved.pos = (5, 1, 5)
    assert retrieved.pos == (5.0, 1.0, 5.0), f"Expected (5,1,5), got {retrieved.pos}"

    # Clear all billboards
    vp.clear_billboards()
    assert vp.billboard_count() == 0, f"Expected 0 after clear, got {vp.billboard_count()}"

    print("[PASS] test_viewport3d_billboard_methods")

def test_viewport3d_billboard_index_bounds():
    """Test get_billboard index bounds checking"""
    vp = mcrfpy.Viewport3D()

    # Empty viewport - any index should fail
    try:
        vp.get_billboard(0)
        assert False, "Should have raised IndexError"
    except IndexError:
        pass

    # Add one billboard
    bb = mcrfpy.Billboard()
    vp.add_billboard(bb)

    # Index 0 should work
    vp.get_billboard(0)

    # Index 1 should fail
    try:
        vp.get_billboard(1)
        assert False, "Should have raised IndexError"
    except IndexError:
        pass

    # Negative index should fail
    try:
        vp.get_billboard(-1)
        assert False, "Should have raised IndexError"
    except IndexError:
        pass

    print("[PASS] test_viewport3d_billboard_index_bounds")

def run_all_tests():
    """Run all Billboard tests"""
    tests = [
        test_billboard_creation,
        test_billboard_with_kwargs,
        test_billboard_facing_modes,
        test_billboard_fixed_rotation,
        test_billboard_property_modification,
        test_billboard_opacity_clamping,
        test_billboard_repr,
        test_billboard_with_texture,
        test_viewport3d_billboard_methods,
        test_viewport3d_billboard_index_bounds,
    ]

    passed = 0
    failed = 0
    skipped = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            if "[SKIP]" in str(e):
                skipped += 1
            else:
                print(f"[ERROR] {test.__name__}: {e}")
                failed += 1

    print(f"\n=== Results: {passed} passed, {failed} failed, {skipped} skipped ===")
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
