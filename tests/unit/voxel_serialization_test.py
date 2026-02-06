#!/usr/bin/env python3
"""Unit tests for Milestone 14: VoxelGrid Serialization

Tests save/load to file and to_bytes/from_bytes memory serialization.
"""

import mcrfpy
import sys
import os
import tempfile

# Test counters
tests_passed = 0
tests_failed = 0

def test(name, condition):
    """Simple test helper"""
    global tests_passed, tests_failed
    if condition:
        tests_passed += 1
        print(f"  PASS: {name}")
    else:
        tests_failed += 1
        print(f"  FAIL: {name}")

# =============================================================================
# Test basic save/load
# =============================================================================

print("\n=== Testing basic save/load ===")

# Create a test grid with materials and voxel data
vg = mcrfpy.VoxelGrid((8, 8, 8), cell_size=1.0)
stone = vg.add_material("stone", (128, 128, 128))
wood = vg.add_material("wood", (139, 90, 43), transparent=False, path_cost=0.8)
glass = vg.add_material("glass", (200, 220, 255, 128), transparent=True, path_cost=1.5)

# Fill with some patterns
vg.fill_box((0, 0, 0), (7, 0, 7), stone)  # Floor
vg.fill_box((0, 1, 0), (0, 3, 7), wood)   # Wall
vg.set(4, 1, 4, glass)  # Single glass block

original_non_air = vg.count_non_air()
original_stone = vg.count_material(stone)
original_wood = vg.count_material(wood)
original_glass = vg.count_material(glass)

print(f"  Original grid: {original_non_air} non-air voxels")
print(f"  Stone={original_stone}, Wood={original_wood}, Glass={original_glass}")

# Save to temp file
with tempfile.NamedTemporaryFile(suffix='.mcvg', delete=False) as f:
    temp_path = f.name

save_result = vg.save(temp_path)
test("save() returns True on success", save_result == True)
test("File was created", os.path.exists(temp_path))

file_size = os.path.getsize(temp_path)
print(f"  File size: {file_size} bytes")
test("File has non-zero size", file_size > 0)

# Create new grid and load
vg2 = mcrfpy.VoxelGrid((1, 1, 1))  # Start with tiny grid
load_result = vg2.load(temp_path)
test("load() returns True on success", load_result == True)

# Verify loaded data matches
test("Loaded size matches original", vg2.size == (8, 8, 8))
test("Loaded cell_size matches", vg2.cell_size == 1.0)
test("Loaded material_count matches", vg2.material_count == 3)
test("Loaded count_non_air matches", vg2.count_non_air() == original_non_air)
test("Loaded stone count matches", vg2.count_material(stone) == original_stone)
test("Loaded wood count matches", vg2.count_material(wood) == original_wood)
test("Loaded glass count matches", vg2.count_material(glass) == original_glass)

# Clean up temp file
os.unlink(temp_path)
test("Temp file cleaned up", not os.path.exists(temp_path))

# =============================================================================
# Test to_bytes/from_bytes
# =============================================================================

print("\n=== Testing to_bytes/from_bytes ===")

vg3 = mcrfpy.VoxelGrid((4, 4, 4), cell_size=2.0)
mat1 = vg3.add_material("test_mat", (255, 0, 0))
vg3.fill_box((1, 1, 1), (2, 2, 2), mat1)

original_bytes = vg3.to_bytes()
test("to_bytes() returns bytes", isinstance(original_bytes, bytes))
test("Bytes have content", len(original_bytes) > 0)

print(f"  Serialized to {len(original_bytes)} bytes")

# Load into new grid
vg4 = mcrfpy.VoxelGrid((1, 1, 1))
load_result = vg4.from_bytes(original_bytes)
test("from_bytes() returns True", load_result == True)
test("Bytes loaded - size matches", vg4.size == (4, 4, 4))
test("Bytes loaded - cell_size matches", vg4.cell_size == 2.0)
test("Bytes loaded - voxels match", vg4.count_non_air() == vg3.count_non_air())

# =============================================================================
# Test material preservation
# =============================================================================

print("\n=== Testing material preservation ===")

vg5 = mcrfpy.VoxelGrid((4, 4, 4))
mat_a = vg5.add_material("alpha", (10, 20, 30, 200), sprite_index=5, transparent=True, path_cost=0.5)
mat_b = vg5.add_material("beta", (100, 110, 120, 255), sprite_index=-1, transparent=False, path_cost=2.0)
vg5.set(0, 0, 0, mat_a)
vg5.set(1, 1, 1, mat_b)

data = vg5.to_bytes()
vg6 = mcrfpy.VoxelGrid((1, 1, 1))
vg6.from_bytes(data)

# Check first material
mat_a_loaded = vg6.get_material(1)
test("Material 1 name preserved", mat_a_loaded['name'] == "alpha")
test("Material 1 color R preserved", mat_a_loaded['color'].r == 10)
test("Material 1 color G preserved", mat_a_loaded['color'].g == 20)
test("Material 1 color B preserved", mat_a_loaded['color'].b == 30)
test("Material 1 color A preserved", mat_a_loaded['color'].a == 200)
test("Material 1 sprite_index preserved", mat_a_loaded['sprite_index'] == 5)
test("Material 1 transparent preserved", mat_a_loaded['transparent'] == True)
test("Material 1 path_cost preserved", abs(mat_a_loaded['path_cost'] - 0.5) < 0.001)

# Check second material
mat_b_loaded = vg6.get_material(2)
test("Material 2 name preserved", mat_b_loaded['name'] == "beta")
test("Material 2 transparent preserved", mat_b_loaded['transparent'] == False)
test("Material 2 path_cost preserved", abs(mat_b_loaded['path_cost'] - 2.0) < 0.001)

# =============================================================================
# Test voxel data integrity
# =============================================================================

print("\n=== Testing voxel data integrity ===")

vg7 = mcrfpy.VoxelGrid((16, 16, 16))
mat = vg7.add_material("checker", (255, 255, 255))

# Create checkerboard pattern
for z in range(16):
    for y in range(16):
        for x in range(16):
            if (x + y + z) % 2 == 0:
                vg7.set(x, y, z, mat)

original_count = vg7.count_non_air()
print(f"  Original checkerboard: {original_count} voxels")

# Save/load
data = vg7.to_bytes()
print(f"  Serialized size: {len(data)} bytes")

vg8 = mcrfpy.VoxelGrid((1, 1, 1))
vg8.from_bytes(data)

test("Checkerboard voxel count preserved", vg8.count_non_air() == original_count)

# Verify individual voxels
all_match = True
for z in range(16):
    for y in range(16):
        for x in range(16):
            expected = mat if (x + y + z) % 2 == 0 else 0
            actual = vg8.get(x, y, z)
            if actual != expected:
                all_match = False
                break
    if not all_match:
        break

test("All checkerboard voxels match", all_match)

# =============================================================================
# Test RLE compression effectiveness
# =============================================================================

print("\n=== Testing RLE compression ===")

# Test with uniform data (should compress well)
vg9 = mcrfpy.VoxelGrid((32, 32, 32))
mat_uniform = vg9.add_material("solid", (100, 100, 100))
vg9.fill(mat_uniform)

uniform_bytes = vg9.to_bytes()
raw_size = 32 * 32 * 32  # 32768 bytes uncompressed
compressed_size = len(uniform_bytes)
compression_ratio = raw_size / compressed_size if compressed_size > 0 else 0

print(f"  Uniform 32x32x32: raw={raw_size}, compressed={compressed_size}")
print(f"  Compression ratio: {compression_ratio:.1f}x")

test("Uniform data compresses significantly (>10x)", compression_ratio > 10)

# Test with alternating data (should compress poorly)
vg10 = mcrfpy.VoxelGrid((32, 32, 32))
mat_alt = vg10.add_material("alt", (200, 200, 200))

for z in range(32):
    for y in range(32):
        for x in range(32):
            if (x + y + z) % 2 == 0:
                vg10.set(x, y, z, mat_alt)

alt_bytes = vg10.to_bytes()
alt_ratio = raw_size / len(alt_bytes) if len(alt_bytes) > 0 else 0

print(f"  Alternating pattern: compressed={len(alt_bytes)}")
print(f"  Compression ratio: {alt_ratio:.1f}x")

# Alternating data should still compress somewhat due to row patterns
test("Alternating data serializes successfully", len(alt_bytes) > 0)

# =============================================================================
# Test error handling
# =============================================================================

print("\n=== Testing error handling ===")

vg_err = mcrfpy.VoxelGrid((2, 2, 2))

# Test load from non-existent file
load_fail = vg_err.load("/nonexistent/path/file.mcvg")
test("load() returns False for non-existent file", load_fail == False)

# Test from_bytes with invalid data
invalid_data = b"not valid mcvg data"
from_fail = vg_err.from_bytes(invalid_data)
test("from_bytes() returns False for invalid data", from_fail == False)

# Test from_bytes with truncated data
vg_good = mcrfpy.VoxelGrid((2, 2, 2))
good_data = vg_good.to_bytes()
truncated = good_data[:10]  # Take only first 10 bytes
from_truncated = vg_err.from_bytes(truncated)
test("from_bytes() returns False for truncated data", from_truncated == False)

# =============================================================================
# Test large grid
# =============================================================================

print("\n=== Testing large grid ===")

vg_large = mcrfpy.VoxelGrid((64, 32, 64))
mat_large = vg_large.add_material("large", (50, 50, 50))

# Fill floor and some walls
vg_large.fill_box((0, 0, 0), (63, 0, 63), mat_large)  # Floor
vg_large.fill_box((0, 1, 0), (0, 31, 63), mat_large)  # Wall

large_bytes = vg_large.to_bytes()
print(f"  64x32x64 grid: {len(large_bytes)} bytes")

vg_large2 = mcrfpy.VoxelGrid((1, 1, 1))
vg_large2.from_bytes(large_bytes)

test("Large grid size preserved", vg_large2.size == (64, 32, 64))
test("Large grid voxels preserved", vg_large2.count_non_air() == vg_large.count_non_air())

# =============================================================================
# Test round-trip with transform
# =============================================================================

print("\n=== Testing transform preservation (not serialized) ===")

# Note: Transform (offset, rotation) is NOT serialized - it's runtime state
vg_trans = mcrfpy.VoxelGrid((4, 4, 4))
vg_trans.offset = (10, 20, 30)
vg_trans.rotation = 45.0
mat_trans = vg_trans.add_material("trans", (128, 128, 128))
vg_trans.set(0, 0, 0, mat_trans)

data_trans = vg_trans.to_bytes()
vg_trans2 = mcrfpy.VoxelGrid((1, 1, 1))
vg_trans2.from_bytes(data_trans)

# Voxel data should be preserved
test("Voxel data preserved after load", vg_trans2.get(0, 0, 0) == mat_trans)

# Transform should be at default (not serialized)
test("Offset resets to default after load", vg_trans2.offset == (0, 0, 0))
test("Rotation resets to default after load", vg_trans2.rotation == 0.0)

# =============================================================================
# Summary
# =============================================================================

print(f"\n=== Results: {tests_passed} passed, {tests_failed} failed ===")

if tests_failed > 0:
    sys.exit(1)
else:
    print("All tests passed!")
    sys.exit(0)
