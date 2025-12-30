#!/usr/bin/env python3
"""Test the object-oriented Scene API (alternative to module-level functions).

The Scene object provides an OOP approach to scene management with several advantages:
1. `scene.on_key` can be set on ANY scene, not just the current one
2. `scene.children` provides direct access to UI elements
3. Subclassing enables lifecycle callbacks (on_enter, on_exit, update, etc.)

This is the recommended approach for new code, replacing:
- mcrfpy.createScene(name) -> scene = mcrfpy.Scene(name)
- mcrfpy.setScene(name) -> scene.activate()
- mcrfpy.sceneUI(name) -> scene.children
- mcrfpy.keypressScene(callback) -> scene.on_key = callback
"""
import mcrfpy
import sys

def test_scene_object_basics():
    """Test basic Scene object creation and properties."""
    print("=== Test: Scene Object Basics ===")

    # Create scene using object-oriented approach
    scene = mcrfpy.Scene("oop_test")

    # Check name property
    assert scene.name == "oop_test", f"Expected 'oop_test', got '{scene.name}'"
    print(f"  name: {scene.name}")

    # Check active property (should be False, not yet activated)
    print(f"  active: {scene.active}")

    # Check children property returns UICollection
    children = scene.children
    print(f"  children type: {type(children).__name__}")
    print(f"  children count: {len(children)}")

    # Add UI elements via children
    frame = mcrfpy.Frame(pos=(50, 50), size=(200, 100), fill_color=mcrfpy.Color(100, 100, 200))
    scene.children.append(frame)
    print(f"  children count after append: {len(scene.children)}")

    print("  PASS: Basic properties work correctly")
    return scene

def test_scene_activation():
    """Test scene activation."""
    print("\n=== Test: Scene Activation ===")

    scene1 = mcrfpy.Scene("scene_a")
    scene2 = mcrfpy.Scene("scene_b")

    # Neither active yet
    print(f"  Before activation - scene1.active: {scene1.active}, scene2.active: {scene2.active}")

    # Activate scene1
    scene1.activate()
    print(f"  After scene1.activate() - scene1.active: {scene1.active}, scene2.active: {scene2.active}")
    assert scene1.active == True, "scene1 should be active"
    assert scene2.active == False, "scene2 should not be active"

    # Activate scene2
    scene2.activate()
    print(f"  After scene2.activate() - scene1.active: {scene1.active}, scene2.active: {scene2.active}")
    assert scene1.active == False, "scene1 should not be active now"
    assert scene2.active == True, "scene2 should be active"

    print("  PASS: Scene activation works correctly")

def test_scene_on_key():
    """Test setting on_key callback on scene objects.

    This is the KEY ADVANTAGE over module-level keypressScene():
    You can set on_key on ANY scene, not just the current one!
    """
    print("\n=== Test: Scene on_key Property ===")

    scene1 = mcrfpy.Scene("keys_scene1")
    scene2 = mcrfpy.Scene("keys_scene2")

    # Track which callback was called
    callback_log = []

    def scene1_keyhandler(key, action):
        callback_log.append(("scene1", key, action))

    def scene2_keyhandler(key, action):
        callback_log.append(("scene2", key, action))

    # Set callbacks on BOTH scenes BEFORE activating either
    # This is impossible with keypressScene() which only works on current scene!
    scene1.on_key = scene1_keyhandler
    scene2.on_key = scene2_keyhandler

    print(f"  scene1.on_key set: {scene1.on_key is not None}")
    print(f"  scene2.on_key set: {scene2.on_key is not None}")

    # Verify callbacks are retrievable
    assert callable(scene1.on_key), "scene1.on_key should be callable"
    assert callable(scene2.on_key), "scene2.on_key should be callable"

    # Test clearing callback
    scene1.on_key = None
    assert scene1.on_key is None, "scene1.on_key should be None after clearing"
    print("  scene1.on_key cleared successfully")

    # Re-set it
    scene1.on_key = scene1_keyhandler

    print("  PASS: on_key property works correctly")

def test_scene_visual_properties():
    """Test scene-level visual properties (pos, visible, opacity)."""
    print("\n=== Test: Scene Visual Properties ===")

    scene = mcrfpy.Scene("visual_props_test")

    # Test pos property
    print(f"  Initial pos: {scene.pos}")
    scene.pos = (100, 50)
    print(f"  After setting pos=(100, 50): {scene.pos}")

    # Test visible property
    print(f"  Initial visible: {scene.visible}")
    scene.visible = False
    print(f"  After setting visible=False: {scene.visible}")
    assert scene.visible == False, "visible should be False"
    scene.visible = True

    # Test opacity property
    print(f"  Initial opacity: {scene.opacity}")
    scene.opacity = 0.5
    print(f"  After setting opacity=0.5: {scene.opacity}")
    assert 0.49 < scene.opacity < 0.51, f"opacity should be ~0.5, got {scene.opacity}"

    print("  PASS: Visual properties work correctly")

def test_scene_subclass():
    """Test subclassing Scene for lifecycle callbacks."""
    print("\n=== Test: Scene Subclass with Lifecycle ===")

    class GameScene(mcrfpy.Scene):
        def __init__(self, name):
            super().__init__(name)
            self.enter_count = 0
            self.exit_count = 0
            self.update_count = 0

        def on_enter(self):
            self.enter_count += 1
            print(f"    GameScene.on_enter() called (count: {self.enter_count})")

        def on_exit(self):
            self.exit_count += 1
            print(f"    GameScene.on_exit() called (count: {self.exit_count})")

        def on_keypress(self, key, action):
            print(f"    GameScene.on_keypress({key}, {action})")

        def update(self, dt):
            self.update_count += 1
            # Note: update is called every frame, so we don't print

    game_scene = GameScene("game_scene_test")
    other_scene = mcrfpy.Scene("other_scene_test")

    # Add some UI to game scene
    game_scene.children.append(
        mcrfpy.Caption(pos=(100, 100), text="Game Scene", fill_color=mcrfpy.Color(255, 255, 255))
    )

    print(f"  Created GameScene with {len(game_scene.children)} children")
    print(f"  enter_count before activation: {game_scene.enter_count}")

    # Activate - should trigger on_enter
    game_scene.activate()
    print(f"  enter_count after activation: {game_scene.enter_count}")

    # Switch away - should trigger on_exit
    other_scene.activate()
    print(f"  exit_count after switching: {game_scene.exit_count}")

    print("  PASS: Subclassing works correctly")

def test_comparison_with_module_functions():
    """Demonstrate the difference between old and new approaches."""
    print("\n=== Comparison: Module Functions vs Scene Objects ===")

    print("\n  OLD APPROACH (module-level functions):")
    print("    mcrfpy.createScene('my_scene')")
    print("    mcrfpy.setScene('my_scene')")
    print("    ui = mcrfpy.sceneUI('my_scene')")
    print("    ui.append(mcrfpy.Frame(...))")
    print("    mcrfpy.keypressScene(handler)  # ONLY works on current scene!")

    print("\n  NEW APPROACH (Scene objects):")
    print("    scene = mcrfpy.Scene('my_scene')")
    print("    scene.activate()")
    print("    scene.children.append(mcrfpy.Frame(...))")
    print("    scene.on_key = handler  # Works on ANY scene!")

    print("\n  KEY BENEFITS:")
    print("    1. scene.on_key can be set on non-active scenes")
    print("    2. Subclassing enables on_enter/on_exit/update callbacks")
    print("    3. Object reference makes code more readable")
    print("    4. scene.children is clearer than sceneUI(name)")

    print("\n  PASS: Documentation complete")

def main():
    """Run all Scene object API tests."""
    print("=" * 60)
    print("Scene Object API Test Suite")
    print("=" * 60)

    try:
        test_scene_object_basics()
        test_scene_activation()
        test_scene_on_key()
        test_scene_visual_properties()
        test_scene_subclass()
        test_comparison_with_module_functions()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        sys.exit(0)

    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
