#!/usr/bin/env python3
"""Unit tests for VoxelGrid (Milestone 9)

Tests the core VoxelGrid data structure:
- Creation with various sizes
- Per-voxel get/set operations
- Bounds checking behavior
- Material palette management
- Bulk operations (fill, clear)
- Transform properties (offset, rotation)
- Statistics (count_non_air, count_material)
"""
import sys

# Track test results
passed = 0
failed = 0

def test(name, condition, detail=""):
    """Record test result"""
    global passed, failed
    if condition:
        print(f"[PASS] {name}")
        passed += 1
    else:
        print(f"[FAIL] {name}" + (f" - {detail}" if detail else ""))
        failed += 1

def test_creation():
    """Test VoxelGrid creation with various parameters"""
    import mcrfpy

    # Basic creation
    vg = mcrfpy.VoxelGrid(size=(16, 8, 16))
    test("Creation: basic", vg is not None)
    test("Creation: width", vg.width == 16)
    test("Creation: height", vg.height == 8)
    test("Creation: depth", vg.depth == 16)
    test("Creation: default cell_size", vg.cell_size == 1.0)

    # With cell_size
    vg2 = mcrfpy.VoxelGrid(size=(10, 5, 10), cell_size=2.0)
    test("Creation: custom cell_size", vg2.cell_size == 2.0)

    # Size property
    test("Creation: size tuple", vg.size == (16, 8, 16))

    # Initial state
    test("Creation: initially empty", vg.count_non_air() == 0)
    test("Creation: no materials", vg.material_count == 0)

def test_invalid_creation():
    """Test that invalid parameters raise errors"""
    import mcrfpy

    errors_caught = 0

    try:
        vg = mcrfpy.VoxelGrid(size=(0, 8, 16))
    except ValueError:
        errors_caught += 1

    try:
        vg = mcrfpy.VoxelGrid(size=(16, -1, 16))
    except ValueError:
        errors_caught += 1

    try:
        vg = mcrfpy.VoxelGrid(size=(16, 8, 16), cell_size=-1.0)
    except ValueError:
        errors_caught += 1

    try:
        vg = mcrfpy.VoxelGrid(size=(16, 8))  # Missing dimension
    except (ValueError, TypeError):
        errors_caught += 1

    test("Invalid creation: catches errors", errors_caught == 4, f"caught {errors_caught}/4")

def test_get_set():
    """Test per-voxel get/set operations"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(16, 8, 16))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Initially all air
    test("Get/Set: initial value is air", vg.get(0, 0, 0) == 0)

    # Set and get
    vg.set(5, 3, 7, stone)
    test("Get/Set: set then get", vg.get(5, 3, 7) == stone)

    # Verify adjacent cells unaffected
    test("Get/Set: adjacent unaffected", vg.get(5, 3, 6) == 0)
    test("Get/Set: adjacent unaffected 2", vg.get(4, 3, 7) == 0)

    # Set back to air
    vg.set(5, 3, 7, 0)
    test("Get/Set: set to air", vg.get(5, 3, 7) == 0)

    # Multiple materials
    wood = vg.add_material("wood", color=mcrfpy.Color(139, 90, 43))
    vg.set(0, 0, 0, stone)
    vg.set(1, 0, 0, wood)
    vg.set(2, 0, 0, stone)
    test("Get/Set: multiple materials",
         vg.get(0, 0, 0) == stone and vg.get(1, 0, 0) == wood and vg.get(2, 0, 0) == stone)

def test_bounds():
    """Test bounds checking behavior"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(8, 4, 8))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Out of bounds get returns 0 (air)
    test("Bounds: negative x", vg.get(-1, 0, 0) == 0)
    test("Bounds: negative y", vg.get(0, -1, 0) == 0)
    test("Bounds: negative z", vg.get(0, 0, -1) == 0)
    test("Bounds: overflow x", vg.get(8, 0, 0) == 0)
    test("Bounds: overflow y", vg.get(0, 4, 0) == 0)
    test("Bounds: overflow z", vg.get(0, 0, 8) == 0)
    test("Bounds: large overflow", vg.get(100, 100, 100) == 0)

    # Out of bounds set is silently ignored (no crash)
    vg.set(-1, 0, 0, stone)  # Should not crash
    vg.set(100, 0, 0, stone)  # Should not crash
    test("Bounds: OOB set doesn't crash", True)

    # Corner cases - max valid indices
    vg.set(7, 3, 7, stone)
    test("Bounds: max valid index", vg.get(7, 3, 7) == stone)

def test_materials():
    """Test material palette management"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(8, 8, 8))

    # Add first material
    stone_id = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))
    test("Materials: first ID is 1", stone_id == 1)

    # Add with all properties
    glass_id = vg.add_material("glass",
                               color=mcrfpy.Color(200, 200, 255, 128),
                               sprite_index=5,
                               transparent=True,
                               path_cost=0.5)
    test("Materials: second ID is 2", glass_id == 2)

    # Verify material count
    test("Materials: count", vg.material_count == 2)

    # Get material and verify properties
    stone = vg.get_material(stone_id)
    test("Materials: name", stone["name"] == "stone")
    test("Materials: color type", hasattr(stone["color"], 'r'))
    test("Materials: default sprite_index", stone["sprite_index"] == -1)
    test("Materials: default transparent", stone["transparent"] == False)
    test("Materials: default path_cost", stone["path_cost"] == 1.0)

    glass = vg.get_material(glass_id)
    test("Materials: custom sprite_index", glass["sprite_index"] == 5)
    test("Materials: custom transparent", glass["transparent"] == True)
    test("Materials: custom path_cost", glass["path_cost"] == 0.5)

    # Air material (ID 0)
    air = vg.get_material(0)
    test("Materials: air name", air["name"] == "air")
    test("Materials: air transparent", air["transparent"] == True)

    # Invalid material ID returns air
    invalid = vg.get_material(255)
    test("Materials: invalid returns air", invalid["name"] == "air")

def test_fill_clear():
    """Test bulk fill and clear operations"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(10, 5, 10))
    total = 10 * 5 * 10  # 500

    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Fill with material
    vg.fill(stone)
    test("Fill: all cells filled", vg.count_non_air() == total)
    test("Fill: specific cell", vg.get(5, 2, 5) == stone)
    test("Fill: corner cell", vg.get(0, 0, 0) == stone)
    test("Fill: opposite corner", vg.get(9, 4, 9) == stone)

    # Clear (fill with air)
    vg.clear()
    test("Clear: all cells empty", vg.count_non_air() == 0)
    test("Clear: specific cell", vg.get(5, 2, 5) == 0)

def test_transform():
    """Test transform properties (offset, rotation)"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(8, 8, 8))

    # Default values
    test("Transform: default offset", vg.offset == (0.0, 0.0, 0.0))
    test("Transform: default rotation", vg.rotation == 0.0)

    # Set offset
    vg.offset = (10.5, -5.0, 20.0)
    offset = vg.offset
    test("Transform: set offset x", abs(offset[0] - 10.5) < 0.001)
    test("Transform: set offset y", abs(offset[1] - (-5.0)) < 0.001)
    test("Transform: set offset z", abs(offset[2] - 20.0) < 0.001)

    # Set rotation
    vg.rotation = 45.0
    test("Transform: set rotation", abs(vg.rotation - 45.0) < 0.001)

    # Negative rotation
    vg.rotation = -90.0
    test("Transform: negative rotation", abs(vg.rotation - (-90.0)) < 0.001)

    # Large rotation
    vg.rotation = 720.0
    test("Transform: large rotation", abs(vg.rotation - 720.0) < 0.001)

def test_statistics():
    """Test statistics methods"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(10, 10, 10))

    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))
    wood = vg.add_material("wood", color=mcrfpy.Color(139, 90, 43))

    # Initially empty
    test("Stats: initial non_air", vg.count_non_air() == 0)
    test("Stats: initial stone count", vg.count_material(stone) == 0)

    # Add some voxels
    for i in range(5):
        vg.set(i, 0, 0, stone)
    for i in range(3):
        vg.set(i, 1, 0, wood)

    test("Stats: non_air after setting", vg.count_non_air() == 8)
    test("Stats: stone count", vg.count_material(stone) == 5)
    test("Stats: wood count", vg.count_material(wood) == 3)
    test("Stats: air count", vg.count_material(0) == 10*10*10 - 8)

def test_repr():
    """Test string representation"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(16, 8, 16))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))
    vg.set(0, 0, 0, stone)

    repr_str = repr(vg)
    test("Repr: contains VoxelGrid", "VoxelGrid" in repr_str)
    test("Repr: contains dimensions", "16x8x16" in repr_str)
    test("Repr: contains materials", "materials=1" in repr_str)
    test("Repr: contains non_air", "non_air=1" in repr_str)

def test_large_grid():
    """Test with larger grid sizes"""
    import mcrfpy

    # 64x64x64 = 262144 voxels
    vg = mcrfpy.VoxelGrid(size=(64, 64, 64))
    test("Large: creation", vg is not None)
    test("Large: size", vg.size == (64, 64, 64))

    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Fill entire grid
    vg.fill(stone)
    expected = 64 * 64 * 64
    test("Large: fill count", vg.count_non_air() == expected, f"got {vg.count_non_air()}, expected {expected}")

    # Clear
    vg.clear()
    test("Large: clear", vg.count_non_air() == 0)

def test_material_limit():
    """Test material palette limit (255 max)"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(8, 8, 8))

    # Add many materials
    for i in range(255):
        mat_id = vg.add_material(f"mat_{i}", color=mcrfpy.Color(i, i, i))
        if mat_id != i + 1:
            test("Material limit: IDs sequential", False, f"expected {i+1}, got {mat_id}")
            return

    test("Material limit: 255 materials added", vg.material_count == 255)

    # 256th should fail
    try:
        vg.add_material("overflow", color=mcrfpy.Color(255, 255, 255))
        test("Material limit: overflow error", False, "should have raised exception")
    except RuntimeError:
        test("Material limit: overflow error", True)

def main():
    """Run all tests"""
    print("=" * 60)
    print("VoxelGrid Unit Tests (Milestone 9)")
    print("=" * 60)
    print()

    test_creation()
    print()
    test_invalid_creation()
    print()
    test_get_set()
    print()
    test_bounds()
    print()
    test_materials()
    print()
    test_fill_clear()
    print()
    test_transform()
    print()
    test_statistics()
    print()
    test_repr()
    print()
    test_large_grid()
    print()
    test_material_limit()
    print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
