"""BSP Shrink Parameter Demo

Demonstrates: to_heightmap with different shrink values
Shows room padding for walls and varied room sizes.
"""
import mcrfpy
from mcrfpy import automation

GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def run_demo(runtime):
    panel_w = GRID_WIDTH // 3
    panel_h = GRID_HEIGHT // 2

    # Use reasonable shrink values relative to room sizes
    shrink_values = [
        (0, "shrink=0", "Rooms fill BSP bounds"),
        (1, "shrink=1", "Standard 1-tile walls"),
        (2, "shrink=2", "Thick fortress walls"),
        (3, "shrink=3", "Wide hallway spacing"),
        (-1, "Random shrink", "Per-room variation"),
        (-2, "Gradient", "Shrink by leaf index"),
    ]

    panels = [
        (0, 0), (panel_w, 0), (panel_w * 2, 0),
        (0, panel_h), (panel_w, panel_h), (panel_w * 2, panel_h)
    ]

    for panel_idx, (shrink, title, desc) in enumerate(shrink_values):
        ox, oy = panels[panel_idx]

        # Create BSP - use depth=2 for larger rooms, bigger min_size
        bsp = mcrfpy.BSP(pos=(ox + 1, oy + 3), size=(panel_w - 2, panel_h - 4))
        bsp.split_recursive(depth=2, min_size=(8, 6), seed=42)

        # Fill panel background (stone wall)
        color_layer.fill_rect((ox, oy), (panel_w, panel_h), mcrfpy.Color(50, 45, 55))

        if shrink >= 0:
            # Standard shrink value using to_heightmap
            rooms_hmap = bsp.to_heightmap(
                size=(GRID_WIDTH, GRID_HEIGHT),
                select='leaves',
                shrink=shrink,
                value=1.0
            )

            # Draw floors with color based on shrink level
            floor_colors = [
                mcrfpy.Color(140, 120, 100),  # shrink=0: tan/full
                mcrfpy.Color(110, 100, 90),   # shrink=1: gray-brown
                mcrfpy.Color(90, 95, 100),    # shrink=2: blue-gray
                mcrfpy.Color(80, 90, 110),    # shrink=3: slate
            ]
            floor_color = floor_colors[min(shrink, len(floor_colors) - 1)]

            for y in range(oy, oy + panel_h):
                for x in range(ox, ox + panel_w):
                    if rooms_hmap.get((x, y)) > 0:
                        # Add subtle tile pattern
                        var = ((x + y) % 2) * 8
                        c = mcrfpy.Color(
                            floor_color.r + var,
                            floor_color.g + var,
                            floor_color.b + var
                        )
                        color_layer.set(((x, y)), c)
        elif shrink == -1:
            # Random shrink per room
            import random
            rand = random.Random(42)
            for leaf in bsp.leaves():
                room_shrink = rand.randint(0, 3)
                pos = leaf.pos
                size = leaf.size

                x1 = pos[0] + room_shrink
                y1 = pos[1] + room_shrink
                x2 = pos[0] + size[0] - room_shrink
                y2 = pos[1] + size[1] - room_shrink

                if x2 > x1 and y2 > y1:
                    colors = [
                        mcrfpy.Color(160, 130, 100),  # Full
                        mcrfpy.Color(130, 120, 100),
                        mcrfpy.Color(100, 110, 110),
                        mcrfpy.Color(80, 90, 100),    # Most shrunk
                    ]
                    floor_color = colors[room_shrink]

                    for y in range(y1, y2):
                        for x in range(x1, x2):
                            if ox <= x < ox + panel_w and oy <= y < oy + panel_h:
                                var = ((x + y) % 2) * 6
                                c = mcrfpy.Color(
                                    floor_color.r + var,
                                    floor_color.g + var,
                                    floor_color.b + var
                                )
                                color_layer.set(((x, y)), c)
        else:
            # Gradient shrink by leaf index
            leaves = list(bsp.leaves())
            for i, leaf in enumerate(leaves):
                # Shrink increases with leaf index
                room_shrink = min(3, i)
                pos = leaf.pos
                size = leaf.size

                x1 = pos[0] + room_shrink
                y1 = pos[1] + room_shrink
                x2 = pos[0] + size[0] - room_shrink
                y2 = pos[1] + size[1] - room_shrink

                if x2 > x1 and y2 > y1:
                    # Color gradient: warm to cool as shrink increases
                    t = i / max(1, len(leaves) - 1)
                    floor_color = mcrfpy.Color(
                        int(180 - t * 80),
                        int(120 + t * 20),
                        int(80 + t * 60)
                    )

                    for y in range(y1, y2):
                        for x in range(x1, x2):
                            if ox <= x < ox + panel_w and oy <= y < oy + panel_h:
                                var = ((x + y) % 2) * 6
                                c = mcrfpy.Color(
                                    floor_color.r + var,
                                    floor_color.g + var - 2,
                                    floor_color.b + var
                                )
                                color_layer.set(((x, y)), c)

        # Add labels
        label = mcrfpy.Caption(text=title, pos=(ox * CELL_SIZE + 5, oy * CELL_SIZE + 5))
        label.fill_color = mcrfpy.Color(255, 255, 255)
        label.outline = 1
        label.outline_color = mcrfpy.Color(0, 0, 0)
        scene.children.append(label)

        desc_label = mcrfpy.Caption(text=desc, pos=(ox * CELL_SIZE + 5, oy * CELL_SIZE + 22))
        desc_label.fill_color = mcrfpy.Color(200, 200, 200)
        desc_label.outline = 1
        desc_label.outline_color = mcrfpy.Color(0, 0, 0)
        scene.children.append(desc_label)

    # Grid lines
    for y in range(GRID_HEIGHT):
        color_layer.set(((panel_w - 1, y)), mcrfpy.Color(30, 30, 35))
        color_layer.set(((panel_w * 2 - 1, y)), mcrfpy.Color(30, 30, 35))
    for x in range(GRID_WIDTH):
        color_layer.set(((x, panel_h - 1)), mcrfpy.Color(30, 30, 35))


# Setup
scene = mcrfpy.Scene("bsp_shrink_demo")

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
automation.screenshot("procgen_13_bsp_shrink.png")
print("Screenshot saved: procgen_13_bsp_shrink.png")
