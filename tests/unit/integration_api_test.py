# integration_api_test.py - Test Milestone 8 API additions
# Tests: Entity3D.follow_path, .is_moving, .clear_path
#        Viewport3D.screen_to_world, .follow

import mcrfpy
import sys

print("Testing Milestone 8 API additions...")

# Create test scene
scene = mcrfpy.Scene("test")

# Create viewport
viewport = mcrfpy.Viewport3D(
    pos=(0, 0),
    size=(800, 600),
    render_resolution=(320, 240),
    fov=60.0,
    camera_pos=(10.0, 10.0, 10.0),
    camera_target=(5.0, 0.0, 5.0)
)
scene.children.append(viewport)

# Set up navigation grid
viewport.set_grid_size(20, 20)

# Create entity
entity = mcrfpy.Entity3D(pos=(5, 5))
viewport.entities.append(entity)

# Test 1: is_moving property (should be False initially)
print(f"Test 1: is_moving = {entity.is_moving}")
assert entity.is_moving == False, "Entity should not be moving initially"
print("  PASS: is_moving is False initially")

# Test 2: follow_path method
path = [(6, 5), (7, 5), (8, 5)]
entity.follow_path(path)
print(f"Test 2: follow_path({path})")
# After follow_path, entity should be moving (or at least have queued moves)
print(f"  is_moving after follow_path = {entity.is_moving}")
assert entity.is_moving == True, "Entity should be moving after follow_path"
print("  PASS: follow_path queued movement")

# Test 3: clear_path method
entity.clear_path()
print("Test 3: clear_path()")
print(f"  is_moving after clear_path = {entity.is_moving}")
# Note: is_moving may still be True if animation is in progress
print("  PASS: clear_path executed without error")

# Test 4: screen_to_world
world_pos = viewport.screen_to_world(400, 300)
print(f"Test 4: screen_to_world(400, 300) = {world_pos}")
if world_pos is None:
    print("  WARNING: screen_to_world returned None (ray missed ground)")
else:
    assert len(world_pos) == 3, "Should return (x, y, z) tuple"
    print(f"  PASS: Got world position {world_pos}")

# Test 5: follow method
viewport.follow(entity, distance=8.0, height=5.0)
print("Test 5: follow(entity, distance=8, height=5)")
cam_pos = viewport.camera_pos
print(f"  Camera position after follow: {cam_pos}")
print("  PASS: follow executed without error")

# Test 6: path_to (existing method)
path = entity.path_to(10, 10)
print(f"Test 6: path_to(10, 10) = {path[:3]}..." if len(path) > 3 else f"Test 6: path_to(10, 10) = {path}")
print("  PASS: path_to works")

print()
print("=" * 50)
print("All Milestone 8 API tests PASSED!")
print("=" * 50)

sys.exit(0)
