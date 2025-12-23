#!/usr/bin/env python3
"""Test Scene properties (#118: Scene as Drawable)"""
import mcrfpy
import sys

# Create test scenes
mcrfpy.createScene("test_scene")

def test_scene_pos():
    """Test Scene pos property"""
    print("Testing scene pos property...")

    # Create a Scene subclass to test
    class TestScene(mcrfpy.Scene):
        def __init__(self, name):
            super().__init__(name)

    scene = TestScene("scene_pos_test")

    # Test initial position
    pos = scene.pos
    assert pos.x == 0.0, f"Initial pos.x should be 0.0, got {pos.x}"
    assert pos.y == 0.0, f"Initial pos.y should be 0.0, got {pos.y}"

    # Test setting position with tuple
    scene.pos = (100.0, 200.0)
    pos = scene.pos
    assert pos.x == 100.0, f"pos.x should be 100.0, got {pos.x}"
    assert pos.y == 200.0, f"pos.y should be 200.0, got {pos.y}"

    # Test setting position with Vector
    scene.pos = mcrfpy.Vector(50.0, 75.0)
    pos = scene.pos
    assert pos.x == 50.0, f"pos.x should be 50.0, got {pos.x}"
    assert pos.y == 75.0, f"pos.y should be 75.0, got {pos.y}"

    print("  - Scene pos property: PASS")

def test_scene_visible():
    """Test Scene visible property"""
    print("Testing scene visible property...")

    class TestScene(mcrfpy.Scene):
        def __init__(self, name):
            super().__init__(name)

    scene = TestScene("scene_vis_test")

    # Test initial visibility (should be True)
    assert scene.visible == True, f"Initial visible should be True, got {scene.visible}"

    # Test setting to False
    scene.visible = False
    assert scene.visible == False, f"visible should be False, got {scene.visible}"

    # Test setting back to True
    scene.visible = True
    assert scene.visible == True, f"visible should be True, got {scene.visible}"

    print("  - Scene visible property: PASS")

def test_scene_opacity():
    """Test Scene opacity property"""
    print("Testing scene opacity property...")

    class TestScene(mcrfpy.Scene):
        def __init__(self, name):
            super().__init__(name)

    scene = TestScene("scene_opa_test")

    # Test initial opacity (should be 1.0)
    assert abs(scene.opacity - 1.0) < 0.001, f"Initial opacity should be 1.0, got {scene.opacity}"

    # Test setting opacity
    scene.opacity = 0.5
    assert abs(scene.opacity - 0.5) < 0.001, f"opacity should be 0.5, got {scene.opacity}"

    # Test clamping to 0.0
    scene.opacity = -0.5
    assert scene.opacity >= 0.0, f"opacity should be clamped to >= 0.0, got {scene.opacity}"

    # Test clamping to 1.0
    scene.opacity = 1.5
    assert scene.opacity <= 1.0, f"opacity should be clamped to <= 1.0, got {scene.opacity}"

    print("  - Scene opacity property: PASS")

def test_scene_name():
    """Test Scene name property (read-only)"""
    print("Testing scene name property...")

    class TestScene(mcrfpy.Scene):
        def __init__(self, name):
            super().__init__(name)

    scene = TestScene("my_test_scene")

    # Test name
    assert scene.name == "my_test_scene", f"name should be 'my_test_scene', got {scene.name}"

    # Name should be read-only (trying to set should raise)
    try:
        scene.name = "other_name"
        print("  - Scene name should be read-only: FAIL")
        sys.exit(1)
    except AttributeError:
        pass  # Expected

    print("  - Scene name property: PASS")

def test_scene_active():
    """Test Scene active property"""
    print("Testing scene active property...")

    class TestScene(mcrfpy.Scene):
        def __init__(self, name):
            super().__init__(name)

    scene1 = TestScene("active_test_1")
    scene2 = TestScene("active_test_2")

    # Activate scene1
    scene1.activate()
    assert scene1.active == True, f"scene1.active should be True after activation"
    assert scene2.active == False, f"scene2.active should be False"

    # Activate scene2
    scene2.activate()
    assert scene1.active == False, f"scene1.active should be False after activating scene2"
    assert scene2.active == True, f"scene2.active should be True"

    print("  - Scene active property: PASS")

def test_scene_children():
    """Test Scene children property (#151)"""
    print("Testing scene children property...")

    class TestScene(mcrfpy.Scene):
        def __init__(self, name):
            super().__init__(name)

    scene = TestScene("ui_test_scene")

    # Get UI collection via children property
    ui = scene.children
    assert ui is not None, "children should return a collection"

    # Add some elements
    ui.append(mcrfpy.Frame(pos=(10, 20), size=(100, 100)))
    ui.append(mcrfpy.Caption(text="Test", pos=(50, 50)))

    # Verify length
    assert len(scene.children) == 2, f"children should have 2 elements, got {len(scene.children)}"

    print("  - Scene children property: PASS")

# Run all tests
if __name__ == "__main__":
    try:
        test_scene_pos()
        test_scene_visible()
        test_scene_opacity()
        test_scene_name()
        test_scene_active()
        test_scene_children()

        print("\n=== All Scene property tests passed! ===")
        sys.exit(0)
    except Exception as e:
        print(f"\nFAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
