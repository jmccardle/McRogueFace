#!/usr/bin/env python3
"""Test rotation support for UIDrawable subclasses"""
import mcrfpy
import sys

def test_rotation_properties():
    """Test rotation, origin, rotate_with_camera properties on all UIDrawable types"""
    print("Testing rotation properties on all UIDrawable types...")

    # Test UIFrame
    frame = mcrfpy.Frame(pos=(100, 100), size=(50, 50))
    assert frame.rotation == 0.0, f"Frame default rotation should be 0, got {frame.rotation}"
    frame.rotation = 45.0
    assert frame.rotation == 45.0, f"Frame rotation should be 45, got {frame.rotation}"

    # Test origin as Vector
    frame.origin = (25, 25)
    assert frame.origin.x == 25.0, f"Frame origin.x should be 25, got {frame.origin.x}"
    assert frame.origin.y == 25.0, f"Frame origin.y should be 25, got {frame.origin.y}"

    # Test rotate_with_camera
    assert frame.rotate_with_camera == False, "Default rotate_with_camera should be False"
    frame.rotate_with_camera = True
    assert frame.rotate_with_camera == True, "rotate_with_camera should be True after setting"
    print("  Frame: PASS")

    # Test UISprite
    sprite = mcrfpy.Sprite(pos=(100, 100))
    assert sprite.rotation == 0.0, f"Sprite default rotation should be 0, got {sprite.rotation}"
    sprite.rotation = 90.0
    assert sprite.rotation == 90.0, f"Sprite rotation should be 90, got {sprite.rotation}"
    sprite.origin = (8, 8)
    assert sprite.origin.x == 8.0, f"Sprite origin.x should be 8, got {sprite.origin.x}"
    print("  Sprite: PASS")

    # Test UICaption
    caption = mcrfpy.Caption(text="Test", pos=(100, 100))
    assert caption.rotation == 0.0, f"Caption default rotation should be 0, got {caption.rotation}"
    caption.rotation = -30.0
    assert caption.rotation == -30.0, f"Caption rotation should be -30, got {caption.rotation}"
    caption.origin = (0, 0)
    assert caption.origin.x == 0.0, f"Caption origin.x should be 0, got {caption.origin.x}"
    print("  Caption: PASS")

    # Test UICircle
    circle = mcrfpy.Circle(center=(100, 100), radius=25)
    assert circle.rotation == 0.0, f"Circle default rotation should be 0, got {circle.rotation}"
    circle.rotation = 180.0
    assert circle.rotation == 180.0, f"Circle rotation should be 180, got {circle.rotation}"
    print("  Circle: PASS")

    # Test UILine
    line = mcrfpy.Line(start=(0, 0), end=(100, 100))
    assert line.rotation == 0.0, f"Line default rotation should be 0, got {line.rotation}"
    line.rotation = 45.0
    assert line.rotation == 45.0, f"Line rotation should be 45, got {line.rotation}"
    print("  Line: PASS")

    # Test UIArc
    arc = mcrfpy.Arc(center=(100, 100), radius=50, start_angle=0, end_angle=90)
    assert arc.rotation == 0.0, f"Arc default rotation should be 0, got {arc.rotation}"
    arc.rotation = 270.0
    assert arc.rotation == 270.0, f"Arc rotation should be 270, got {arc.rotation}"
    print("  Arc: PASS")

    print("All rotation property tests passed!")
    return True

def test_rotation_animation():
    """Test that rotation can be animated"""
    print("\nTesting rotation animation...")

    frame = mcrfpy.Frame(pos=(100, 100), size=(50, 50))
    frame.rotation = 0.0

    # Test that animate method exists and accepts rotation
    try:
        frame.animate("rotation", 360.0, 1.0, mcrfpy.Easing.LINEAR)
        print("  Animation started successfully")
    except Exception as e:
        print(f"  Animation failed: {e}")
        return False

    # Test origin animation
    try:
        frame.animate("origin_x", 25.0, 0.5, mcrfpy.Easing.LINEAR)
        frame.animate("origin_y", 25.0, 0.5, mcrfpy.Easing.LINEAR)
        print("  Origin animation started successfully")
    except Exception as e:
        print(f"  Origin animation failed: {e}")
        return False

    print("Rotation animation tests passed!")
    return True

def test_grid_camera_rotation():
    """Test UIGrid camera_rotation property"""
    print("\nTesting Grid camera_rotation...")

    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(50, 50), size=(200, 200))

    # Test default camera_rotation
    assert grid.camera_rotation == 0.0, f"Grid default camera_rotation should be 0, got {grid.camera_rotation}"

    # Test setting camera_rotation
    grid.camera_rotation = 45.0
    assert grid.camera_rotation == 45.0, f"Grid camera_rotation should be 45, got {grid.camera_rotation}"

    # Test negative rotation
    grid.camera_rotation = -90.0
    assert grid.camera_rotation == -90.0, f"Grid camera_rotation should be -90, got {grid.camera_rotation}"

    # Test full rotation
    grid.camera_rotation = 360.0
    assert grid.camera_rotation == 360.0, f"Grid camera_rotation should be 360, got {grid.camera_rotation}"

    # Grid also has regular rotation (viewport rotation)
    assert grid.rotation == 0.0, f"Grid viewport rotation should default to 0, got {grid.rotation}"
    grid.rotation = 15.0
    assert grid.rotation == 15.0, f"Grid viewport rotation should be 15, got {grid.rotation}"

    # Test camera_rotation animation
    try:
        grid.animate("camera_rotation", 90.0, 1.0, mcrfpy.Easing.EASE_IN_OUT)
        print("  Camera rotation animation started successfully")
    except Exception as e:
        print(f"  Camera rotation animation failed: {e}")
        return False

    print("Grid camera_rotation tests passed!")
    return True

def run_all_tests():
    """Run all rotation tests"""
    print("=" * 50)
    print("UIDrawable Rotation Tests")
    print("=" * 50)

    results = []
    results.append(("Rotation Properties", test_rotation_properties()))
    results.append(("Rotation Animation", test_rotation_animation()))
    results.append(("Grid Camera Rotation", test_grid_camera_rotation()))

    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\nAll tests PASSED!")
        return 0
    else:
        print("\nSome tests FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
