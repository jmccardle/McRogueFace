"""BSP Traversal Orders Demo

Demonstrates: traverse() with different Traversal orders
Shows how traversal order affects leaf enumeration.
"""
import mcrfpy
from mcrfpy import automation

GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def run_demo(runtime):
    panel_w = GRID_WIDTH // 3
    panel_h = GRID_HEIGHT // 2

    traversal_orders = [
        (mcrfpy.Traversal.PRE_ORDER, "PRE_ORDER", "Root first, then children"),
        (mcrfpy.Traversal.IN_ORDER, "IN_ORDER", "Left, node, right"),
        (mcrfpy.Traversal.POST_ORDER, "POST_ORDER", "Children before parent"),
        (mcrfpy.Traversal.LEVEL_ORDER, "LEVEL_ORDER", "Breadth-first by level"),
        (mcrfpy.Traversal.INVERTED_LEVEL_ORDER, "INV_LEVEL", "Deepest levels first"),
    ]

    panels = [
        (0, 0), (panel_w, 0), (panel_w * 2, 0),
        (0, panel_h), (panel_w, panel_h), (panel_w * 2, panel_h)
    ]

    # Distinct color palette for 8+ leaves
    leaf_colors = [
        mcrfpy.Color(220, 60, 60),    # Red
        mcrfpy.Color(60, 180, 60),    # Green
        mcrfpy.Color(60, 100, 220),   # Blue
        mcrfpy.Color(220, 180, 40),   # Yellow
        mcrfpy.Color(180, 60, 180),   # Magenta
        mcrfpy.Color(60, 200, 200),   # Cyan
        mcrfpy.Color(220, 120, 60),   # Orange
        mcrfpy.Color(160, 100, 200),  # Purple
        mcrfpy.Color(100, 200, 120),  # Mint
        mcrfpy.Color(200, 100, 140),  # Pink
    ]

    for panel_idx, (order, name, desc) in enumerate(traversal_orders):
        if panel_idx >= 6:
            break

        ox, oy = panels[panel_idx]

        # Create BSP for this panel
        bsp = mcrfpy.BSP(pos=(ox + 2, oy + 4), size=(panel_w - 4, panel_h - 6))
        bsp.split_recursive(depth=3, min_size=(5, 4), seed=42)

        # Fill panel background (dark gray = walls)
        color_layer.fill_rect((ox, oy), (panel_w, panel_h), mcrfpy.Color(40, 35, 45))

        # Traverse and color ONLY LEAVES by their position in traversal
        leaf_idx = 0
        for node in bsp.traverse(order):
            if not node.is_leaf:
                continue  # Skip branch nodes

            color = leaf_colors[leaf_idx % len(leaf_colors)]
            pos = node.pos
            size = node.size

            # Shrink by 1 to show walls between rooms
            for y in range(pos[1] + 1, pos[1] + size[1] - 1):
                for x in range(pos[0] + 1, pos[0] + size[0] - 1):
                    if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                        color_layer.set(((x, y)), color)

            # Draw leaf index in center
            cx, cy = node.center()
            # Draw index as a darker spot
            if 0 <= cx < GRID_WIDTH and 0 <= cy < GRID_HEIGHT:
                dark = mcrfpy.Color(color.r // 2, color.g // 2, color.b // 2)
                color_layer.set(((cx, cy)), dark)
                if cx + 1 < GRID_WIDTH:
                    color_layer.set(((cx + 1, cy)), dark)

            leaf_idx += 1

        # Add labels
        label = mcrfpy.Caption(text=f"{name}", pos=(ox * CELL_SIZE + 5, oy * CELL_SIZE + 5))
        label.fill_color = mcrfpy.Color(255, 255, 255)
        label.outline = 1
        label.outline_color = mcrfpy.Color(0, 0, 0)
        scene.children.append(label)

        desc_label = mcrfpy.Caption(text=f"{desc} ({leaf_idx} leaves)", pos=(ox * CELL_SIZE + 5, oy * CELL_SIZE + 22))
        desc_label.fill_color = mcrfpy.Color(200, 200, 200)
        desc_label.outline = 1
        desc_label.outline_color = mcrfpy.Color(0, 0, 0)
        scene.children.append(desc_label)

    # Panel 6: Show tree depth levels (branch AND leaf nodes)
    ox, oy = panels[5]
    bsp = mcrfpy.BSP(pos=(ox + 2, oy + 4), size=(panel_w - 4, panel_h - 6))
    bsp.split_recursive(depth=3, min_size=(5, 4), seed=42)

    color_layer.fill_rect((ox, oy), (panel_w, panel_h), mcrfpy.Color(40, 35, 45))

    # Draw by level - deepest first so leaves are on top
    level_colors = [
        mcrfpy.Color(60, 40, 40),     # Level 0 (root) - dark
        mcrfpy.Color(80, 60, 50),     # Level 1
        mcrfpy.Color(100, 80, 60),    # Level 2
        mcrfpy.Color(140, 120, 80),   # Level 3 (leaves usually)
    ]

    # Use INVERTED_LEVEL_ORDER so leaves are drawn last
    for node in bsp.traverse(mcrfpy.Traversal.INVERTED_LEVEL_ORDER):
        level = node.level
        color = level_colors[min(level, len(level_colors) - 1)]

        # Make leaves brighter
        if node.is_leaf:
            color = mcrfpy.Color(
                min(255, color.r + 80),
                min(255, color.g + 80),
                min(255, color.b + 60)
            )

        pos = node.pos
        size = node.size

        for y in range(pos[1], pos[1] + size[1]):
            for x in range(pos[0], pos[0] + size[0]):
                if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                    # Draw border
                    if x == pos[0] or x == pos[0] + size[0] - 1 or \
                       y == pos[1] or y == pos[1] + size[1] - 1:
                        border = mcrfpy.Color(20, 20, 30)
                        color_layer.set(((x, y)), border)
                    else:
                        color_layer.set(((x, y)), color)

    label = mcrfpy.Caption(text="BY LEVEL (depth)", pos=(ox * CELL_SIZE + 5, oy * CELL_SIZE + 5))
    label.fill_color = mcrfpy.Color(255, 255, 255)
    label.outline = 1
    label.outline_color = mcrfpy.Color(0, 0, 0)
    scene.children.append(label)

    desc_label = mcrfpy.Caption(text="Darker=root, Bright=leaves", pos=(ox * CELL_SIZE + 5, oy * CELL_SIZE + 22))
    desc_label.fill_color = mcrfpy.Color(200, 200, 200)
    desc_label.outline = 1
    desc_label.outline_color = mcrfpy.Color(0, 0, 0)
    scene.children.append(desc_label)

    # Grid lines
    for y in range(GRID_HEIGHT):
        color_layer.set(((panel_w - 1, y)), mcrfpy.Color(60, 60, 60))
        color_layer.set(((panel_w * 2 - 1, y)), mcrfpy.Color(60, 60, 60))
    for x in range(GRID_WIDTH):
        color_layer.set(((x, panel_h - 1)), mcrfpy.Color(60, 60, 60))


# Setup
scene = mcrfpy.Scene("bsp_traversal_demo")

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
automation.screenshot("procgen_11_bsp_traversal.png")
print("Screenshot saved: procgen_11_bsp_traversal.png")
