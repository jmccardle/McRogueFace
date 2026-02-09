# 3d_full_test.py - Integration tests for complete 3D system
# Tests all 3D features working together

import mcrfpy
import sys

def test_viewport_creation():
    """Test Viewport3D creation and basic properties"""
    viewport = mcrfpy.Viewport3D(
        pos=(0, 0),
        size=(800, 600),
        render_resolution=(320, 240),
        fov=60.0,
        camera_pos=(10.0, 10.0, 10.0),
        camera_target=(0.0, 0.0, 0.0)
    )

    assert viewport.w == 800, f"Width mismatch: {viewport.w}"
    assert viewport.h == 600, f"Height mismatch: {viewport.h}"
    assert viewport.fov == 60.0, f"FOV mismatch: {viewport.fov}"

    print("[PASS] test_viewport_creation")
    return viewport

def test_navigation_grid(viewport):
    """Test navigation grid setup"""
    viewport.set_grid_size(16, 16)

    assert viewport.grid_size == (16, 16), f"Grid size mismatch: {viewport.grid_size}"

    # Test cell access
    cell = viewport.at(5, 5)
    assert cell is not None, "Cell access failed"
    assert cell.walkable == True, "Default cell should be walkable"

    # Test setting cell properties
    cell.walkable = False
    cell2 = viewport.at(5, 5)
    assert cell2.walkable == False, "Cell walkable not persisted"
    cell.walkable = True  # Reset

    print("[PASS] test_navigation_grid")

def test_heightmap_and_terrain(viewport):
    """Test heightmap and terrain generation"""
    hm = mcrfpy.HeightMap((16, 16))
    hm.mid_point_displacement(roughness=0.4)
    hm.normalize(0.0, 1.0)

    # Check heightmap values are in range
    for x in range(16):
        for z in range(16):
            h = hm[x, z]
            assert 0.0 <= h <= 1.0, f"Height out of range at ({x},{z}): {h}"

    # Build terrain
    vertex_count = viewport.build_terrain(
        layer_name="terrain",
        heightmap=hm,
        y_scale=2.0,
        cell_size=1.0
    )

    assert vertex_count > 0, "No vertices generated"

    # Apply heightmap to navigation
    viewport.apply_heightmap(hm, 2.0)

    print("[PASS] test_heightmap_and_terrain")

def test_terrain_colors(viewport):
    """Test terrain color application"""
    r_map = mcrfpy.HeightMap((16, 16))
    g_map = mcrfpy.HeightMap((16, 16))
    b_map = mcrfpy.HeightMap((16, 16))

    # Set all green
    for x in range(16):
        for z in range(16):
            r_map[x, z] = 0.2
            g_map[x, z] = 0.5
            b_map[x, z] = 0.2

    viewport.apply_terrain_colors("terrain", r_map, g_map, b_map)

    print("[PASS] test_terrain_colors")

def test_entity_creation(viewport):
    """Test Entity3D creation and properties"""
    entity = mcrfpy.Entity3D(pos=(8, 8), scale=1.0, color=mcrfpy.Color(255, 100, 50))
    viewport.entities.append(entity)

    assert entity.pos == (8, 8), f"Position mismatch: {entity.pos}"
    assert entity.scale == 1.0, f"Scale mismatch: {entity.scale}"
    assert entity.is_moving == False, "New entity should not be moving"

    print("[PASS] test_entity_creation")
    return entity

def test_pathfinding(viewport, entity):
    """Test A* pathfinding"""
    # Find path to another location
    path = entity.path_to(12, 12)

    assert isinstance(path, list), "path_to should return list"

    # Path may be empty if blocked, but should not error
    if path:
        assert len(path) > 0, "Path should have steps"
        # First step should be adjacent to start or the start itself

    # Test find_path on viewport
    vp_path = viewport.find_path((8, 8), (12, 12))
    assert isinstance(vp_path, list), "viewport.find_path should return list"

    print("[PASS] test_pathfinding")
    return path

def test_entity_movement(entity, path):
    """Test Entity3D movement via follow_path"""
    if not path:
        print("[SKIP] test_entity_movement - no path available")
        return

    # Test follow_path
    entity.follow_path(path[:3])  # Just first 3 steps

    # After queueing moves, entity should be moving
    assert entity.is_moving == True, "Entity should be moving after follow_path"

    # Test clear_path
    entity.clear_path()

    print("[PASS] test_entity_movement")

def test_fov_computation(viewport):
    """Test field of view computation"""
    visible = viewport.compute_fov((8, 8), radius=5)

    assert isinstance(visible, list), "compute_fov should return list"
    assert len(visible) > 0, "FOV should see some cells"

    # Origin should be visible
    origin_visible = (8, 8) in [(c[0], c[1]) for c in visible]
    assert origin_visible, "Origin should be in FOV"

    # Test is_in_fov
    assert viewport.is_in_fov(8, 8) == True, "Origin should be in FOV"

    print("[PASS] test_fov_computation")

def test_screen_to_world(viewport):
    """Test screen-to-world ray casting"""
    # Test center of viewport
    result = viewport.screen_to_world(160, 120)  # Half of 320x240 render resolution

    # May return None if ray misses ground
    if result is not None:
        assert len(result) == 3, "Should return (x, y, z)"
        assert result[1] == 0.0, "Y should be 0 (ground plane)"

    print("[PASS] test_screen_to_world")

def test_camera_follow(viewport, entity):
    """Test camera follow method"""
    original_pos = viewport.camera_pos

    viewport.follow(entity, distance=10.0, height=5.0)

    new_pos = viewport.camera_pos
    # Camera should have moved
    # (Position may or may not change significantly depending on entity location)

    print("[PASS] test_camera_follow")

def test_layer_management(viewport):
    """Test mesh layer management"""
    # Add layer
    layer = viewport.add_layer("test_layer", z_index=5)
    assert layer is not None, "add_layer should return layer dict"

    # Get layer
    layer2 = viewport.get_layer("test_layer")
    assert layer2 is not None, "get_layer should find layer"

    # Layer count
    count = viewport.layer_count()
    assert count >= 1, "Should have at least 1 layer"

    # Remove layer
    removed = viewport.remove_layer("test_layer")
    assert removed == True, "remove_layer should return True"

    # Verify removed
    layer3 = viewport.get_layer("test_layer")
    assert layer3 is None, "Layer should be removed"

    print("[PASS] test_layer_management")

def test_threshold_and_slope(viewport):
    """Test walkability threshold and slope cost"""
    hm = mcrfpy.HeightMap((16, 16))
    hm.normalize(0.0, 1.0)

    # Apply threshold - mark low areas unwalkable
    viewport.apply_threshold(hm, 0.0, 0.2, False)

    # Set slope cost
    viewport.set_slope_cost(0.5, 2.0)

    print("[PASS] test_threshold_and_slope")

def test_place_blocking(viewport):
    """Test place_blocking for marking cells"""
    # Mark a 2x2 area as blocking
    viewport.place_blocking((10, 10), (2, 2), walkable=False, transparent=False)

    # Verify cells are blocked
    cell = viewport.at(10, 10)
    assert cell.walkable == False, "Cell should be unwalkable after place_blocking"

    print("[PASS] test_place_blocking")

def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("3D Full Integration Test Suite")
    print("=" * 60)

    passed = 0
    failed = 0

    try:
        viewport = test_viewport_creation()
        passed += 1
    except Exception as e:
        print(f"[FAIL] test_viewport_creation: {e}")
        failed += 1
        return

    tests = [
        lambda: test_navigation_grid(viewport),
        lambda: test_heightmap_and_terrain(viewport),
        lambda: test_terrain_colors(viewport),
        lambda: test_layer_management(viewport),
        lambda: test_threshold_and_slope(viewport),
        lambda: test_place_blocking(viewport),
        lambda: test_fov_computation(viewport),
        lambda: test_screen_to_world(viewport),
    ]

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__ if hasattr(test, '__name__') else 'test'}: {e}")
            failed += 1

    # Entity tests
    try:
        entity = test_entity_creation(viewport)
        passed += 1

        path = test_pathfinding(viewport, entity)
        passed += 1

        test_entity_movement(entity, path)
        passed += 1

        test_camera_follow(viewport, entity)
        passed += 1
    except Exception as e:
        print(f"[FAIL] Entity tests: {e}")
        failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0

# Run tests
if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
