# meshlayer_test.py - Unit tests for MeshLayer terrain system
# Tests HeightMap to 3D mesh conversion via Viewport3D

import mcrfpy
import sys

def test_viewport3d_layer_creation():
    """Test that layers can be created and managed"""
    print("Testing Viewport3D layer creation...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))

    # Initial layer count should be 0
    assert viewport.layer_count() == 0, f"Expected 0 layers, got {viewport.layer_count()}"

    # Add a layer
    layer_info = viewport.add_layer("test_layer", z_index=5)
    assert layer_info is not None, "add_layer returned None"
    assert layer_info["name"] == "test_layer", f"Layer name mismatch: {layer_info['name']}"
    assert layer_info["z_index"] == 5, f"Z-index mismatch: {layer_info['z_index']}"

    # Layer count should be 1
    assert viewport.layer_count() == 1, f"Expected 1 layer, got {viewport.layer_count()}"

    # Get the layer
    retrieved = viewport.get_layer("test_layer")
    assert retrieved is not None, "get_layer returned None"
    assert retrieved["name"] == "test_layer"

    # Get non-existent layer
    missing = viewport.get_layer("nonexistent")
    assert missing is None, "Expected None for missing layer"

    # Remove the layer
    removed = viewport.remove_layer("test_layer")
    assert removed == True, "remove_layer should return True"
    assert viewport.layer_count() == 0, "Layer count should be 0 after removal"

    # Remove non-existent layer
    removed_again = viewport.remove_layer("test_layer")
    assert removed_again == False, "remove_layer should return False for missing layer"

    print("  PASS: Layer creation and management")

def test_terrain_from_heightmap():
    """Test building terrain mesh from HeightMap"""
    print("Testing terrain mesh from HeightMap...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))

    # Create a small heightmap
    hm = mcrfpy.HeightMap((10, 10))
    hm.fill(0.5)  # Flat terrain at 0.5 height

    # Build terrain
    vertex_count = viewport.build_terrain(
        layer_name="terrain",
        heightmap=hm,
        y_scale=2.0,
        cell_size=1.0
    )

    # Expected vertices: (10-1) x (10-1) quads x 2 triangles x 3 vertices = 9 * 9 * 6 = 486
    expected_verts = 9 * 9 * 6
    assert vertex_count == expected_verts, f"Expected {expected_verts} vertices, got {vertex_count}"

    # Verify layer exists
    layer = viewport.get_layer("terrain")
    assert layer is not None, "Terrain layer not found"
    assert layer["vertex_count"] == expected_verts

    print(f"  PASS: Built terrain with {vertex_count} vertices")

def test_heightmap_terrain_generation():
    """Test that HeightMap generation methods work with terrain"""
    print("Testing HeightMap generation methods...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))

    # Test midpoint displacement
    hm = mcrfpy.HeightMap((17, 17))  # Power of 2 + 1 for midpoint displacement
    hm.mid_point_displacement(0.5, seed=123)
    hm.normalize(0.0, 1.0)

    min_h, max_h = hm.min_max()
    assert min_h >= 0.0, f"Min height should be >= 0, got {min_h}"
    assert max_h <= 1.0, f"Max height should be <= 1, got {max_h}"

    vertex_count = viewport.build_terrain("terrain", hm, y_scale=5.0, cell_size=1.0)
    assert vertex_count > 0, "Should have vertices"

    print(f"  PASS: Midpoint displacement terrain with {vertex_count} vertices")

def test_orbit_camera():
    """Test camera orbit helper"""
    print("Testing camera orbit...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))

    # Test orbit at different angles
    import math

    viewport.orbit_camera(angle=0, distance=10, height=5)
    pos = viewport.camera_pos
    assert abs(pos[0] - 10.0) < 0.01, f"X should be 10 at angle=0, got {pos[0]}"
    assert abs(pos[1] - 5.0) < 0.01, f"Y (height) should be 5, got {pos[1]}"
    assert abs(pos[2]) < 0.01, f"Z should be 0 at angle=0, got {pos[2]}"

    viewport.orbit_camera(angle=math.pi/2, distance=10, height=5)
    pos = viewport.camera_pos
    assert abs(pos[0]) < 0.01, f"X should be 0 at angle=pi/2, got {pos[0]}"
    assert abs(pos[2] - 10.0) < 0.01, f"Z should be 10 at angle=pi/2, got {pos[2]}"

    print("  PASS: Camera orbit positioning")

def test_large_terrain():
    """Test larger terrain (performance check)"""
    print("Testing larger terrain mesh...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))

    # 80x45 is mentioned in the milestone doc
    hm = mcrfpy.HeightMap((80, 45))
    hm.mid_point_displacement(0.5, seed=999)
    hm.normalize(0.0, 1.0)

    vertex_count = viewport.build_terrain("large_terrain", hm, y_scale=4.0, cell_size=1.0)

    # Expected: 79 * 44 * 6 = 20,856 vertices
    expected = 79 * 44 * 6
    assert vertex_count == expected, f"Expected {expected} vertices, got {vertex_count}"

    print(f"  PASS: Large terrain ({80}x{45} heightmap) with {vertex_count} vertices")

def test_terrain_color_map():
    """Test applying RGB color maps to terrain"""
    print("Testing terrain color map...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))

    # Create small terrain
    hm = mcrfpy.HeightMap((10, 10))
    hm.fill(0.5)
    viewport.build_terrain("colored_terrain", hm, y_scale=2.0, cell_size=1.0)

    # Create RGB color maps
    r_map = mcrfpy.HeightMap((10, 10))
    g_map = mcrfpy.HeightMap((10, 10))
    b_map = mcrfpy.HeightMap((10, 10))

    # Fill with test colors (red terrain)
    r_map.fill(1.0)
    g_map.fill(0.0)
    b_map.fill(0.0)

    # Apply colors - should not raise
    viewport.apply_terrain_colors("colored_terrain", r_map, g_map, b_map)

    # Test with mismatched dimensions (should fail silently or raise)
    wrong_size = mcrfpy.HeightMap((5, 5))
    wrong_size.fill(0.5)
    # This should not crash, just do nothing due to dimension mismatch
    viewport.apply_terrain_colors("colored_terrain", wrong_size, wrong_size, wrong_size)

    # Test with non-existent layer
    try:
        viewport.apply_terrain_colors("nonexistent", r_map, g_map, b_map)
        assert False, "Should have raised ValueError for non-existent layer"
    except ValueError:
        pass  # Expected

    print("  PASS: Terrain color map application")

def run_all_tests():
    """Run all unit tests"""
    print("=" * 60)
    print("MeshLayer Unit Tests")
    print("=" * 60)

    try:
        test_viewport3d_layer_creation()
        test_terrain_from_heightmap()
        test_heightmap_terrain_generation()
        test_orbit_camera()
        test_large_terrain()
        test_terrain_color_map()

        print("=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)
        sys.exit(0)
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Run tests
run_all_tests()
