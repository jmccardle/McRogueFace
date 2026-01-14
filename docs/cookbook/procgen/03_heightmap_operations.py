"""HeightMap Combination Operations Demo

Demonstrates: add, subtract, multiply, min, max, lerp, copy_from
Shows how heightmaps can be combined for complex terrain effects.
"""
import mcrfpy
from mcrfpy import automation

GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def value_to_color(h):
    """Simple grayscale with color tinting for visibility."""
    h = max(0.0, min(1.0, h))
    # Blue-white-red gradient for clear visualization
    if h < 0.5:
        t = h / 0.5
        return mcrfpy.Color(int(50 * t), int(100 * t), int(200 - 100 * t))
    else:
        t = (h - 0.5) / 0.5
        return mcrfpy.Color(int(50 + 200 * t), int(100 + 100 * t), int(100 - 50 * t))

def run_demo(runtime):
    # Create 6 panels (2 rows x 3 columns)
    panel_w = GRID_WIDTH // 3
    panel_h = GRID_HEIGHT // 2

    # Create two base heightmaps for operations
    noise1 = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=42)
    noise2 = mcrfpy.NoiseSource(dimensions=2, algorithm='perlin', seed=123)

    base1 = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    base1.add_noise(noise1, world_size=(10, 10), mode='fbm', octaves=4)
    base1.normalize(0.0, 1.0)

    base2 = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    base2.add_noise(noise2, world_size=(10, 10), mode='fbm', octaves=4)
    base2.normalize(0.0, 1.0)

    # Panel 1: ADD operation (combined terrain)
    add_result = base1.copy_from(base1)  # Actually need to create new
    add_result = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    add_result.copy_from(base1).add(base2).normalize(0.0, 1.0)

    # Panel 2: SUBTRACT operation (carving)
    sub_result = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    sub_result.copy_from(base1).subtract(base2).normalize(0.0, 1.0)

    # Panel 3: MULTIPLY operation (masking)
    mul_result = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    mul_result.copy_from(base1).multiply(base2).normalize(0.0, 1.0)

    # Panel 4: MIN operation (valleys)
    min_result = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    min_result.copy_from(base1).min(base2)

    # Panel 5: MAX operation (ridges)
    max_result = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    max_result.copy_from(base1).max(base2)

    # Panel 6: LERP operation (blending)
    lerp_result = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    lerp_result.copy_from(base1).lerp(base2, 0.5)

    # Apply panels to grid
    panels = [
        (add_result, 0, 0, "ADD"),
        (sub_result, panel_w, 0, "SUBTRACT"),
        (mul_result, panel_w * 2, 0, "MULTIPLY"),
        (min_result, 0, panel_h, "MIN"),
        (max_result, panel_w, panel_h, "MAX"),
        (lerp_result, panel_w * 2, panel_h, "LERP(0.5)"),
    ]

    for hmap, ox, oy, name in panels:
        for y in range(panel_h):
            for x in range(panel_w):
                h = hmap.get((x, y))
                color_layer.set(((ox + x, oy + y)), value_to_color(h))

        # Add label
        label = mcrfpy.Caption(text=name, pos=(ox * CELL_SIZE + 5, oy * CELL_SIZE + 5))
        label.fill_color = mcrfpy.Color(255, 255, 255)
        label.outline = 1
        label.outline_color = mcrfpy.Color(0, 0, 0)
        scene.children.append(label)

    # Draw grid lines
    for y in range(GRID_HEIGHT):
        color_layer.set(((panel_w - 1, y)), mcrfpy.Color(255, 255, 255, 80))
        color_layer.set(((panel_w * 2 - 1, y)), mcrfpy.Color(255, 255, 255, 80))
    for x in range(GRID_WIDTH):
        color_layer.set(((x, panel_h - 1)), mcrfpy.Color(255, 255, 255, 80))


# Setup
scene = mcrfpy.Scene("operations_demo")

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
automation.screenshot("procgen_03_heightmap_operations.png")
print("Screenshot saved: procgen_03_heightmap_operations.png")
