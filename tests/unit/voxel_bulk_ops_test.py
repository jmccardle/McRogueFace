#!/usr/bin/env python3
"""Unit tests for VoxelGrid bulk operations (Milestone 11)

Tests:
- fill_box_hollow: Verify shell only, interior empty
- fill_sphere: Volume roughly matches (4/3)πr³
- fill_cylinder: Volume roughly matches πr²h
- fill_noise: Higher threshold = fewer voxels
- copy_region/paste_region: Round-trip verification
- skip_air option for paste
"""
import sys
import math

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

def test_fill_box_hollow_basic():
    """fill_box_hollow creates correct shell"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(10, 10, 10))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Create hollow 6x6x6 box with thickness 1
    vg.fill_box_hollow((2, 2, 2), (7, 7, 7), stone, thickness=1)

    # Total box = 6x6x6 = 216
    # Interior = 4x4x4 = 64
    # Shell = 216 - 64 = 152
    expected = 152
    actual = vg.count_non_air()
    test("Hollow box: shell has correct voxel count", actual == expected,
         f"got {actual}, expected {expected}")

    # Verify interior is empty (center should be air)
    test("Hollow box: interior is air", vg.get(4, 4, 4) == 0)
    test("Hollow box: interior is air (another point)", vg.get(5, 5, 5) == 0)

    # Verify shell exists
    test("Hollow box: corner is filled", vg.get(2, 2, 2) == stone)
    test("Hollow box: edge is filled", vg.get(4, 2, 2) == stone)

def test_fill_box_hollow_thick():
    """fill_box_hollow with thickness > 1"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(12, 12, 12))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Create hollow 10x10x10 box with thickness 2
    vg.fill_box_hollow((1, 1, 1), (10, 10, 10), stone, thickness=2)

    # Total box = 10x10x10 = 1000
    # Interior = 6x6x6 = 216
    # Shell = 1000 - 216 = 784
    expected = 784
    actual = vg.count_non_air()
    test("Thick hollow box: correct voxel count", actual == expected,
         f"got {actual}, expected {expected}")

    # Verify interior is empty
    test("Thick hollow box: center is air", vg.get(5, 5, 5) == 0)

def test_fill_sphere_volume():
    """fill_sphere produces roughly spherical shape"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(30, 30, 30))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Fill sphere with radius 8
    radius = 8
    vg.fill_sphere((15, 15, 15), radius, stone)

    # Expected volume ≈ (4/3)πr³
    expected_vol = (4.0 / 3.0) * math.pi * (radius ** 3)
    actual = vg.count_non_air()

    # Voxel sphere should be within 20% of theoretical volume
    ratio = actual / expected_vol
    test("Sphere volume: within 20% of (4/3)πr³",
         0.8 <= ratio <= 1.2,
         f"got {actual}, expected ~{int(expected_vol)}, ratio={ratio:.2f}")

def test_fill_sphere_carve():
    """fill_sphere with material 0 carves out voxels"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(20, 20, 20))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Fill entire grid with stone
    vg.fill(stone)
    initial = vg.count_non_air()
    test("Sphere carve: initial fill", initial == 8000)  # 20x20x20

    # Carve out a sphere (material 0)
    vg.fill_sphere((10, 10, 10), 5, 0)  # Air

    final = vg.count_non_air()
    test("Sphere carve: voxels removed", final < initial)

def test_fill_cylinder_volume():
    """fill_cylinder produces roughly cylindrical shape"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(30, 30, 30))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Fill cylinder with radius 5, height 10
    radius = 5
    height = 10
    vg.fill_cylinder((15, 5, 15), radius, height, stone)

    # Expected volume ≈ πr²h
    expected_vol = math.pi * (radius ** 2) * height
    actual = vg.count_non_air()

    # Voxel cylinder should be within 20% of theoretical volume
    ratio = actual / expected_vol
    test("Cylinder volume: within 20% of πr²h",
         0.8 <= ratio <= 1.2,
         f"got {actual}, expected ~{int(expected_vol)}, ratio={ratio:.2f}")

def test_fill_cylinder_bounds():
    """fill_cylinder respects grid bounds"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(10, 10, 10))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Cylinder partially outside grid
    vg.fill_cylinder((2, 0, 2), 3, 15, stone)  # height extends beyond grid

    # Should not crash, and have some voxels
    count = vg.count_non_air()
    test("Cylinder bounds: handles out-of-bounds gracefully", count > 0)
    test("Cylinder bounds: limited by grid height", count < 3.14 * 9 * 15)

def test_fill_noise_threshold():
    """fill_noise: higher threshold = fewer voxels"""
    import mcrfpy

    vg1 = mcrfpy.VoxelGrid(size=(16, 16, 16))
    vg2 = mcrfpy.VoxelGrid(size=(16, 16, 16))
    stone = vg1.add_material("stone", color=mcrfpy.Color(128, 128, 128))
    vg2.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Same seed, different thresholds
    vg1.fill_noise((0, 0, 0), (15, 15, 15), stone, threshold=0.3, scale=0.15, seed=12345)
    vg2.fill_noise((0, 0, 0), (15, 15, 15), stone, threshold=0.7, scale=0.15, seed=12345)

    count1 = vg1.count_non_air()
    count2 = vg2.count_non_air()

    # Higher threshold should produce fewer voxels
    test("Noise threshold: high threshold produces fewer voxels",
         count2 < count1,
         f"threshold=0.3 gave {count1}, threshold=0.7 gave {count2}")

def test_fill_noise_seed():
    """fill_noise: same seed produces same result"""
    import mcrfpy

    vg1 = mcrfpy.VoxelGrid(size=(16, 16, 16))
    vg2 = mcrfpy.VoxelGrid(size=(16, 16, 16))
    stone = vg1.add_material("stone", color=mcrfpy.Color(128, 128, 128))
    vg2.add_material("stone", color=mcrfpy.Color(128, 128, 128))

    # Same parameters
    vg1.fill_noise((0, 0, 0), (15, 15, 15), stone, threshold=0.5, scale=0.1, seed=42)
    vg2.fill_noise((0, 0, 0), (15, 15, 15), stone, threshold=0.5, scale=0.1, seed=42)

    # Should produce identical results
    count1 = vg1.count_non_air()
    count2 = vg2.count_non_air()

    test("Noise seed: same seed produces same count", count1 == count2,
         f"got {count1} vs {count2}")

    # Check a few sample points
    same_values = True
    for x, y, z in [(0, 0, 0), (8, 8, 8), (15, 15, 15), (3, 7, 11)]:
        if vg1.get(x, y, z) != vg2.get(x, y, z):
            same_values = False
            break

    test("Noise seed: same seed produces identical voxels", same_values)

def test_copy_paste_basic():
    """copy_region and paste_region round-trip"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(20, 10, 20))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))
    brick = vg.add_material("brick", color=mcrfpy.Color(165, 42, 42))

    # Create a small structure
    vg.fill_box((2, 0, 2), (5, 3, 5), stone)
    vg.set(3, 1, 3, brick)  # Add a different material

    # Copy the region
    prefab = vg.copy_region((2, 0, 2), (5, 3, 5))

    # Verify VoxelRegion properties
    test("Copy region: correct width", prefab.width == 4)
    test("Copy region: correct height", prefab.height == 4)
    test("Copy region: correct depth", prefab.depth == 4)
    test("Copy region: size tuple", prefab.size == (4, 4, 4))

    # Paste elsewhere
    vg.paste_region(prefab, (10, 0, 10))

    # Verify paste
    test("Paste region: stone at corner", vg.get(10, 0, 10) == stone)
    test("Paste region: brick inside", vg.get(11, 1, 11) == brick)

def test_copy_paste_skip_air():
    """paste_region with skip_air=True doesn't overwrite"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(20, 10, 20))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))
    gold = vg.add_material("gold", color=mcrfpy.Color(255, 215, 0))

    # Create prefab with air gaps
    vg.fill_box((0, 0, 0), (3, 3, 3), stone)
    vg.set(1, 1, 1, 0)  # Air hole
    vg.set(2, 2, 2, 0)  # Another air hole

    # Copy it
    prefab = vg.copy_region((0, 0, 0), (3, 3, 3))

    # Place gold in destination
    vg.set(11, 1, 11, gold)  # Where air hole will paste
    vg.set(12, 2, 12, gold)  # Where another air hole will paste

    # Paste with skip_air=True (default)
    vg.paste_region(prefab, (10, 0, 10), skip_air=True)

    # Gold should still be there (air didn't overwrite)
    test("Skip air: preserves existing material", vg.get(11, 1, 11) == gold)
    test("Skip air: preserves at other location", vg.get(12, 2, 12) == gold)

def test_copy_paste_overwrite():
    """paste_region with skip_air=False overwrites"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(20, 10, 20))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))
    gold = vg.add_material("gold", color=mcrfpy.Color(255, 215, 0))

    # Create prefab with air gap
    vg.fill_box((0, 0, 0), (3, 3, 3), stone)
    vg.set(1, 1, 1, 0)  # Air hole

    # Copy it
    prefab = vg.copy_region((0, 0, 0), (3, 3, 3))

    # Clear and place gold in destination
    vg.clear()
    vg.set(11, 1, 11, gold)

    # Paste with skip_air=False
    vg.paste_region(prefab, (10, 0, 10), skip_air=False)

    # Gold should be overwritten with air
    test("Overwrite air: replaces existing material", vg.get(11, 1, 11) == 0)

def test_voxel_region_repr():
    """VoxelRegion has proper repr"""
    import mcrfpy

    vg = mcrfpy.VoxelGrid(size=(10, 10, 10))
    stone = vg.add_material("stone", color=mcrfpy.Color(128, 128, 128))
    vg.fill_box((0, 0, 0), (4, 4, 4), stone)

    prefab = vg.copy_region((0, 0, 0), (4, 4, 4))
    rep = repr(prefab)

    test("VoxelRegion repr: contains dimensions", "5x5x5" in rep)
    test("VoxelRegion repr: is VoxelRegion", "VoxelRegion" in rep)

def main():
    """Run all bulk operation tests"""
    print("=" * 60)
    print("VoxelGrid Bulk Operations Tests (Milestone 11)")
    print("=" * 60)
    print()

    test_fill_box_hollow_basic()
    print()
    test_fill_box_hollow_thick()
    print()
    test_fill_sphere_volume()
    print()
    test_fill_sphere_carve()
    print()
    test_fill_cylinder_volume()
    print()
    test_fill_cylinder_bounds()
    print()
    test_fill_noise_threshold()
    print()
    test_fill_noise_seed()
    print()
    test_copy_paste_basic()
    print()
    test_copy_paste_skip_air()
    print()
    test_copy_paste_overwrite()
    print()
    test_voxel_region_repr()
    print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
