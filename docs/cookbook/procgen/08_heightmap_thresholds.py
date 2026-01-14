"""HeightMap Thresholds and ColorLayer Integration Demo

Demonstrates: threshold, threshold_binary, inverse, count_in_range
Also: ColorLayer.apply_ranges for multi-threshold coloring
Shows terrain classification and visualization techniques.
"""
import mcrfpy
from mcrfpy import automation

GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def run_demo(runtime):
    panel_w = GRID_WIDTH // 3
    panel_h = GRID_HEIGHT // 2

    # Create source terrain
    noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=42)
    source = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    source.add_noise(noise, world_size=(10, 10), mode='fbm', octaves=5)
    source.add_hill((panel_w // 2, panel_h // 2), 8, 0.3)
    source.normalize(0.0, 1.0)

    # Create derived heightmaps
    water_mask = source.threshold((0.0, 0.3))  # Returns NEW heightmap with values only in range
    land_binary = source.threshold_binary((0.3, 1.0), value=1.0)  # Binary mask
    inverted = source.inverse()  # Inverted values

    # Count cells in ranges for classification stats
    water_count = source.count_in_range((0.0, 0.3))
    land_count = source.count_in_range((0.3, 0.7))
    mountain_count = source.count_in_range((0.7, 1.0))

    # IMPORTANT: Render apply_ranges FIRST since it affects the whole layer
    # Panel 6: Using ColorLayer.apply_ranges (bottom-right)
    # Create a full-size heightmap and copy source data to correct position
    panel6_hmap = mcrfpy.HeightMap((GRID_WIDTH, GRID_HEIGHT), fill=-1.0)  # -1 won't match any range
    for y in range(panel_h):
        for x in range(panel_w):
            h = source.get((x, y))
            panel6_hmap.fill(h, pos=(panel_w * 2 + x, panel_h + y), size=(1, 1))

    # apply_ranges colors cells based on height ranges
    # Cells with -1.0 won't match any range and stay unchanged
    color_layer.apply_ranges(panel6_hmap, [
        ((0.0, 0.2), (30, 80, 160)),           # Deep water
        ((0.2, 0.3), ((60, 120, 180), (120, 160, 140))),  # Gradient: shallow to shore
        ((0.3, 0.5), (80, 150, 60)),           # Lowland
        ((0.5, 0.7), ((60, 120, 40), (100, 100, 80))),   # Gradient: forest to hills
        ((0.7, 0.85), (130, 120, 110)),        # Rock
        ((0.85, 1.0), ((180, 180, 190), (250, 250, 255))),  # Gradient: rock to snow
    ])

    # Now render the other 5 panels (they will overwrite only their regions)

    # Panel 1 (top-left): Original grayscale
    for y in range(panel_h):
        for x in range(panel_w):
            h = source.get((x, y))
            v = int(h * 255)
            color_layer.set(((x, y)), mcrfpy.Color(v, v, v))

    # Panel 2 (top-middle): threshold() - shows only values in range 0.0-0.3
    for y in range(panel_h):
        for x in range(panel_w):
            h = water_mask.get((x, y))
            if h > 0:
                # Values were preserved in 0.0-0.3 range
                t = h / 0.3
                color_layer.set(((panel_w + x, y)), mcrfpy.Color(
                    int(30 + t * 40), int(60 + t * 60), int(150 + t * 50)))
            else:
                # Outside threshold range - dark
                color_layer.set(((panel_w + x, y)), mcrfpy.Color(20, 20, 30))

    # Panel 3 (top-right): threshold_binary() - land mask
    for y in range(panel_h):
        for x in range(panel_w):
            h = land_binary.get((x, y))
            if h > 0:
                color_layer.set(((panel_w * 2 + x, y)), mcrfpy.Color(80, 140, 60))  # Land
            else:
                color_layer.set(((panel_w * 2 + x, y)), mcrfpy.Color(40, 80, 150))  # Water

    # Panel 4 (bottom-left): inverse()
    for y in range(panel_h):
        for x in range(panel_w):
            h = inverted.get((x, y))
            v = int(h * 255)
            color_layer.set(((x, panel_h + y)), mcrfpy.Color(v, int(v * 0.8), int(v * 0.6)))

    # Panel 5 (bottom-middle): Classification using count_in_range results
    for y in range(panel_h):
        for x in range(panel_w):
            h = source.get((x, y))
            if h < 0.3:
                color_layer.set(((panel_w + x, panel_h + y)), mcrfpy.Color(50, 100, 180))  # Water
            elif h < 0.7:
                color_layer.set(((panel_w + x, panel_h + y)), mcrfpy.Color(70, 140, 50))   # Land
            else:
                color_layer.set(((panel_w + x, panel_h + y)), mcrfpy.Color(140, 130, 120)) # Mountain

    # Labels
    labels = [
        ("Original (grayscale)", 5, 5),
        ("threshold(0-0.3)", panel_w * CELL_SIZE + 5, 5),
        ("threshold_binary(land)", panel_w * 2 * CELL_SIZE + 5, 5),
        ("inverse()", 5, panel_h * CELL_SIZE + 5),
        (f"Classified (W:{water_count} L:{land_count} M:{mountain_count})", panel_w * CELL_SIZE + 5, panel_h * CELL_SIZE + 5),
        ("apply_ranges (biome)", panel_w * 2 * CELL_SIZE + 5, panel_h * CELL_SIZE + 5),
    ]

    for text, x, y in labels:
        label = mcrfpy.Caption(text=text, pos=(x, y))
        label.fill_color = mcrfpy.Color(255, 255, 255)
        label.outline = 1
        label.outline_color = mcrfpy.Color(0, 0, 0)
        scene.children.append(label)

    # Grid divider lines
    for y in range(GRID_HEIGHT):
        color_layer.set(((panel_w - 1, y)), mcrfpy.Color(80, 80, 80))
        color_layer.set(((panel_w * 2 - 1, y)), mcrfpy.Color(80, 80, 80))
    for x in range(GRID_WIDTH):
        color_layer.set(((x, panel_h - 1)), mcrfpy.Color(80, 80, 80))


# Setup
scene = mcrfpy.Scene("thresholds_demo")

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
automation.screenshot("procgen_08_heightmap_thresholds.png")
print("Screenshot saved: procgen_08_heightmap_thresholds.png")
