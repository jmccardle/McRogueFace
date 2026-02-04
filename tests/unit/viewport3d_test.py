# viewport3d_test.py - Unit test for Viewport3D 3D rendering viewport

import mcrfpy
import sys

def test_viewport3d_creation():
    """Test basic Viewport3D creation and default properties"""
    vp = mcrfpy.Viewport3D()

    # Default position
    assert vp.x == 0.0, f"Expected x=0, got {vp.x}"
    assert vp.y == 0.0, f"Expected y=0, got {vp.y}"

    # Default size (320x240 - PS1 resolution)
    assert vp.w == 320.0, f"Expected w=320, got {vp.w}"
    assert vp.h == 240.0, f"Expected h=240, got {vp.h}"

    # Default render resolution
    assert vp.render_resolution == (320, 240), f"Expected (320, 240), got {vp.render_resolution}"

    # Default camera position
    assert vp.camera_pos == (0.0, 0.0, 5.0), f"Expected (0, 0, 5), got {vp.camera_pos}"

    # Default camera target
    assert vp.camera_target == (0.0, 0.0, 0.0), f"Expected (0, 0, 0), got {vp.camera_target}"

    # Default FOV
    assert vp.fov == 60.0, f"Expected fov=60, got {vp.fov}"

    # Default PS1 effect flags
    assert vp.enable_vertex_snap == True, f"Expected vertex_snap=True, got {vp.enable_vertex_snap}"
    assert vp.enable_affine == True, f"Expected affine=True, got {vp.enable_affine}"
    assert vp.enable_dither == True, f"Expected dither=True, got {vp.enable_dither}"
    assert vp.enable_fog == True, f"Expected fog=True, got {vp.enable_fog}"

    # Default fog range
    assert vp.fog_near == 10.0, f"Expected fog_near=10, got {vp.fog_near}"
    assert vp.fog_far == 100.0, f"Expected fog_far=100, got {vp.fog_far}"

    print("[PASS] test_viewport3d_creation")

def test_viewport3d_with_kwargs():
    """Test Viewport3D creation with keyword arguments"""
    vp = mcrfpy.Viewport3D(
        pos=(100, 200),
        size=(640, 480),
        render_resolution=(160, 120),
        fov=90.0,
        camera_pos=(10.0, 5.0, 10.0),
        camera_target=(0.0, 2.0, 0.0),
        enable_vertex_snap=False,
        enable_affine=False,
        enable_dither=False,
        enable_fog=False,
        fog_near=5.0,
        fog_far=50.0
    )

    assert vp.x == 100.0, f"Expected x=100, got {vp.x}"
    assert vp.y == 200.0, f"Expected y=200, got {vp.y}"
    assert vp.w == 640.0, f"Expected w=640, got {vp.w}"
    assert vp.h == 480.0, f"Expected h=480, got {vp.h}"
    assert vp.render_resolution == (160, 120), f"Expected (160, 120), got {vp.render_resolution}"
    assert vp.fov == 90.0, f"Expected fov=90, got {vp.fov}"
    assert vp.camera_pos == (10.0, 5.0, 10.0), f"Expected (10, 5, 10), got {vp.camera_pos}"
    assert vp.camera_target == (0.0, 2.0, 0.0), f"Expected (0, 2, 0), got {vp.camera_target}"
    assert vp.enable_vertex_snap == False, f"Expected vertex_snap=False, got {vp.enable_vertex_snap}"
    assert vp.enable_affine == False, f"Expected affine=False, got {vp.enable_affine}"
    assert vp.enable_dither == False, f"Expected dither=False, got {vp.enable_dither}"
    assert vp.enable_fog == False, f"Expected fog=False, got {vp.enable_fog}"
    assert vp.fog_near == 5.0, f"Expected fog_near=5, got {vp.fog_near}"
    assert vp.fog_far == 50.0, f"Expected fog_far=50, got {vp.fog_far}"

    print("[PASS] test_viewport3d_with_kwargs")

def test_viewport3d_property_modification():
    """Test modifying Viewport3D properties after creation"""
    vp = mcrfpy.Viewport3D()

    # Modify position
    vp.x = 50
    vp.y = 75
    assert vp.x == 50.0, f"Expected x=50, got {vp.x}"
    assert vp.y == 75.0, f"Expected y=75, got {vp.y}"

    # Modify size
    vp.w = 800
    vp.h = 600
    assert vp.w == 800.0, f"Expected w=800, got {vp.w}"
    assert vp.h == 600.0, f"Expected h=600, got {vp.h}"

    # Modify render resolution
    vp.render_resolution = (256, 192)
    assert vp.render_resolution == (256, 192), f"Expected (256, 192), got {vp.render_resolution}"

    # Modify camera
    vp.camera_pos = (0.0, 10.0, 20.0)
    vp.camera_target = (5.0, 0.0, 5.0)
    vp.fov = 45.0
    assert vp.camera_pos == (0.0, 10.0, 20.0), f"Expected (0, 10, 20), got {vp.camera_pos}"
    assert vp.camera_target == (5.0, 0.0, 5.0), f"Expected (5, 0, 5), got {vp.camera_target}"
    assert vp.fov == 45.0, f"Expected fov=45, got {vp.fov}"

    # Modify PS1 effects
    vp.enable_vertex_snap = False
    vp.enable_affine = False
    vp.enable_dither = True
    vp.enable_fog = True
    assert vp.enable_vertex_snap == False
    assert vp.enable_affine == False
    assert vp.enable_dither == True
    assert vp.enable_fog == True

    # Modify fog range
    vp.fog_near = 1.0
    vp.fog_far = 200.0
    assert vp.fog_near == 1.0, f"Expected fog_near=1, got {vp.fog_near}"
    assert vp.fog_far == 200.0, f"Expected fog_far=200, got {vp.fog_far}"

    print("[PASS] test_viewport3d_property_modification")

def test_viewport3d_scene_integration():
    """Test adding Viewport3D to a scene"""
    scene = mcrfpy.Scene("viewport3d_test_scene")
    vp = mcrfpy.Viewport3D(pos=(10, 10), size=(400, 300))

    # Add to scene
    scene.children.append(vp)

    # Verify it was added
    assert len(scene.children) == 1, f"Expected 1 child, got {len(scene.children)}"

    # Retrieve and verify type
    child = scene.children[0]
    assert type(child).__name__ == "Viewport3D", f"Expected Viewport3D, got {type(child).__name__}"

    # Verify properties match
    assert child.x == 10.0
    assert child.y == 10.0
    assert child.w == 400.0
    assert child.h == 300.0

    print("[PASS] test_viewport3d_scene_integration")

def test_viewport3d_visibility():
    """Test visibility and opacity properties"""
    vp = mcrfpy.Viewport3D()

    # Default visibility
    assert vp.visible == True, f"Expected visible=True, got {vp.visible}"
    assert vp.opacity == 1.0, f"Expected opacity=1.0, got {vp.opacity}"

    # Modify visibility
    vp.visible = False
    assert vp.visible == False, f"Expected visible=False, got {vp.visible}"

    # Modify opacity
    vp.opacity = 0.5
    assert vp.opacity == 0.5, f"Expected opacity=0.5, got {vp.opacity}"

    # Opacity clamping
    vp.opacity = 2.0  # Should clamp to 1.0
    assert vp.opacity == 1.0, f"Expected opacity=1.0 after clamping, got {vp.opacity}"

    vp.opacity = -0.5  # Should clamp to 0.0
    assert vp.opacity == 0.0, f"Expected opacity=0.0 after clamping, got {vp.opacity}"

    print("[PASS] test_viewport3d_visibility")

def test_viewport3d_repr():
    """Test Viewport3D string representation"""
    vp = mcrfpy.Viewport3D(pos=(100, 200), size=(640, 480), render_resolution=(320, 240))
    repr_str = repr(vp)

    # Check that repr contains expected information
    assert "Viewport3D" in repr_str, f"Expected 'Viewport3D' in repr, got {repr_str}"
    assert "100" in repr_str, f"Expected x position in repr, got {repr_str}"
    assert "200" in repr_str, f"Expected y position in repr, got {repr_str}"

    print("[PASS] test_viewport3d_repr")

def run_all_tests():
    """Run all Viewport3D tests"""
    tests = [
        test_viewport3d_creation,
        test_viewport3d_with_kwargs,
        test_viewport3d_property_modification,
        test_viewport3d_scene_integration,
        test_viewport3d_visibility,
        test_viewport3d_repr,
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
