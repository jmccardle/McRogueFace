#!/usr/bin/env python3
"""Test for mcrfpy.current_scene (successor to setScene()/currentScene())"""
import mcrfpy
import sys

print("Starting current_scene test...")

# Create test scenes first
scenes = ["scene_A", "scene_B", "scene_C"]
scene_objs = {}
for scene in scenes:
    scene_objs[scene] = mcrfpy.Scene(scene)
    print(f"Created scene: {scene}")

results = []

# Test switching between scenes by name (mcrfpy.current_scene is read/write)
for scene in scenes:
    try:
        mcrfpy.current_scene = scene
        current = (mcrfpy.current_scene.name if mcrfpy.current_scene else None)
        if current == scene:
            results.append(f"[ok] current_scene set/get by name works for '{scene}'")
        else:
            results.append(f"[FAIL] Scene mismatch: set '{scene}', got '{current}'")
    except Exception as e:
        results.append(f"[FAIL] Error with scene '{scene}': {e}")

# Test switching by Scene object, and via Scene.activate()
for scene in scenes:
    try:
        mcrfpy.current_scene = scene_objs[scene]
        current = mcrfpy.current_scene
        if current.name == scene and current.active:
            results.append(f"[ok] current_scene set by Scene object works for '{scene}'")
        else:
            results.append(f"[FAIL] Object assign mismatch: set '{scene}', got '{current.name}'")
    except Exception as e:
        results.append(f"[FAIL] Error assigning Scene object '{scene}': {e}")

try:
    scene_objs["scene_B"].activate()
    if mcrfpy.current_scene.name == "scene_B":
        results.append("[ok] Scene.activate() switches the current scene")
    else:
        results.append(f"[FAIL] activate() left current scene at '{mcrfpy.current_scene.name}'")
except Exception as e:
    results.append(f"[FAIL] Error in Scene.activate(): {e}")

# Test invalid scene - it must not change the current scene.
# Current contract: assigning an unknown scene name raises KeyError and the
# current scene is left untouched (the old setScene() silently ignored it).
current_before = (mcrfpy.current_scene.name if mcrfpy.current_scene else None)
try:
    mcrfpy.current_scene = "nonexistent_scene"
    results.append("[FAIL] Assigning a nonexistent scene name did not raise")
except KeyError:
    results.append("[ok] Assigning a nonexistent scene name raises KeyError")
except Exception as e:
    results.append(f"[FAIL] Expected KeyError for nonexistent scene, got {type(e).__name__}: {e}")

current_after = (mcrfpy.current_scene.name if mcrfpy.current_scene else None)
if current_before == current_after:
    results.append(f"[ok] Failed switch leaves current scene alone (stayed on '{current_after}')")
else:
    results.append(f"[FAIL] Scene changed unexpectedly from '{current_before}' to '{current_after}'")

# Print results
for result in results:
    print(result)

# Determine pass/fail
if all("[ok]" in r for r in results):
    print("PASS")
    sys.exit(0)
else:
    print("FAIL")
    sys.exit(1)
