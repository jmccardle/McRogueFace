#!/usr/bin/env python3
"""Test #151: Consistent Scene API - scene.children, scene.on_key, mcrfpy.current_scene, mcrfpy.scenes"""
import mcrfpy
import sys

print("Testing Issue #151 - Consistent Scene API")
print("=" * 50)

def test_scene_children():
    """Test scene.children property (replaces get_ui method)"""
    print("\n1. Testing scene.children property...")

    class TestScene(mcrfpy.Scene):
        def __init__(self, name):
            super().__init__(name)

    scene = TestScene("children_test")

    # Get children
    children = scene.children
    assert children is not None, "children should not be None"

    # Add elements via children
    frame = mcrfpy.Frame(pos=(10, 20), size=(100, 100))
    children.append(frame)

    caption = mcrfpy.Caption(text="Test", pos=(50, 50))
    children.append(caption)

    # Verify count
    assert len(scene.children) == 2, f"Expected 2 children, got {len(scene.children)}"

    print("   PASS - scene.children works correctly")
    return True

def test_scene_on_key():
    """Test scene.on_key property (replaces keypressScene and register_keyboard)"""
    print("\n2. Testing scene.on_key property...")

    class TestScene(mcrfpy.Scene):
        def __init__(self, name):
            super().__init__(name)

    scene = TestScene("on_key_test")
    scene.activate()

    # Initial state should be None
    # Note: might return None or the default empty callable
    initial = scene.on_key
    print(f"   Initial on_key value: {initial}")

    # Define a handler
    handler_called = [False]
    def test_handler(key, action):
        handler_called[0] = True
        print(f"   Handler called with key={key}, action={action}")

    # Set handler via property
    scene.on_key = test_handler

    # Get handler back
    retrieved = scene.on_key
    assert retrieved is not None, "on_key should return the handler"
    assert callable(retrieved), "on_key should be callable"

    # Clear handler
    scene.on_key = None
    cleared = scene.on_key
    assert cleared is None, f"on_key should be None after clearing, got {cleared}"

    print("   PASS - scene.on_key works correctly")
    return True

def test_current_scene_property():
    """Test mcrfpy.current_scene property"""
    print("\n3. Testing mcrfpy.current_scene property...")

    class TestScene(mcrfpy.Scene):
        def __init__(self, name):
            super().__init__(name)

    scene1 = TestScene("scene_prop_1")
    scene2 = TestScene("scene_prop_2")

    # Set via property
    mcrfpy.current_scene = scene1

    # Get via property
    current = mcrfpy.current_scene
    assert current is not None, "current_scene should not be None"
    assert current.name == "scene_prop_1", f"Expected scene_prop_1, got {current.name}"

    # Switch to scene2
    mcrfpy.current_scene = scene2
    current = mcrfpy.current_scene
    assert current.name == "scene_prop_2", f"Expected scene_prop_2, got {current.name}"

    # Also test setting by string name
    mcrfpy.current_scene = "scene_prop_1"
    current = mcrfpy.current_scene
    assert current.name == "scene_prop_1", f"Expected scene_prop_1 (set by string), got {current.name}"

    print("   PASS - mcrfpy.current_scene works correctly")
    return True

def test_scenes_collection():
    """Test mcrfpy.scenes collection"""
    print("\n4. Testing mcrfpy.scenes collection...")

    # Get current scenes tuple
    scenes = mcrfpy.scenes
    assert scenes is not None, "scenes should not be None"
    assert isinstance(scenes, tuple), f"scenes should be a tuple, got {type(scenes)}"

    print(f"   Found {len(scenes)} scenes: {[s.name for s in scenes]}")

    # All items should be Scene objects
    for scene in scenes:
        assert hasattr(scene, 'name'), f"Scene should have name attribute: {scene}"
        assert hasattr(scene, 'children'), f"Scene should have children attribute: {scene}"

    print("   PASS - mcrfpy.scenes works correctly")
    return True

def test_scenes_readonly():
    """Test that scenes is read-only"""
    print("\n5. Testing mcrfpy.scenes is read-only...")

    try:
        mcrfpy.scenes = ()
        print("   FAIL - should have raised AttributeError")
        return False
    except AttributeError as e:
        print(f"   Correctly raised AttributeError: {e}")
        print("   PASS - mcrfpy.scenes is read-only")
        return True

# Run all tests
if __name__ == "__main__":
    try:
        all_passed = True

        all_passed &= test_scene_children()
        all_passed &= test_scene_on_key()
        all_passed &= test_current_scene_property()
        all_passed &= test_scenes_collection()
        all_passed &= test_scenes_readonly()

        print("\n" + "=" * 50)
        if all_passed:
            print("ALL TESTS PASSED!")
            sys.exit(0)
        else:
            print("SOME TESTS FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\nFAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
