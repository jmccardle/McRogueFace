"""BSP Dungeon Generation Demo

Demonstrates: BSP, split_recursive, leaves iteration, to_heightmap
Classic roguelike dungeon generation with rooms.
"""
import mcrfpy
from mcrfpy import automation

GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def run_demo(runtime):
    # Create BSP tree covering the map
    bsp = mcrfpy.BSP(pos=(1, 1), size=(GRID_WIDTH - 2, GRID_HEIGHT - 2))

    # Split recursively to create rooms
    # depth=4 creates up to 16 rooms, min_size ensures rooms aren't too small
    bsp.split_recursive(depth=4, min_size=(8, 6), max_ratio=1.5, seed=42)

    # Convert to heightmap for visualization
    # shrink=1 leaves 1-tile border for walls
    rooms_hmap = bsp.to_heightmap(
        size=(GRID_WIDTH, GRID_HEIGHT),
        select='leaves',
        shrink=1,
        value=1.0
    )

    # Fill background (walls)
    color_layer.fill(mcrfpy.Color(40, 35, 45))

    # Draw rooms
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if rooms_hmap.get((x, y)) > 0:
                color_layer.set(((x, y)), mcrfpy.Color(80, 75, 70))

    # Add some visual variety to rooms
    room_colors = [
        mcrfpy.Color(85, 80, 75),
        mcrfpy.Color(75, 70, 65),
        mcrfpy.Color(90, 85, 80),
        mcrfpy.Color(70, 65, 60),
    ]

    for i, leaf in enumerate(bsp.leaves()):
        pos = leaf.pos
        size = leaf.size
        color = room_colors[i % len(room_colors)]

        # Fill room interior (with shrink)
        for y in range(pos[1] + 1, pos[1] + size[1] - 1):
            for x in range(pos[0] + 1, pos[0] + size[0] - 1):
                if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                    color_layer.set(((x, y)), color)

        # Mark room center
        cx, cy = leaf.center()
        if 0 <= cx < GRID_WIDTH and 0 <= cy < GRID_HEIGHT:
            color_layer.set(((cx, cy)), mcrfpy.Color(200, 180, 100))

    # Simple corridor generation: connect adjacent rooms
    # Using adjacency graph
    adjacency = bsp.adjacency
    connected = set()

    for leaf_idx in range(len(bsp)):
        leaf = bsp.get_leaf(leaf_idx)
        cx1, cy1 = leaf.center()

        for neighbor_idx in adjacency[leaf_idx]:
            if (min(leaf_idx, neighbor_idx), max(leaf_idx, neighbor_idx)) in connected:
                continue
            connected.add((min(leaf_idx, neighbor_idx), max(leaf_idx, neighbor_idx)))

            neighbor = bsp.get_leaf(neighbor_idx)
            cx2, cy2 = neighbor.center()

            # Draw L-shaped corridor
            # Horizontal first, then vertical
            x1, x2 = min(cx1, cx2), max(cx1, cx2)
            for x in range(x1, x2 + 1):
                if 0 <= x < GRID_WIDTH and 0 <= cy1 < GRID_HEIGHT:
                    color_layer.set(((x, cy1)), mcrfpy.Color(100, 95, 90))

            y1, y2 = min(cy1, cy2), max(cy1, cy2)
            for y in range(y1, y2 + 1):
                if 0 <= cx2 < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                    color_layer.set(((cx2, y)), mcrfpy.Color(100, 95, 90))

    # Draw outer border
    for x in range(GRID_WIDTH):
        color_layer.set(((x, 0)), mcrfpy.Color(60, 50, 70))
        color_layer.set(((x, GRID_HEIGHT - 1)), mcrfpy.Color(60, 50, 70))
    for y in range(GRID_HEIGHT):
        color_layer.set(((0, y)), mcrfpy.Color(60, 50, 70))
        color_layer.set(((GRID_WIDTH - 1, y)), mcrfpy.Color(60, 50, 70))

    # Stats
    stats = mcrfpy.Caption(
        text=f"BSP Dungeon: {len(bsp)} rooms, depth=4, seed=42",
        pos=(10, 10)
    )
    stats.fill_color = mcrfpy.Color(255, 255, 255)
    stats.outline = 1
    stats.outline_color = mcrfpy.Color(0, 0, 0)
    scene.children.append(stats)


# Setup
scene = mcrfpy.Scene("bsp_dungeon_demo")

grid = mcrfpy.Grid(
    grid_size=(GRID_WIDTH, GRID_HEIGHT),
    pos=(0, 0),
    size=(GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE),
    layers={}
)
grid.fill_color = mcrfpy.Color(0, 0, 0)
color_layer = grid.add_layer("color", z_index=-1)
scene.children.append(grid)

scene.activate()

# Run the demo
run_demo(0)

# Take screenshot
automation.screenshot("procgen_10_bsp_dungeon.png")
print("Screenshot saved: procgen_10_bsp_dungeon.png")
