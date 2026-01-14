"""BSP Adjacency Graph Demo

Demonstrates: adjacency property, get_leaf, adjacent_tiles
Shows room connectivity for corridor generation.
"""
import mcrfpy
from mcrfpy import automation

GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def run_demo(runtime):
    # Create dungeon BSP
    bsp = mcrfpy.BSP(pos=(2, 2), size=(GRID_WIDTH - 4, GRID_HEIGHT - 4))
    bsp.split_recursive(depth=3, min_size=(10, 8), max_ratio=1.4, seed=42)

    # Fill with wall color
    color_layer.fill(mcrfpy.Color(50, 45, 55))

    # Generate distinct colors for each room
    num_rooms = len(bsp)
    room_colors = []
    for i in range(num_rooms):
        hue = (i * 137.5) % 360  # Golden angle for good distribution
        # HSV to RGB (simplified, saturation=0.6, value=0.7)
        h = hue / 60
        c = 0.42  # 0.6 * 0.7
        x = c * (1 - abs(h % 2 - 1))
        m = 0.28  # 0.7 - c

        if h < 1: r, g, b = c, x, 0
        elif h < 2: r, g, b = x, c, 0
        elif h < 3: r, g, b = 0, c, x
        elif h < 4: r, g, b = 0, x, c
        elif h < 5: r, g, b = x, 0, c
        else: r, g, b = c, 0, x

        room_colors.append(mcrfpy.Color(
            int((r + m) * 255),
            int((g + m) * 255),
            int((b + m) * 255)
        ))

    # Draw rooms with unique colors
    for i, leaf in enumerate(bsp.leaves()):
        pos = leaf.pos
        size = leaf.size
        color = room_colors[i]

        for y in range(pos[1] + 1, pos[1] + size[1] - 1):
            for x in range(pos[0] + 1, pos[0] + size[0] - 1):
                color_layer.set(((x, y)), color)

        # Room label
        cx, cy = leaf.center()
        label = mcrfpy.Caption(text=str(i), pos=(cx * CELL_SIZE - 4, cy * CELL_SIZE - 8))
        label.fill_color = mcrfpy.Color(255, 255, 255)
        label.outline = 1
        label.outline_color = mcrfpy.Color(0, 0, 0)
        scene.children.append(label)

    # Draw corridors using adjacency graph
    adjacency = bsp.adjacency
    connected = set()

    corridor_color = mcrfpy.Color(100, 95, 90)
    door_color = mcrfpy.Color(180, 140, 80)

    for leaf_idx in range(num_rooms):
        leaf = bsp.get_leaf(leaf_idx)

        # Get adjacent_tiles for this leaf
        adj_tiles = leaf.adjacent_tiles

        for neighbor_idx in adjacency[leaf_idx]:
            pair = (min(leaf_idx, neighbor_idx), max(leaf_idx, neighbor_idx))
            if pair in connected:
                continue
            connected.add(pair)

            neighbor = bsp.get_leaf(neighbor_idx)

            # Find shared wall tiles
            if neighbor_idx in adj_tiles:
                wall_tiles = adj_tiles[neighbor_idx]
                if len(wall_tiles) > 0:
                    # Pick middle tile for door
                    mid_tile = wall_tiles[len(wall_tiles) // 2]
                    dx, dy = int(mid_tile.x), int(mid_tile.y)

                    # Draw door
                    color_layer.set(((dx, dy)), door_color)

                    # Simple corridor: connect room centers through door
                    cx1, cy1 = leaf.center()
                    cx2, cy2 = neighbor.center()

                    # Path from room 1 to door
                    for x in range(min(cx1, dx), max(cx1, dx) + 1):
                        color_layer.set(((x, cy1)), corridor_color)
                    for y in range(min(cy1, dy), max(cy1, dy) + 1):
                        color_layer.set(((dx, y)), corridor_color)

                    # Path from door to room 2
                    for x in range(min(dx, cx2), max(dx, cx2) + 1):
                        color_layer.set(((x, dy)), corridor_color)
                    for y in range(min(dy, cy2), max(dy, cy2) + 1):
                        color_layer.set(((cx2, y)), corridor_color)
            else:
                # Fallback: L-shaped corridor
                cx1, cy1 = leaf.center()
                cx2, cy2 = neighbor.center()

                for x in range(min(cx1, cx2), max(cx1, cx2) + 1):
                    color_layer.set(((x, cy1)), corridor_color)
                for y in range(min(cy1, cy2), max(cy1, cy2) + 1):
                    color_layer.set(((cx2, y)), corridor_color)

    # Title and stats
    title = mcrfpy.Caption(
        text=f"BSP Adjacency: {num_rooms} rooms, {len(connected)} connections",
        pos=(10, 10)
    )
    title.fill_color = mcrfpy.Color(255, 255, 255)
    title.outline = 1
    title.outline_color = mcrfpy.Color(0, 0, 0)
    scene.children.append(title)

    # Legend
    legend = mcrfpy.Caption(
        text="Numbers = room index, Gold = doors, Brown = corridors",
        pos=(10, GRID_HEIGHT * CELL_SIZE - 25)
    )
    legend.fill_color = mcrfpy.Color(200, 200, 200)
    legend.outline = 1
    legend.outline_color = mcrfpy.Color(0, 0, 0)
    scene.children.append(legend)


# Setup
scene = mcrfpy.Scene("bsp_adjacency_demo")

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
automation.screenshot("procgen_12_bsp_adjacency.png")
print("Screenshot saved: procgen_12_bsp_adjacency.png")
