# voxelpoint_test.py - Unit tests for VoxelPoint navigation grid
# Tests grid creation, cell access, and property modification

import mcrfpy
import sys

def test_grid_creation():
    """Test creating and sizing a navigation grid"""
    print("Testing navigation grid creation...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))

    # Initial grid should be 0x0
    assert viewport.grid_size == (0, 0), f"Expected (0, 0), got {viewport.grid_size}"

    # Set grid size via property
    viewport.grid_size = (10, 8)
    assert viewport.grid_size == (10, 8), f"Expected (10, 8), got {viewport.grid_size}"

    # Set grid size via method
    viewport.set_grid_size(20, 15)
    assert viewport.grid_size == (20, 15), f"Expected (20, 15), got {viewport.grid_size}"

    print("  PASS: Grid creation and sizing")


def test_voxelpoint_access():
    """Test accessing VoxelPoint cells"""
    print("Testing VoxelPoint access...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))
    viewport.grid_size = (10, 10)

    # Access a cell
    vp = viewport.at(5, 5)
    assert vp is not None, "at() returned None"

    # Check grid_pos
    assert vp.grid_pos == (5, 5), f"Expected grid_pos (5, 5), got {vp.grid_pos}"

    # Test bounds checking
    try:
        viewport.at(-1, 0)
        assert False, "Expected IndexError for negative coordinate"
    except IndexError:
        pass

    try:
        viewport.at(10, 5)  # Out of bounds (0-9 valid)
        assert False, "Expected IndexError for out of bounds"
    except IndexError:
        pass

    print("  PASS: VoxelPoint access")


def test_voxelpoint_properties():
    """Test VoxelPoint property read/write"""
    print("Testing VoxelPoint properties...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))
    viewport.grid_size = (10, 10)

    vp = viewport.at(3, 4)

    # Test default values
    assert vp.walkable == True, f"Default walkable should be True, got {vp.walkable}"
    assert vp.transparent == True, f"Default transparent should be True, got {vp.transparent}"
    assert vp.height == 0.0, f"Default height should be 0.0, got {vp.height}"
    assert vp.cost == 1.0, f"Default cost should be 1.0, got {vp.cost}"

    # Test setting bool properties
    vp.walkable = False
    assert vp.walkable == False, "walkable not set to False"

    vp.transparent = False
    assert vp.transparent == False, "transparent not set to False"

    # Test setting float properties
    vp.height = 5.5
    assert abs(vp.height - 5.5) < 0.01, f"height should be 5.5, got {vp.height}"

    vp.cost = 2.0
    assert abs(vp.cost - 2.0) < 0.01, f"cost should be 2.0, got {vp.cost}"

    # Test cost must be non-negative
    try:
        vp.cost = -1.0
        assert False, "Expected ValueError for negative cost"
    except ValueError:
        pass

    print("  PASS: VoxelPoint properties")


def test_voxelpoint_persistence():
    """Test that VoxelPoint changes persist in the grid"""
    print("Testing VoxelPoint persistence...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))
    viewport.grid_size = (10, 10)

    # Modify a cell
    vp = viewport.at(2, 3)
    vp.walkable = False
    vp.height = 10.0
    vp.cost = 3.5

    # Access the same cell again
    vp2 = viewport.at(2, 3)
    assert vp2.walkable == False, "walkable change did not persist"
    assert abs(vp2.height - 10.0) < 0.01, "height change did not persist"
    assert abs(vp2.cost - 3.5) < 0.01, "cost change did not persist"

    # Make sure other cells are unaffected
    vp3 = viewport.at(2, 4)
    assert vp3.walkable == True, "Adjacent cell was modified"
    assert vp3.height == 0.0, "Adjacent cell height was modified"

    print("  PASS: VoxelPoint persistence")


def test_cell_size_property():
    """Test cell_size property"""
    print("Testing cell_size property...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))

    # Default cell size should be 1.0
    assert abs(viewport.cell_size - 1.0) < 0.01, f"Default cell_size should be 1.0, got {viewport.cell_size}"

    # Set cell size
    viewport.cell_size = 2.5
    assert abs(viewport.cell_size - 2.5) < 0.01, f"cell_size should be 2.5, got {viewport.cell_size}"

    # cell_size must be positive
    try:
        viewport.cell_size = 0
        assert False, "Expected ValueError for zero cell_size"
    except ValueError:
        pass

    try:
        viewport.cell_size = -1.0
        assert False, "Expected ValueError for negative cell_size"
    except ValueError:
        pass

    print("  PASS: cell_size property")


def test_repr():
    """Test VoxelPoint __repr__"""
    print("Testing VoxelPoint repr...")

    viewport = mcrfpy.Viewport3D(pos=(0, 0), size=(320, 240))
    viewport.grid_size = (10, 10)

    vp = viewport.at(3, 7)
    r = repr(vp)
    assert "VoxelPoint" in r, f"repr should contain 'VoxelPoint', got {r}"
    assert "3, 7" in r, f"repr should contain '3, 7', got {r}"

    print("  PASS: VoxelPoint repr")


def run_all_tests():
    """Run all unit tests"""
    print("=" * 60)
    print("VoxelPoint Unit Tests")
    print("=" * 60)

    try:
        test_grid_creation()
        test_voxelpoint_access()
        test_voxelpoint_properties()
        test_voxelpoint_persistence()
        test_cell_size_property()
        test_repr()

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
