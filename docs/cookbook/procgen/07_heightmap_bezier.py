"""HeightMap Bezier Curves Demo

Demonstrates: dig_bezier for rivers, roads, and paths
Shows path carving with variable width and depth.
"""
import mcrfpy
from mcrfpy import automation
import math

GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def terrain_with_water(h):
    """Terrain coloring with water in low areas."""
    if h < 0.15:
        # Water (carved paths)
        t = h / 0.15
        return mcrfpy.Color(int(30 + t * 30), int(60 + t * 50), int(140 + t * 40))
    elif h < 0.25:
        # Shore/wet ground
        t = (h - 0.15) / 0.1
        return mcrfpy.Color(int(80 + t * 40), int(100 + t * 30), int(80 - t * 20))
    elif h < 0.5:
        # Lowland
        t = (h - 0.25) / 0.25
        return mcrfpy.Color(int(70 + t * 20), int(130 + t * 20), int(50 + t * 10))
    elif h < 0.7:
        # Highland
        t = (h - 0.5) / 0.2
        return mcrfpy.Color(int(60 + t * 30), int(110 - t * 20), int(45 + t * 15))
    elif h < 0.85:
        # Hills
        t = (h - 0.7) / 0.15
        return mcrfpy.Color(int(100 + t * 30), int(95 + t * 25), int(70 + t * 30))
    else:
        # Peaks
        t = (h - 0.85) / 0.15
        return mcrfpy.Color(int(150 + t * 60), int(150 + t * 60), int(155 + t * 60))

def run_demo(runtime):
    panel_w = GRID_WIDTH // 2
    panel_h = GRID_HEIGHT

    # Left panel: River system
    river_map = mcrfpy.HeightMap((panel_w, panel_h), fill=0.5)

    # Add terrain
    noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=42)
    river_map.add_noise(noise, world_size=(10, 10), mode='fbm', octaves=4, scale=0.3)
    river_map.add_hill((panel_w // 2, 5), 12, 0.3)  # Mountain source
    river_map.normalize(0.3, 0.9)

    # Main river - wide, flowing from top to bottom
    river_map.dig_bezier(
        points=((panel_w // 2, 2), (panel_w // 4, 15), (panel_w * 3 // 4, 30), (panel_w // 2, panel_h - 3)),
        start_radius=2, end_radius=5,
        start_height=0.1, end_height=0.05
    )

    # Tributary from left
    river_map.dig_bezier(
        points=((3, 20), (10, 18), (15, 22), (panel_w // 3, 20)),
        start_radius=1, end_radius=2,
        start_height=0.12, end_height=0.1
    )

    # Tributary from right
    river_map.dig_bezier(
        points=((panel_w - 3, 15), (panel_w - 8, 20), (panel_w - 12, 18), (panel_w * 2 // 3, 25)),
        start_radius=1, end_radius=2,
        start_height=0.12, end_height=0.1
    )

    # Right panel: Road network
    road_map = mcrfpy.HeightMap((panel_w, panel_h), fill=0.5)
    road_map.add_noise(noise, world_size=(8, 8), mode='fbm', octaves=3, scale=0.2)
    road_map.normalize(0.35, 0.7)

    # Main road - relatively straight
    road_map.dig_bezier(
        points=((5, panel_h // 2), (15, panel_h // 2 - 3), (panel_w - 15, panel_h // 2 + 3), (panel_w - 5, panel_h // 2)),
        start_radius=2, end_radius=2,
        start_height=0.25, end_height=0.25
    )

    # North-south crossing road
    road_map.dig_bezier(
        points=((panel_w // 2, 5), (panel_w // 2 + 5, 15), (panel_w // 2 - 5, 35), (panel_w // 2, panel_h - 5)),
        start_radius=2, end_radius=2,
        start_height=0.25, end_height=0.25
    )

    # Winding mountain path
    road_map.dig_bezier(
        points=((5, 8), (15, 5), (20, 15), (25, 10)),
        start_radius=1, end_radius=1,
        start_height=0.28, end_height=0.28
    )

    # Curved path to settlement
    road_map.dig_bezier(
        points=((panel_w - 5, panel_h - 8), (panel_w - 15, panel_h - 5), (panel_w - 10, panel_h - 15), (panel_w // 2 + 5, panel_h - 10)),
        start_radius=1, end_radius=2,
        start_height=0.27, end_height=0.26
    )

    # Apply to grid
    for y in range(panel_h):
        for x in range(panel_w):
            # Left panel: rivers
            h = river_map.get((x, y))
            color_layer.set(((x, y)), terrain_with_water(h))

            # Right panel: roads (use brown for roads)
            h2 = road_map.get((x, y))
            if h2 < 0.3:
                # Road surface
                t = h2 / 0.3
                color = mcrfpy.Color(int(140 - t * 40), int(120 - t * 30), int(80 - t * 20))
            else:
                color = terrain_with_water(h2)
            color_layer.set(((panel_w + x, y)), color)

    # Divider
    for y in range(GRID_HEIGHT):
        color_layer.set(((panel_w - 1, y)), mcrfpy.Color(100, 100, 100))

    # Labels
    labels = [("Rivers (dig_bezier)", 10, 10), ("Roads & Paths", panel_w * CELL_SIZE + 10, 10)]
    for text, x, ypos in labels:
        label = mcrfpy.Caption(text=text, pos=(x, ypos))
        label.fill_color = mcrfpy.Color(255, 255, 255)
        label.outline = 1
        label.outline_color = mcrfpy.Color(0, 0, 0)
        scene.children.append(label)


# Setup
scene = mcrfpy.Scene("bezier_demo")

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
automation.screenshot("procgen_07_heightmap_bezier.png")
print("Screenshot saved: procgen_07_heightmap_bezier.png")
