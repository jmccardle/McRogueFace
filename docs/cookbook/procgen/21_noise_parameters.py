"""NoiseSource Parameters Demo

Demonstrates: hurst (roughness), lacunarity (frequency scaling), octaves
Shows how parameters affect terrain character.
"""
import mcrfpy
from mcrfpy import automation

GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def value_to_gray(h):
    """Simple grayscale visualization."""
    h = (h + 1) / 2  # -1..1 to 0..1
    h = max(0.0, min(1.0, h))
    v = int(h * 255)
    return mcrfpy.Color(v, v, v)

def run_demo(runtime):
    panel_w = GRID_WIDTH // 3
    panel_h = GRID_HEIGHT // 3

    # 3x3 grid showing parameter variations
    # Rows: different hurst values (roughness)
    # Cols: different lacunarity values

    hurst_values = [0.2, 0.5, 0.8]
    lacunarity_values = [1.5, 2.0, 3.0]

    for row, hurst in enumerate(hurst_values):
        for col, lacunarity in enumerate(lacunarity_values):
            ox = col * panel_w
            oy = row * panel_h

            # Create noise with these parameters
            noise = mcrfpy.NoiseSource(
                dimensions=2,
                algorithm='simplex',
                hurst=hurst,
                lacunarity=lacunarity,
                seed=42
            )

            # Sample using heightmap for efficiency
            hmap = noise.sample(
                size=(panel_w, panel_h),
                world_origin=(0, 0),
                world_size=(10, 10),
                mode='fbm',
                octaves=6
            )

            # Apply to color layer
            for y in range(panel_h):
                for x in range(panel_w):
                    h = hmap.get((x, y))
                    color_layer.set(((ox + x, oy + y)), value_to_gray(h))

            # Parameter label
            label = mcrfpy.Caption(
                text=f"H={hurst} L={lacunarity}",
                pos=(ox * CELL_SIZE + 3, oy * CELL_SIZE + 3)
            )
            label.fill_color = mcrfpy.Color(255, 255, 0)
            label.outline = 1
            label.outline_color = mcrfpy.Color(0, 0, 0)
            scene.children.append(label)

    # Row/Column labels
    row_labels = ["Low Hurst (rough)", "Mid Hurst (natural)", "High Hurst (smooth)"]
    for row, text in enumerate(row_labels):
        label = mcrfpy.Caption(text=text, pos=(5, row * panel_h * CELL_SIZE + panel_h * CELL_SIZE - 20))
        label.fill_color = mcrfpy.Color(255, 200, 100)
        label.outline = 1
        label.outline_color = mcrfpy.Color(0, 0, 0)
        scene.children.append(label)

    col_labels = ["Low Lacunarity", "Standard (2.0)", "High Lacunarity"]
    for col, text in enumerate(col_labels):
        label = mcrfpy.Caption(text=text, pos=(col * panel_w * CELL_SIZE + 5, GRID_HEIGHT * CELL_SIZE - 20))
        label.fill_color = mcrfpy.Color(100, 200, 255)
        label.outline = 1
        label.outline_color = mcrfpy.Color(0, 0, 0)
        scene.children.append(label)

    # Grid lines
    for y in range(GRID_HEIGHT):
        color_layer.set(((panel_w - 1, y)), mcrfpy.Color(100, 100, 100))
        color_layer.set(((panel_w * 2 - 1, y)), mcrfpy.Color(100, 100, 100))
    for x in range(GRID_WIDTH):
        color_layer.set(((x, panel_h - 1)), mcrfpy.Color(100, 100, 100))
        color_layer.set(((x, panel_h * 2 - 1)), mcrfpy.Color(100, 100, 100))


# Setup
scene = mcrfpy.Scene("noise_params_demo")

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
automation.screenshot("procgen_21_noise_parameters.png")
print("Screenshot saved: procgen_21_noise_parameters.png")
