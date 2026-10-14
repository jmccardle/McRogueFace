"""VoxelGrid Core Demo (Milestone 9)

Demonstrates the VoxelGrid data structure without rendering.
This is a "console demo" that creates VoxelGrids, defines materials,
places voxel patterns, and displays statistics.

Note: Visual rendering comes in Milestone 10 (VoxelMeshing).
"""
import mcrfpy
from mcrfpy import Color

def format_bytes(bytes_val):
    """Format bytes as human-readable string"""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    else:
        return f"{bytes_val / (1024 * 1024):.1f} MB"

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_grid_stats(vg, name="VoxelGrid"):
    """Print statistics for a VoxelGrid"""
    print(f"\n  {name}:")
    print(f"    Dimensions: {vg.width} x {vg.height} x {vg.depth}")
    print(f"    Total voxels: {vg.width * vg.height * vg.depth:,}")
    print(f"    Cell size: {vg.cell_size} units")
    print(f"    Materials: {vg.material_count}")
    print(f"    Non-air voxels: {vg.count_non_air():,}")
    print(f"    Memory estimate: {format_bytes(vg.width * vg.height * vg.depth)}")
    print(f"    Offset: {vg.offset}")
    print(f"    Rotation: {vg.rotation} deg")

def demo_basic_creation():
    """Demonstrate basic VoxelGrid creation"""
    print_header("1. Basic VoxelGrid Creation")

    # Create various sizes
    small = mcrfpy.VoxelGrid(size=(8, 4, 8))
    medium = mcrfpy.VoxelGrid(size=(16, 8, 16), cell_size=1.0)
    large = mcrfpy.VoxelGrid(size=(32, 16, 32), cell_size=0.5)

    print_grid_stats(small, "Small (8x4x8)")
    print_grid_stats(medium, "Medium (16x8x16)")
    print_grid_stats(large, "Large (32x16x32, 0.5 cell size)")

def demo_material_palette():
    """Demonstrate material palette system"""
    print_header("2. Material Palette System")

    vg = mcrfpy.VoxelGrid(size=(16, 8, 16))

    # Define a palette of building materials
    materials = {}
    materials['stone'] = vg.add_material("stone", color=Color(128, 128, 128))
    materials['brick'] = vg.add_material("brick", color=Color(165, 42, 42))
    materials['wood'] = vg.add_material("wood", color=Color(139, 90, 43))
    materials['glass'] = vg.add_material("glass",
                                          color=Color(200, 220, 255, 128),
                                          transparent=True,
                                          path_cost=1.0)
    materials['metal'] = vg.add_material("metal",
                                          color=Color(180, 180, 190),
                                          path_cost=0.8)
    materials['grass'] = vg.add_material("grass", color=Color(60, 150, 60))

    print(f"\n  Defined {vg.material_count} materials:")
    print(f"    ID 0: air (implicit, always transparent)")

    for name, mat_id in materials.items():
        mat = vg.get_material(mat_id)
        c = mat['color']
        props = []
        if mat['transparent']:
            props.append("transparent")
        if mat['path_cost'] != 1.0:
            props.append(f"cost={mat['path_cost']}")
        props_str = f" ({', '.join(props)})" if props else ""
        print(f"    ID {mat_id}: {name} RGB({c.r},{c.g},{c.b},{c.a}){props_str}")

    return vg, materials

def demo_voxel_placement():
    """Demonstrate voxel placement patterns"""
    print_header("3. Voxel Placement Patterns")

    vg, materials = demo_material_palette()
    stone = materials['stone']
    brick = materials['brick']
    wood = materials['wood']

    # Pattern 1: Solid cube
    print("\n  Pattern: Solid 4x4x4 cube at origin")
    for z in range(4):
        for y in range(4):
            for x in range(4):
                vg.set(x, y, z, stone)
    print(f"    Placed {vg.count_material(stone)} stone voxels")

    # Pattern 2: Checkerboard floor
    print("\n  Pattern: Checkerboard floor at y=0, x=6-14, z=0-8")
    for z in range(8):
        for x in range(6, 14):
            mat = stone if (x + z) % 2 == 0 else brick
            vg.set(x, 0, z, mat)
    print(f"    Stone: {vg.count_material(stone)}, Brick: {vg.count_material(brick)}")

    # Pattern 3: Hollow cube (walls only)
    print("\n  Pattern: Hollow cube frame 4x4x4 at x=10, z=10")
    for x in range(4):
        for y in range(4):
            for z in range(4):
                # Only place on edges
                on_edge_x = (x == 0 or x == 3)
                on_edge_y = (y == 0 or y == 3)
                on_edge_z = (z == 0 or z == 3)
                if sum([on_edge_x, on_edge_y, on_edge_z]) >= 2:
                    vg.set(10 + x, y, 10 + z, wood)
    print(f"    Wood voxels: {vg.count_material(wood)}")

    print_grid_stats(vg, "After patterns")

    # Material breakdown
    print("\n  Material breakdown:")
    print(f"    Air:   {vg.count_material(0):,} ({100 * vg.count_material(0) / (16*8*16):.1f}%)")
    print(f"    Stone: {vg.count_material(stone):,}")
    print(f"    Brick: {vg.count_material(brick):,}")
    print(f"    Wood:  {vg.count_material(wood):,}")

def demo_bulk_operations():
    """Demonstrate bulk fill and clear operations"""
    print_header("4. Bulk Operations")

    vg = mcrfpy.VoxelGrid(size=(32, 8, 32))
    total = 32 * 8 * 32

    stone = vg.add_material("stone", color=Color(128, 128, 128))

    print(f"\n  Grid: 32x8x32 = {total:,} voxels")

    # Fill
    vg.fill(stone)
    print(f"  After fill(stone): {vg.count_non_air():,} non-air")

    # Clear
    vg.clear()
    print(f"  After clear(): {vg.count_non_air():,} non-air")

def demo_transforms():
    """Demonstrate transform properties"""
    print_header("5. Transform Properties")

    vg = mcrfpy.VoxelGrid(size=(8, 8, 8))

    print(f"\n  Default state:")
    print(f"    Offset: {vg.offset}")
    print(f"    Rotation: {vg.rotation} deg")

    # Position for a building
    vg.offset = (100.0, 0.0, 50.0)
    vg.rotation = 45.0

    print(f"\n  After positioning:")
    print(f"    Offset: {vg.offset}")
    print(f"    Rotation: {vg.rotation} deg")

    # Multiple buildings with different transforms
    print("\n  Example: Village layout with 3 buildings")
    buildings = []
    positions = [(0, 0, 0), (20, 0, 0), (10, 0, 15)]
    rotations = [0, 90, 45]

    for i, (pos, rot) in enumerate(zip(positions, rotations)):
        b = mcrfpy.VoxelGrid(size=(8, 6, 8))
        b.offset = pos
        b.rotation = rot
        buildings.append(b)
        print(f"    Building {i+1}: offset={pos}, rotation={rot} deg")

def demo_edge_cases():
    """Test edge cases and limits"""
    print_header("6. Edge Cases and Limits")

    # Maximum practical size
    print("\n  Testing large grid (64x64x64)...")
    large = mcrfpy.VoxelGrid(size=(64, 64, 64))
    mat = large.add_material("test", color=Color(128, 128, 128))
    large.fill(mat)
    print(f"    Created and filled: {large.count_non_air():,} voxels")
    large.clear()
    print(f"    Cleared: {large.count_non_air()} voxels")

    # Bounds checking
    print("\n  Bounds checking (should not crash):")
    small = mcrfpy.VoxelGrid(size=(4, 4, 4))
    test_mat = small.add_material("test", color=Color(255, 0, 0))
    small.set(-1, 0, 0, test_mat)
    small.set(100, 0, 0, test_mat)
    print(f"    Out-of-bounds get(-1,0,0): {small.get(-1, 0, 0)} (expected 0)")
    print(f"    Out-of-bounds get(100,0,0): {small.get(100, 0, 0)} (expected 0)")

    # Material palette capacity
    print("\n  Material palette capacity test:")
    full_vg = mcrfpy.VoxelGrid(size=(4, 4, 4))
    for i in range(255):
        full_vg.add_material(f"mat_{i}", color=Color(i, i, i))
    print(f"    Added 255 materials: count = {full_vg.material_count}")

    try:
        full_vg.add_material("overflow", color=Color(255, 255, 255))
        print("    ERROR: Should have raised exception!")
    except RuntimeError as e:
        print(f"    256th material correctly rejected: {e}")

def demo_memory_usage():
    """Show memory usage for various grid sizes"""
    print_header("7. Memory Usage Estimates")

    sizes = [
        (8, 8, 8),
        (16, 8, 16),
        (32, 16, 32),
        (64, 32, 64),
        (80, 16, 45),  # Example dungeon size
    ]

    print("\n  Size            Voxels      Memory")
    print("  " + "-" * 40)

    for w, h, d in sizes:
        voxels = w * h * d
        memory = voxels  # 1 byte per voxel
        print(f"  {w:3}x{h:3}x{d:3}  {voxels:>10,}  {format_bytes(memory):>10}")

def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("       VOXELGRID CORE DEMO (Milestone 9)")
    print("       Dense 3D Voxel Array with Material Palette")
    print("=" * 60)

    demo_basic_creation()
    demo_material_palette()
    demo_voxel_placement()
    demo_bulk_operations()
    demo_transforms()
    demo_edge_cases()
    demo_memory_usage()

    print_header("Demo Complete!")
    print("\n  Next milestone (10): Voxel Mesh Generation")
    print("  The VoxelGrid data will be converted to renderable 3D meshes.")
    print()

if __name__ == "__main__":
    import sys
    main()
    sys.exit(0)
