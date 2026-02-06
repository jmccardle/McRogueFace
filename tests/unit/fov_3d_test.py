# fov_3d_test.py - Unit tests for 3D field of view
# Tests FOV computation on VoxelPoint navigation grid

import mcrfpy
import sys

def test_basic_fov():
    """Test basic FOV computation"""
    print("Testing basic FOV...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))
    viewport.grid_size = (20, 20)

    # Compute FOV from center
    visible = viewport.compute_fov((10, 10), radius=5)

    # Should have visible cells
    assert len(visible) > 0, "Expected visible cells"

    # Origin should be visible
    assert (10, 10) in visible, "Origin should be visible"

    # Cells within radius should be visible
    assert (10, 11) in visible, "(10, 11) should be visible"
    assert (11, 10) in visible, "(11, 10) should be visible"

    # Cells outside radius should not be visible
    assert (10, 20) not in visible, "(10, 20) should not be visible"
    assert (0, 0) not in visible, "(0, 0) should not be visible"

    print(f"  PASS: Basic FOV ({len(visible)} cells visible)")


def test_fov_with_walls():
    """Test FOV blocked by opaque cells"""
    print("Testing FOV with walls...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))
    viewport.grid_size = (20, 20)

    # Create a wall blocking line of sight
    # Wall at x=12
    for z in range(5, 16):
        viewport.at(12, z).transparent = False

    # Compute FOV from (10, 10)
    visible = viewport.compute_fov((10, 10), radius=10)

    # Origin should be visible
    assert (10, 10) in visible, "Origin should be visible"

    # Cells before wall should be visible
    assert (11, 10) in visible, "Cell before wall should be visible"

    # Wall cells themselves might be visible (at the edge)
    # But cells behind wall should NOT be visible
    # Note: Exact behavior depends on FOV algorithm

    # Cells well behind the wall should not be visible
    # (18, 10) is 6 cells behind the wall
    assert (18, 10) not in visible, "Cell behind wall should not be visible"

    print(f"  PASS: FOV with walls ({len(visible)} cells visible)")


def test_fov_radius():
    """Test FOV respects radius"""
    print("Testing FOV radius...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))
    viewport.grid_size = (30, 30)

    # Compute small FOV
    visible_small = viewport.compute_fov((15, 15), radius=3)

    # Compute larger FOV
    visible_large = viewport.compute_fov((15, 15), radius=8)

    # Larger radius should reveal more cells
    assert len(visible_large) > len(visible_small), \
        f"Larger radius should reveal more cells ({len(visible_large)} vs {len(visible_small)})"

    # Small FOV cells should be subset of large FOV
    for cell in visible_small:
        assert cell in visible_large, f"{cell} in small FOV but not in large FOV"

    print(f"  PASS: FOV radius (small={len(visible_small)}, large={len(visible_large)})")


def test_is_in_fov():
    """Test is_in_fov() method"""
    print("Testing is_in_fov...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))
    viewport.grid_size = (20, 20)

    # Compute FOV
    viewport.compute_fov((10, 10), radius=5)

    # Check is_in_fov matches compute_fov results
    assert viewport.is_in_fov(10, 10) == True, "Origin should be in FOV"
    assert viewport.is_in_fov(10, 11) == True, "Adjacent cell should be in FOV"
    assert viewport.is_in_fov(0, 0) == False, "Distant cell should not be in FOV"

    print("  PASS: is_in_fov method")


def test_fov_corner():
    """Test FOV from corner position"""
    print("Testing FOV from corner...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))
    viewport.grid_size = (20, 20)

    # Compute FOV from corner
    visible = viewport.compute_fov((0, 0), radius=5)

    # Origin should be visible
    assert (0, 0) in visible, "Origin should be visible"

    # Cells in direction of grid should be visible
    assert (1, 0) in visible, "(1, 0) should be visible"
    assert (0, 1) in visible, "(0, 1) should be visible"

    # Should handle edge of grid gracefully
    # Shouldn't crash or have negative coordinates

    print(f"  PASS: FOV from corner ({len(visible)} cells visible)")


def test_fov_empty_grid():
    """Test FOV on uninitialized grid"""
    print("Testing FOV on empty grid...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))

    # Grid size is 0x0 by default
    # Compute FOV should return empty list or handle gracefully
    visible = viewport.compute_fov((0, 0), radius=5)

    assert len(visible) == 0, "FOV on empty grid should return empty list"

    print("  PASS: FOV on empty grid")


def test_multiple_fov_calls():
    """Test that multiple FOV calls work correctly"""
    print("Testing multiple FOV calls...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))
    viewport.grid_size = (20, 20)

    # First FOV from (5, 5)
    visible1 = viewport.compute_fov((5, 5), radius=4)
    assert (5, 5) in visible1, "First origin should be visible"

    # Second FOV from (15, 15)
    visible2 = viewport.compute_fov((15, 15), radius=4)
    assert (15, 15) in visible2, "Second origin should be visible"

    # is_in_fov should reflect the LAST computed FOV
    assert viewport.is_in_fov(15, 15) == True, "Last origin should be in FOV"
    # Note: (5, 5) might not be in FOV anymore depending on radius

    print("  PASS: Multiple FOV calls")


def run_all_tests():
    """Run all unit tests"""
    print("=" * 60)
    print("3D FOV Unit Tests")
    print("=" * 60)

    try:
        test_basic_fov()
        test_fov_with_walls()
        test_fov_radius()
        test_is_in_fov()
        test_fov_corner()
        test_fov_empty_grid()
        test_multiple_fov_calls()

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
