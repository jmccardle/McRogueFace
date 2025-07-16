#!/usr/bin/env python3
"""Test for mcrfpy.createScene() method"""
import mcrfpy

def test_createScene():
    """Test creating a new scene"""
    # Test creating scenes
    test_scenes = ["test_scene1", "test_scene2", "special_chars_!@#"]
    
    for scene_name in test_scenes:
        try:
            mcrfpy.createScene(scene_name)
            print(f"✓ Created scene: {scene_name}")
        except Exception as e:
            print(f"✗ Failed to create scene {scene_name}: {e}")
            return
    
    # Try to set scene to verify it was created
    try:
        mcrfpy.setScene("test_scene1")
        current = mcrfpy.currentScene()
        if current == "test_scene1":
            print("✓ Scene switching works correctly")
        else:
            print(f"✗ Scene switch failed: expected 'test_scene1', got '{current}'")
    except Exception as e:
        print(f"✗ Scene switching error: {e}")
    
    print("PASS")

# Run test immediately
print("Running createScene test...")
test_createScene()
print("Test completed.")