"""Voxel Serialization Demo - Milestone 14

Demonstrates save/load functionality for VoxelGrid, including:
- Saving to file with .mcvg format
- Loading from file
- Serialization to bytes (for network/custom storage)
- RLE compression effectiveness
"""

import mcrfpy
import os
import tempfile

def create_demo_scene():
    """Create a scene demonstrating voxel serialization."""
    scene = mcrfpy.Scene("voxel_serialization_demo")
    ui = scene.children

    # Dark background
    bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=(20, 20, 30))
    ui.append(bg)

    # Title
    title = mcrfpy.Caption(text="Milestone 14: VoxelGrid Serialization",
                           pos=(30, 20))
    title.font_size = 28
    title.fill_color = (255, 220, 100)
    ui.append(title)

    # Create demo VoxelGrid with interesting structure
    grid = mcrfpy.VoxelGrid((16, 16, 16), cell_size=1.0)

    # Add materials
    stone = grid.add_material("stone", (100, 100, 110))
    wood = grid.add_material("wood", (139, 90, 43))
    glass = grid.add_material("glass", (180, 200, 220, 100), transparent=True)
    gold = grid.add_material("gold", (255, 215, 0))

    # Build a small structure
    grid.fill_box((0, 0, 0), (15, 0, 15), stone)  # Floor
    grid.fill_box((0, 1, 0), (0, 4, 15), stone)   # Wall 1
    grid.fill_box((15, 1, 0), (15, 4, 15), stone) # Wall 2
    grid.fill_box((0, 1, 0), (15, 4, 0), stone)   # Wall 3
    grid.fill_box((0, 1, 15), (15, 4, 15), stone) # Wall 4

    # Windows (clear some wall, add glass)
    grid.fill_box((6, 2, 0), (10, 3, 0), 0)       # Clear for window
    grid.fill_box((6, 2, 0), (10, 3, 0), glass)   # Add glass

    # Pillars
    grid.fill_box((4, 1, 4), (4, 3, 4), wood)
    grid.fill_box((12, 1, 4), (12, 3, 4), wood)
    grid.fill_box((4, 1, 12), (4, 3, 12), wood)
    grid.fill_box((12, 1, 12), (12, 3, 12), wood)

    # Gold decorations
    grid.set(8, 1, 8, gold)
    grid.set(7, 1, 8, gold)
    grid.set(9, 1, 8, gold)
    grid.set(8, 1, 7, gold)
    grid.set(8, 1, 9, gold)

    # Get original stats
    original_voxels = grid.count_non_air()
    original_materials = grid.material_count

    # === Test save/load to file ===
    with tempfile.NamedTemporaryFile(suffix='.mcvg', delete=False) as f:
        temp_path = f.name

    save_success = grid.save(temp_path)
    file_size = os.path.getsize(temp_path) if save_success else 0

    # Load into new grid
    loaded_grid = mcrfpy.VoxelGrid((1, 1, 1))
    load_success = loaded_grid.load(temp_path)
    os.unlink(temp_path)  # Clean up

    loaded_voxels = loaded_grid.count_non_air() if load_success else 0
    loaded_materials = loaded_grid.material_count if load_success else 0

    # === Test to_bytes/from_bytes ===
    data_bytes = grid.to_bytes()
    bytes_size = len(data_bytes)

    bytes_grid = mcrfpy.VoxelGrid((1, 1, 1))
    bytes_success = bytes_grid.from_bytes(data_bytes)
    bytes_voxels = bytes_grid.count_non_air() if bytes_success else 0

    # === Calculate compression ===
    raw_size = 16 * 16 * 16  # Uncompressed voxel data
    compression_ratio = raw_size / bytes_size if bytes_size > 0 else 0

    # Display information
    y_pos = 80

    # Original Grid Info
    info1 = mcrfpy.Caption(text="Original VoxelGrid:",
                           pos=(30, y_pos))
    info1.font_size = 20
    info1.fill_color = (100, 200, 255)
    ui.append(info1)
    y_pos += 30

    for line in [
        f"  Dimensions: 16x16x16 = 4096 voxels",
        f"  Non-air voxels: {original_voxels}",
        f"  Materials defined: {original_materials}",
        f"  Structure: Walled room with pillars, windows, gold decor"
    ]:
        cap = mcrfpy.Caption(text=line, pos=(30, y_pos))
        cap.font_size = 16
        cap.fill_color = (200, 200, 210)
        ui.append(cap)
        y_pos += 22

    y_pos += 20

    # File Save/Load Results
    info2 = mcrfpy.Caption(text="File Serialization (.mcvg):",
                           pos=(30, y_pos))
    info2.font_size = 20
    info2.fill_color = (100, 255, 150)
    ui.append(info2)
    y_pos += 30

    save_status = "SUCCESS" if save_success else "FAILED"
    load_status = "SUCCESS" if load_success else "FAILED"
    match_status = "MATCH" if loaded_voxels == original_voxels else "MISMATCH"

    for line in [
        f"  Save to file: {save_status}",
        f"  File size: {file_size} bytes",
        f"  Load from file: {load_status}",
        f"  Loaded voxels: {loaded_voxels} ({match_status})",
        f"  Loaded materials: {loaded_materials}"
    ]:
        color = (150, 255, 150) if "SUCCESS" in line or "MATCH" in line else (200, 200, 210)
        if "FAILED" in line or "MISMATCH" in line:
            color = (255, 100, 100)
        cap = mcrfpy.Caption(text=line, pos=(30, y_pos))
        cap.font_size = 16
        cap.fill_color = color
        ui.append(cap)
        y_pos += 22

    y_pos += 20

    # Bytes Serialization Results
    info3 = mcrfpy.Caption(text="Memory Serialization (to_bytes/from_bytes):",
                           pos=(30, y_pos))
    info3.font_size = 20
    info3.fill_color = (255, 200, 100)
    ui.append(info3)
    y_pos += 30

    bytes_status = "SUCCESS" if bytes_success else "FAILED"
    bytes_match = "MATCH" if bytes_voxels == original_voxels else "MISMATCH"

    for line in [
        f"  Serialized size: {bytes_size} bytes",
        f"  Raw voxel data: {raw_size} bytes",
        f"  Compression ratio: {compression_ratio:.1f}x",
        f"  from_bytes(): {bytes_status}",
        f"  Restored voxels: {bytes_voxels} ({bytes_match})"
    ]:
        color = (200, 200, 210)
        if "SUCCESS" in line or "MATCH" in line:
            color = (150, 255, 150)
        cap = mcrfpy.Caption(text=line, pos=(30, y_pos))
        cap.font_size = 16
        cap.fill_color = color
        ui.append(cap)
        y_pos += 22

    y_pos += 20

    # RLE Compression Demo
    info4 = mcrfpy.Caption(text="RLE Compression Effectiveness:",
                           pos=(30, y_pos))
    info4.font_size = 20
    info4.fill_color = (200, 150, 255)
    ui.append(info4)
    y_pos += 30

    # Create uniform grid for compression test
    uniform_grid = mcrfpy.VoxelGrid((32, 32, 32))
    uniform_mat = uniform_grid.add_material("solid", (128, 128, 128))
    uniform_grid.fill(uniform_mat)
    uniform_bytes = uniform_grid.to_bytes()
    uniform_raw = 32 * 32 * 32
    uniform_ratio = uniform_raw / len(uniform_bytes)

    for line in [
        f"  Uniform 32x32x32 filled grid:",
        f"    Raw: {uniform_raw} bytes",
        f"    Compressed: {len(uniform_bytes)} bytes",
        f"    Compression: {uniform_ratio:.0f}x",
        f"  ",
        f"  RLE excels at runs of identical values."
    ]:
        cap = mcrfpy.Caption(text=line, pos=(30, y_pos))
        cap.font_size = 16
        cap.fill_color = (200, 180, 220)
        ui.append(cap)
        y_pos += 22

    y_pos += 30

    # File Format Info
    info5 = mcrfpy.Caption(text="File Format (.mcvg):",
                           pos=(30, y_pos))
    info5.font_size = 20
    info5.fill_color = (255, 150, 200)
    ui.append(info5)
    y_pos += 30

    for line in [
        "  Header: Magic 'MCVG' + version + dimensions + cell_size",
        "  Materials: name, color (RGBA), sprite_index, transparent, path_cost",
        "  Voxel data: RLE-encoded material IDs",
        "  ",
        "  Note: Transform (offset, rotation) is runtime state, not serialized"
    ]:
        cap = mcrfpy.Caption(text=line, pos=(30, y_pos))
        cap.font_size = 14
        cap.fill_color = (200, 180, 200)
        ui.append(cap)
        y_pos += 20

    # API Reference on right side
    y_ref = 80
    x_ref = 550

    api_title = mcrfpy.Caption(text="Python API:", pos=(x_ref, y_ref))
    api_title.font_size = 20
    api_title.fill_color = (150, 200, 255)
    ui.append(api_title)
    y_ref += 35

    for line in [
        "# Save to file",
        "success = grid.save('world.mcvg')",
        "",
        "# Load from file",
        "grid = VoxelGrid((1,1,1))",
        "success = grid.load('world.mcvg')",
        "",
        "# Save to bytes",
        "data = grid.to_bytes()",
        "",
        "# Load from bytes",
        "success = grid.from_bytes(data)",
        "",
        "# Network example:",
        "# send_to_server(grid.to_bytes())",
        "# data = recv_from_server()",
        "# grid.from_bytes(data)"
    ]:
        cap = mcrfpy.Caption(text=line, pos=(x_ref, y_ref))
        cap.font_size = 14
        if line.startswith("#"):
            cap.fill_color = (100, 150, 100)
        elif "=" in line or "(" in line:
            cap.fill_color = (255, 220, 150)
        else:
            cap.fill_color = (180, 180, 180)
        ui.append(cap)
        y_ref += 18

    return scene


# Run demonstration
if __name__ == "__main__":
    import sys
    # Create and activate the scene
    scene = create_demo_scene()
    mcrfpy.current_scene = scene

    # When run directly, print summary and exit for headless testing
    print("\n=== Voxel Serialization Demo (Milestone 14) ===\n")

    # Run a quick verification
    grid = mcrfpy.VoxelGrid((8, 8, 8))
    mat = grid.add_material("test", (100, 100, 100))
    grid.fill_box((0, 0, 0), (7, 0, 7), mat)

    print(f"Created 8x8x8 grid with {grid.count_non_air()} non-air voxels")

    # Test to_bytes
    data = grid.to_bytes()
    print(f"Serialized to {len(data)} bytes")

    # Test from_bytes
    grid2 = mcrfpy.VoxelGrid((1, 1, 1))
    success = grid2.from_bytes(data)
    print(f"from_bytes(): {'SUCCESS' if success else 'FAILED'}")
    print(f"Restored size: {grid2.size}")
    print(f"Restored voxels: {grid2.count_non_air()}")

    # Compression test
    big_grid = mcrfpy.VoxelGrid((32, 32, 32))
    big_mat = big_grid.add_material("solid", (128, 128, 128))
    big_grid.fill(big_mat)
    big_data = big_grid.to_bytes()
    raw_size = 32 * 32 * 32
    print(f"\nCompression test (32x32x32 uniform):")
    print(f"  Raw: {raw_size} bytes")
    print(f"  Compressed: {len(big_data)} bytes")
    print(f"  Ratio: {raw_size / len(big_data):.0f}x")

    print("\n=== Demo complete ===")
    sys.exit(0)
