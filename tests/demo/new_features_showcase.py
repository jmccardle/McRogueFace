#!/usr/bin/env python3
"""
New Features Screenshot Showcase - Alignment + Dijkstra-to-HeightMap

Generates screenshots for the new API cookbook recipes.
Run with: xvfb-run -a ./build/mcrogueface --headless --exec tests/demo/new_features_showcase.py
"""
import mcrfpy
from mcrfpy import automation
import sys
import os

OUTPUT_DIR = "/opt/goblincorps/repos/mcrogueface.github.io/images/cookbook"


def screenshot_alignment():
    """Create an alignment system showcase."""
    scene = mcrfpy.Scene("alignment")

    # Dark background
    bg = mcrfpy.Frame(pos=(0, 0), size=(800, 600))
    bg.fill_color = mcrfpy.Color(20, 20, 30)
    scene.children.append(bg)

    # Title
    title = mcrfpy.Caption(text="UI Alignment System", pos=(50, 20))
    title.fill_color = mcrfpy.Color(255, 255, 255)
    title.font_size = 28
    scene.children.append(title)

    subtitle = mcrfpy.Caption(text="Auto-positioning with reactive resize", pos=(50, 50))
    subtitle.fill_color = mcrfpy.Color(180, 180, 200)
    subtitle.font_size = 16
    scene.children.append(subtitle)

    # Demo container
    container = mcrfpy.Frame(pos=(100, 100), size=(600, 400))
    container.fill_color = mcrfpy.Color(40, 40, 50)
    container.outline = 2
    container.outline_color = mcrfpy.Color(80, 80, 100)
    scene.children.append(container)

    # Container label
    container_label = mcrfpy.Caption(text="Parent Container (600x400)", pos=(10, 10))
    container_label.fill_color = mcrfpy.Color(100, 100, 120)
    container_label.font_size = 12
    container.children.append(container_label)

    # 9 alignment positions demo
    alignments = [
        (mcrfpy.Alignment.TOP_LEFT, "TL", mcrfpy.Color(200, 80, 80)),
        (mcrfpy.Alignment.TOP_CENTER, "TC", mcrfpy.Color(200, 150, 80)),
        (mcrfpy.Alignment.TOP_RIGHT, "TR", mcrfpy.Color(200, 200, 80)),
        (mcrfpy.Alignment.CENTER_LEFT, "CL", mcrfpy.Color(80, 200, 80)),
        (mcrfpy.Alignment.CENTER, "C", mcrfpy.Color(80, 200, 200)),
        (mcrfpy.Alignment.CENTER_RIGHT, "CR", mcrfpy.Color(80, 80, 200)),
        (mcrfpy.Alignment.BOTTOM_LEFT, "BL", mcrfpy.Color(150, 80, 200)),
        (mcrfpy.Alignment.BOTTOM_CENTER, "BC", mcrfpy.Color(200, 80, 200)),
        (mcrfpy.Alignment.BOTTOM_RIGHT, "BR", mcrfpy.Color(200, 80, 150)),
    ]

    for align, label, color in alignments:
        box = mcrfpy.Frame(pos=(0, 0), size=(60, 40))
        box.fill_color = color
        box.outline = 1
        box.outline_color = mcrfpy.Color(255, 255, 255)
        box.align = align
        if align != mcrfpy.Alignment.CENTER:
            box.margin = 15.0

        # Label inside box
        text = mcrfpy.Caption(text=label, pos=(0, 0))
        text.fill_color = mcrfpy.Color(255, 255, 255)
        text.font_size = 16
        text.align = mcrfpy.Alignment.CENTER
        box.children.append(text)

        container.children.append(box)

    # Legend
    legend = mcrfpy.Caption(text="TL=TOP_LEFT  TC=TOP_CENTER  TR=TOP_RIGHT  etc.", pos=(100, 520))
    legend.fill_color = mcrfpy.Color(150, 150, 170)
    legend.font_size = 14
    scene.children.append(legend)

    legend2 = mcrfpy.Caption(text="All boxes have margin=15 except CENTER", pos=(100, 545))
    legend2.fill_color = mcrfpy.Color(150, 150, 170)
    legend2.font_size = 14
    scene.children.append(legend2)

    scene.activate()
    output_path = os.path.join(OUTPUT_DIR, "ui_alignment.png")
    automation.screenshot(output_path)
    print(f"  -> {output_path}")


def screenshot_dijkstra_heightmap():
    """Create a dijkstra-to-heightmap showcase."""
    scene = mcrfpy.Scene("dijkstra_hmap")

    # Title
    title = mcrfpy.Caption(text="Dijkstra to HeightMap", pos=(50, 20))
    title.fill_color = mcrfpy.Color(255, 255, 255)
    title.font_size = 28
    scene.children.append(title)

    subtitle = mcrfpy.Caption(text="Distance-based gradients for fog, difficulty, and visualization", pos=(50, 50))
    subtitle.fill_color = mcrfpy.Color(180, 180, 200)
    subtitle.font_size = 16
    scene.children.append(subtitle)

    # Create grid for dijkstra visualization
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(
        pos=(50, 90),
        size=(350, 350),
        grid_size=(16, 16),
        texture=texture,
        zoom=1.3
    )
    grid.fill_color = mcrfpy.Color(20, 20, 30)
    scene.children.append(grid)

    # Initialize grid
    for y in range(16):
        for x in range(16):
            grid.at((x, y)).walkable = True
            grid.at((x, y)).tilesprite = 42  # floor

    # Add some walls
    for i in range(5, 11):
        grid.at((i, 5)).walkable = False
        grid.at((i, 5)).tilesprite = 30  # wall
        grid.at((5, i)).walkable = False
        grid.at((5, i)).tilesprite = 30

    # Player at center
    player = mcrfpy.Entity(grid_pos=(8, 8), texture=texture, sprite_index=84)
    grid.entities.append(player)

    # Get dijkstra and create color visualization
    dijkstra = grid.get_dijkstra_map((8, 8))
    hmap = dijkstra.to_heightmap(unreachable=-1.0)

    # Find max for normalization
    max_dist = 0
    for y in range(16):
        for x in range(16):
            d = hmap[(x, y)]
            if d > max_dist and d >= 0:
                max_dist = d

    # Second visualization panel - color gradient
    viz_frame = mcrfpy.Frame(pos=(420, 90), size=(350, 350))
    viz_frame.fill_color = mcrfpy.Color(30, 30, 40)
    viz_frame.outline = 2
    viz_frame.outline_color = mcrfpy.Color(60, 60, 80)
    scene.children.append(viz_frame)

    viz_label = mcrfpy.Caption(text="Distance Visualization", pos=(80, 10))
    viz_label.fill_color = mcrfpy.Color(200, 200, 220)
    viz_label.font_size = 16
    viz_frame.children.append(viz_label)

    # Draw colored squares for each cell
    cell_size = 20
    offset_x = 15
    offset_y = 35

    for y in range(16):
        for x in range(16):
            dist = hmap[(x, y)]

            if dist < 0:
                # Unreachable - dark red
                color = mcrfpy.Color(60, 0, 0)
            elif dist == 0:
                # Source - bright yellow
                color = mcrfpy.Color(255, 255, 0)
            else:
                # Gradient: green (near) to blue (far)
                t = min(1.0, dist / max_dist)
                r = 0
                g = int(200 * (1 - t))
                b = int(200 * t)
                color = mcrfpy.Color(r, g, b)

            cell = mcrfpy.Frame(
                pos=(offset_x + x * cell_size, offset_y + y * cell_size),
                size=(cell_size - 1, cell_size - 1)
            )
            cell.fill_color = color
            viz_frame.children.append(cell)

    # Legend
    legend_frame = mcrfpy.Frame(pos=(50, 460), size=(720, 100))
    legend_frame.fill_color = mcrfpy.Color(30, 30, 40)
    legend_frame.outline = 1
    legend_frame.outline_color = mcrfpy.Color(60, 60, 80)
    scene.children.append(legend_frame)

    leg1 = mcrfpy.Caption(text="Use Cases:", pos=(15, 10))
    leg1.fill_color = mcrfpy.Color(255, 255, 255)
    leg1.font_size = 16
    legend_frame.children.append(leg1)

    uses = [
        "Distance-based enemy difficulty",
        "Fog intensity gradients",
        "Pathfinding visualization",
        "Influence maps for AI",
    ]
    for i, use in enumerate(uses):
        txt = mcrfpy.Caption(text=f"- {use}", pos=(15 + (i // 2) * 350, 35 + (i % 2) * 25))
        txt.fill_color = mcrfpy.Color(180, 180, 200)
        txt.font_size = 14
        legend_frame.children.append(txt)

    # Color key
    key_label = mcrfpy.Caption(text="Yellow=Source  Green=Near  Blue=Far  Red=Blocked", pos=(420, 450))
    key_label.fill_color = mcrfpy.Color(150, 150, 170)
    key_label.font_size = 12
    scene.children.append(key_label)

    scene.activate()
    output_path = os.path.join(OUTPUT_DIR, "grid_dijkstra_heightmap.png")
    automation.screenshot(output_path)
    print(f"  -> {output_path}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=== New Features Screenshot Showcase ===")
    print(f"Output: {OUTPUT_DIR}\n")

    showcases = [
        ('Alignment System', screenshot_alignment),
        ('Dijkstra to HeightMap', screenshot_dijkstra_heightmap),
    ]

    for name, func in showcases:
        print(f"Generating {name}...")
        try:
            func()
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    print("\n=== New feature screenshots generated! ===")
    sys.exit(0)


main()
