#!/usr/bin/env python3
"""Test for mcrfpy.setScene() and currentScene() methods"""
import mcrfpy

print("Starting setScene/currentScene test...")

# Create test scenes first
scenes = ["scene_A", "scene_B", "scene_C"]
for scene in scenes:
    _scene = mcrfpy.Scene(scene)
    print(f"Created scene: {scene}")

results = []

# Test switching between scenes
for scene in scenes:
    try:
        mcrfpy.current_scene = scene
        current = (mcrfpy.current_scene.name if mcrfpy.current_scene else None)
        if current == scene:
            results.append(f"✓ setScene/currentScene works for '{scene}'")
        else:
            results.append(f"✗ Scene mismatch: set '{scene}', got '{current}'")
    except Exception as e:
        results.append(f"✗ Error with scene '{scene}': {e}")

# Test invalid scene - it should not change the current scene
current_before = (mcrfpy.current_scene.name if mcrfpy.current_scene else None)
nonexistent_scene.activate()  # Note: ensure scene was created
current_after = (mcrfpy.current_scene.name if mcrfpy.current_scene else None)
if current_before == current_after:
    results.append(f"✓ setScene correctly ignores nonexistent scene (stayed on '{current_after}')")
else:
    results.append(f"✗ Scene changed unexpectedly from '{current_before}' to '{current_after}'")

# Print results
for result in results:
    print(result)

# Determine pass/fail
if all("✓" in r for r in results):
    print("PASS")
else:
    print("FAIL")