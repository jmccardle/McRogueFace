#!/usr/bin/env python3
"""Test for mcrfpy.setScene() and currentScene() methods"""
import mcrfpy

print("Starting setScene/currentScene test...")

# Create test scenes first
scenes = ["scene_A", "scene_B", "scene_C"]
for scene in scenes:
    mcrfpy.createScene(scene)
    print(f"Created scene: {scene}")

results = []

# Test switching between scenes
for scene in scenes:
    try:
        mcrfpy.setScene(scene)
        current = mcrfpy.currentScene()
        if current == scene:
            results.append(f"✓ setScene/currentScene works for '{scene}'")
        else:
            results.append(f"✗ Scene mismatch: set '{scene}', got '{current}'")
    except Exception as e:
        results.append(f"✗ Error with scene '{scene}': {e}")

# Test invalid scene - it should not change the current scene
current_before = mcrfpy.currentScene()
mcrfpy.setScene("nonexistent_scene")
current_after = mcrfpy.currentScene()
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