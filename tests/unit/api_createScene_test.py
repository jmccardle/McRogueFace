#!/usr/bin/env python3
"""Test for mcrfpy.Scene() creation and activation (formerly mcrfpy.createScene())"""
import mcrfpy
import sys

def test_createScene():
    """Test creating a new scene"""
    failures = []
    scenes = {}

    # Test creating scenes
    test_scenes = ["test_scene1", "test_scene2", "special_chars_!@#"]

    for scene_name in test_scenes:
        try:
            scenes[scene_name] = mcrfpy.Scene(scene_name)
            print(f"PASS: Created scene: {scene_name}")
        except Exception as e:
            print(f"FAIL: Failed to create scene {scene_name}: {e}")
            failures.append(f"create {scene_name}")
            continue

        if scenes[scene_name].name != scene_name:
            print(f"FAIL: scene.name mismatch: expected '{scene_name}', got '{scenes[scene_name].name}'")
            failures.append(f"name {scene_name}")

    # Activate a created scene to verify it exists and is switchable
    if "test_scene1" in scenes:
        try:
            scenes["test_scene1"].activate()
            current = (mcrfpy.current_scene.name if mcrfpy.current_scene else None)
            if current == "test_scene1":
                print("PASS: Scene switching works correctly")
            else:
                print(f"FAIL: Scene switch failed: expected 'test_scene1', got '{current}'")
                failures.append("activate()")
        except Exception as e:
            print(f"FAIL: Scene switching error: {e}")
            failures.append("activate()")

        # current_scene is also writable directly
        try:
            mcrfpy.current_scene = scenes["test_scene2"]
            current = (mcrfpy.current_scene.name if mcrfpy.current_scene else None)
            if current == "test_scene2":
                print("PASS: mcrfpy.current_scene assignment works correctly")
            else:
                print(f"FAIL: current_scene assignment failed: expected 'test_scene2', got '{current}'")
                failures.append("current_scene=")
        except Exception as e:
            print(f"FAIL: current_scene assignment error: {e}")
            failures.append("current_scene=")

    return failures

# Run test immediately
print("Running createScene test...")
failures = test_createScene()
print("Test completed.")

if failures:
    print("FAIL: " + ", ".join(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
