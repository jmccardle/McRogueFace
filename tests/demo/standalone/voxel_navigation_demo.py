#!/usr/bin/env python3
"""Visual Demo: Milestone 12 - VoxelGrid Navigation Projection

Demonstrates projection of 3D voxel terrain to 2D navigation grid for pathfinding.
Shows:
1. Voxel dungeon with multiple levels
2. Navigation grid projection (walkable/unwalkable areas)
3. A* pathfinding through the projected terrain
4. FOV computation from voxel transparency
"""

import mcrfpy
import sys
import math

def create_demo_scene():
    """Create the navigation projection demo scene"""

    scene = mcrfpy.Scene("voxel_nav_demo")

    # =========================================================================
    # Create a small dungeon-style voxel grid
    # =========================================================================

    vg = mcrfpy.VoxelGrid((16, 8, 16), cell_size=1.0)

    # Add materials
    floor_mat = vg.add_material("floor", (100, 80, 60))  # Brown floor
    wall_mat = vg.add_material("wall", (80, 80, 90), transparent=False)  # Gray walls
    pillar_mat = vg.add_material("pillar", (60, 60, 70), transparent=False)  # Dark pillars
    glass_mat = vg.add_material("glass", (150, 200, 255), transparent=True)  # Transparent glass
    water_mat = vg.add_material("water", (50, 100, 200), transparent=True, path_cost=3.0)  # Slow water

    # Create floor
    vg.fill_box((0, 0, 0), (15, 0, 15), floor_mat)

    # Create outer walls
    vg.fill_box((0, 1, 0), (15, 4, 0), wall_mat)   # North wall
    vg.fill_box((0, 1, 15), (15, 4, 15), wall_mat)  # South wall
    vg.fill_box((0, 1, 0), (0, 4, 15), wall_mat)   # West wall
    vg.fill_box((15, 1, 0), (15, 4, 15), wall_mat)  # East wall

    # Interior walls creating rooms
    vg.fill_box((5, 1, 0), (5, 4, 10), wall_mat)   # Vertical wall
    vg.fill_box((10, 1, 5), (15, 4, 5), wall_mat)  # Horizontal wall

    # Doorways (carve holes)
    vg.fill_box((5, 1, 3), (5, 2, 4), 0)  # Door in vertical wall
    vg.fill_box((12, 1, 5), (13, 2, 5), 0)  # Door in horizontal wall

    # Central pillars
    vg.fill_box((8, 1, 8), (8, 4, 8), pillar_mat)
    vg.fill_box((8, 1, 12), (8, 4, 12), pillar_mat)

    # Water pool in one corner (slow movement)
    vg.fill_box((1, 0, 11), (3, 0, 14), water_mat)

    # Glass window
    vg.fill_box((10, 2, 5), (11, 3, 5), glass_mat)

    # Raised platform in one area (height variation)
    vg.fill_box((12, 1, 8), (14, 1, 13), floor_mat)  # Platform at y=1

    # =========================================================================
    # Create Viewport3D with navigation grid
    # =========================================================================

    viewport = mcrfpy.Viewport3D(pos=(10, 10), size=(600, 400))
    viewport.set_grid_size(16, 16)
    viewport.cell_size = 1.0

    # Configure camera for top-down view
    viewport.camera_pos = (8, 15, 20)
    viewport.camera_target = (8, 0, 8)

    # Add voxel layer
    viewport.add_voxel_layer(vg, z_index=0)

    # Project voxels to navigation grid with headroom=2 (entity needs 2 voxels height)
    viewport.project_voxel_to_nav(vg, headroom=2)

    # =========================================================================
    # Info panel
    # =========================================================================

    info_frame = mcrfpy.Frame(pos=(620, 10), size=(250, 400))
    info_frame.fill_color = mcrfpy.Color(30, 30, 40, 220)
    info_frame.outline_color = mcrfpy.Color(100, 100, 120)
    info_frame.outline = 2.0

    title = mcrfpy.Caption(text="Nav Projection Demo", pos=(10, 10))
    title.fill_color = mcrfpy.Color(255, 255, 100)

    desc = mcrfpy.Caption(text="Voxels projected to\n2D nav grid", pos=(10, 35))
    desc.fill_color = mcrfpy.Color(200, 200, 200)

    info1 = mcrfpy.Caption(text="Grid: 16x16 cells", pos=(10, 75))
    info1.fill_color = mcrfpy.Color(150, 200, 255)

    info2 = mcrfpy.Caption(text="Headroom: 2 voxels", pos=(10, 95))
    info2.fill_color = mcrfpy.Color(150, 200, 255)

    # Count walkable cells
    walkable_count = 0
    for x in range(16):
        for z in range(16):
            cell = viewport.at(x, z)
            if cell.walkable:
                walkable_count += 1

    info3 = mcrfpy.Caption(text=f"Walkable: {walkable_count}/256", pos=(10, 115))
    info3.fill_color = mcrfpy.Color(100, 255, 100)

    # Find path example
    path = viewport.find_path((1, 1), (13, 13))
    info4 = mcrfpy.Caption(text=f"Path length: {len(path)}", pos=(10, 135))
    info4.fill_color = mcrfpy.Color(255, 200, 100)

    # FOV example
    fov = viewport.compute_fov((8, 8), 10)
    info5 = mcrfpy.Caption(text=f"FOV cells: {len(fov)}", pos=(10, 155))
    info5.fill_color = mcrfpy.Color(200, 150, 255)

    # Legend
    legend_title = mcrfpy.Caption(text="Materials:", pos=(10, 185))
    legend_title.fill_color = mcrfpy.Color(255, 255, 255)

    leg1 = mcrfpy.Caption(text="  Floor (walkable)", pos=(10, 205))
    leg1.fill_color = mcrfpy.Color(100, 80, 60)

    leg2 = mcrfpy.Caption(text="  Wall (blocking)", pos=(10, 225))
    leg2.fill_color = mcrfpy.Color(80, 80, 90)

    leg3 = mcrfpy.Caption(text="  Water (slow)", pos=(10, 245))
    leg3.fill_color = mcrfpy.Color(50, 100, 200)

    leg4 = mcrfpy.Caption(text="  Glass (see-through)", pos=(10, 265))
    leg4.fill_color = mcrfpy.Color(150, 200, 255)

    controls = mcrfpy.Caption(text="[Space] Recompute FOV\n[P] Show path\n[Q] Quit", pos=(10, 300))
    controls.fill_color = mcrfpy.Color(150, 150, 150)

    info_frame.children.extend([
        title, desc, info1, info2, info3, info4, info5,
        legend_title, leg1, leg2, leg3, leg4, controls
    ])

    # =========================================================================
    # Status bar
    # =========================================================================

    status_frame = mcrfpy.Frame(pos=(10, 420), size=(860, 50))
    status_frame.fill_color = mcrfpy.Color(20, 20, 30, 220)
    status_frame.outline_color = mcrfpy.Color(80, 80, 100)
    status_frame.outline = 1.0

    status_text = mcrfpy.Caption(
        text="Milestone 12: VoxelGrid Navigation Projection - Project 3D voxels to 2D pathfinding grid",
        pos=(10, 15)
    )
    status_text.fill_color = mcrfpy.Color(180, 180, 200)
    status_frame.children.append(status_text)

    # =========================================================================
    # Add elements to scene
    # =========================================================================

    scene.children.extend([viewport, info_frame, status_frame])

    # Store references for interaction (using module-level globals)
    global demo_viewport, demo_voxelgrid, demo_path, demo_fov_origin
    demo_viewport = viewport
    demo_voxelgrid = vg
    demo_path = path
    demo_fov_origin = (8, 8)

    # =========================================================================
    # Keyboard handler
    # =========================================================================

    def on_key(key, state):
        global demo_fov_origin
        if state != mcrfpy.InputState.PRESSED:
            return

        if key == mcrfpy.Key.Q or key == mcrfpy.Key.ESCAPE:
            # Exit
            sys.exit(0)
        elif key == mcrfpy.Key.SPACE:
            # Recompute FOV from different origin
            ox, oz = demo_fov_origin
            ox = (ox + 3) % 14 + 1
            oz = (oz + 5) % 14 + 1
            demo_fov_origin = (ox, oz)
            fov = demo_viewport.compute_fov((ox, oz), 8)
            info5.text = f"FOV from ({ox},{oz}): {len(fov)}"
        elif key == mcrfpy.Key.P:
            # Show path info
            print(f"Path from (1,1) to (13,13): {len(demo_path)} steps")
            for i, (px, pz) in enumerate(demo_path[:10]):
                cell = demo_viewport.at(px, pz)
                print(f"  Step {i}: ({px},{pz}) h={cell.height:.1f} cost={cell.cost:.1f}")
            if len(demo_path) > 10:
                print(f"  ... and {len(demo_path) - 10} more steps")

    scene.on_key = on_key

    return scene

def main():
    """Main entry point"""
    print("=== Milestone 12: VoxelGrid Navigation Projection Demo ===")
    print()
    print("This demo shows how 3D voxel terrain is projected to a 2D")
    print("navigation grid for pathfinding and FOV calculations.")
    print()
    print("The projection scans each column from top to bottom, finding")
    print("the topmost walkable floor with adequate headroom.")
    print()

    scene = create_demo_scene()
    mcrfpy.current_scene = scene

    # Print nav grid summary
    grid_w, grid_d = demo_viewport.grid_size
    print("Navigation grid summary:")
    print(f"  Grid size: {grid_w}x{grid_d}")

    # Count by walkability and transparency
    walkable = 0
    blocking = 0
    transparent = 0
    for x in range(grid_w):
        for z in range(grid_d):
            cell = demo_viewport.at(x, z)
            if cell.walkable:
                walkable += 1
            else:
                blocking += 1
            if cell.transparent:
                transparent += 1

    print(f"  Walkable cells: {walkable}")
    print(f"  Blocking cells: {blocking}")
    print(f"  Transparent cells: {transparent}")
    print()

if __name__ == "__main__":
    main()
    sys.exit(0)
