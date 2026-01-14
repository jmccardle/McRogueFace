"""BSP Manual Split Demo

Demonstrates: split_once for controlled layouts
Shows handcrafted room placement with manual BSP control.
"""
import mcrfpy
from mcrfpy import automation

GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def run_demo(runtime):
    # Fill background
    color_layer.fill(mcrfpy.Color(50, 45, 55))

    # Create main BSP covering most of the map
    bsp = mcrfpy.BSP(pos=(2, 2), size=(GRID_WIDTH - 4, GRID_HEIGHT - 4))

    # Manual split strategy for a temple-like layout:
    # 1. Split horizontally to create upper/lower sections
    # 2. Upper section: main hall (large) + side rooms
    # 3. Lower section: entrance + storage areas

    # First split: horizontal, creating top (sanctuary) and bottom (entrance) areas
    # Split at about 60% height
    split_y = 2 + int((GRID_HEIGHT - 4) * 0.6)
    bsp.split_once(horizontal=True, position=split_y)

    # Now manually color the structure
    root = bsp.root

    # Get the two main regions
    upper = root.left  # Sanctuary area
    lower = root.right  # Entrance area

    # Color the sanctuary (upper area) - golden temple floor
    if upper:
        pos, size = upper.pos, upper.size
        for y in range(pos[1] + 1, pos[1] + size[1] - 1):
            for x in range(pos[0] + 1, pos[0] + size[0] - 1):
                # Create a pattern
                if (x + y) % 4 == 0:
                    color_layer.set(((x, y)), mcrfpy.Color(180, 150, 80))
                else:
                    color_layer.set(((x, y)), mcrfpy.Color(160, 130, 70))

        # Add altar in center of sanctuary
        cx, cy = upper.center()
        for dy in range(-2, 3):
            for dx in range(-3, 4):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                    if abs(dx) <= 1 and abs(dy) <= 1:
                        color_layer.set(((nx, ny)), mcrfpy.Color(200, 180, 100))  # Altar
                    else:
                        color_layer.set(((nx, ny)), mcrfpy.Color(140, 100, 60))   # Altar base

    # Color the entrance (lower area) - stone floor
    if lower:
        pos, size = lower.pos, lower.size
        for y in range(pos[1] + 1, pos[1] + size[1] - 1):
            for x in range(pos[0] + 1, pos[0] + size[0] - 1):
                base = 80 + ((x * 3 + y * 7) % 20)
                color_layer.set(((x, y)), mcrfpy.Color(base, base - 5, base - 10))

        # Add entrance path
        cx = pos[0] + size[0] // 2
        for y in range(pos[1] + size[1] - 1, pos[1], -1):
            for dx in range(-2, 3):
                nx = cx + dx
                if pos[0] < nx < pos[0] + size[0] - 1:
                    color_layer.set(((nx, y)), mcrfpy.Color(100, 95, 85))

    # Add pillars along the sides
    if upper:
        pos, size = upper.pos, upper.size
        for y in range(pos[1] + 3, pos[1] + size[1] - 3, 4):
            # Left pillars
            color_layer.set(((pos[0] + 3, y)), mcrfpy.Color(120, 110, 100))
            color_layer.set(((pos[0] + 3, y + 1)), mcrfpy.Color(120, 110, 100))
            # Right pillars
            color_layer.set(((pos[0] + size[0] - 4, y)), mcrfpy.Color(120, 110, 100))
            color_layer.set(((pos[0] + size[0] - 4, y + 1)), mcrfpy.Color(120, 110, 100))

    # Add side chambers using manual rectangles
    # Left chamber
    chamber_w, chamber_h = 8, 6
    for y in range(10, 10 + chamber_h):
        for x in range(4, 4 + chamber_w):
            if x == 4 or x == 4 + chamber_w - 1 or y == 10 or y == 10 + chamber_h - 1:
                continue  # Skip border (walls)
            color_layer.set(((x, y)), mcrfpy.Color(100, 80, 90))  # Purple-ish storage

    # Right chamber
    for y in range(10, 10 + chamber_h):
        for x in range(GRID_WIDTH - 4 - chamber_w, GRID_WIDTH - 4):
            if x == GRID_WIDTH - 4 - chamber_w or x == GRID_WIDTH - 5 or y == 10 or y == 10 + chamber_h - 1:
                continue
            color_layer.set(((x, y)), mcrfpy.Color(80, 100, 90))  # Green-ish treasury

    # Connect chambers to main hall
    hall_y = 12
    for x in range(4 + chamber_w, 15):
        color_layer.set(((x, hall_y)), mcrfpy.Color(90, 85, 80))
    for x in range(GRID_WIDTH - 15, GRID_WIDTH - 4 - chamber_w):
        color_layer.set(((x, hall_y)), mcrfpy.Color(90, 85, 80))

    # Title
    title = mcrfpy.Caption(text="BSP split_once: Temple Layout", pos=(10, 10))
    title.fill_color = mcrfpy.Color(255, 255, 255)
    title.outline = 1
    title.outline_color = mcrfpy.Color(0, 0, 0)
    scene.children.append(title)

    # Labels for areas
    labels = [
        ("SANCTUARY", GRID_WIDTH // 2 * CELL_SIZE - 40, 80),
        ("ENTRANCE", GRID_WIDTH // 2 * CELL_SIZE - 35, split_y * CELL_SIZE + 30),
        ("Storage", 50, 180),
        ("Treasury", (GRID_WIDTH - 10) * CELL_SIZE - 30, 180),
    ]
    for text, x, y in labels:
        lbl = mcrfpy.Caption(text=text, pos=(x, y))
        lbl.fill_color = mcrfpy.Color(200, 200, 200)
        lbl.outline = 1
        lbl.outline_color = mcrfpy.Color(0, 0, 0)
        scene.children.append(lbl)


# Setup
scene = mcrfpy.Scene("bsp_manual_demo")

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
automation.screenshot("procgen_14_bsp_manual_split.png")
print("Screenshot saved: procgen_14_bsp_manual_split.png")
