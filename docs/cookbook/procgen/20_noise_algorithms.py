"""NoiseSource Algorithms Demo

Demonstrates: simplex, perlin, wavelet noise algorithms
Shows visual differences between noise types.
"""
import mcrfpy
from mcrfpy import automation

GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def value_to_terrain(h):
    """Convert noise value (-1 to 1) to terrain color."""
    # Normalize from -1..1 to 0..1
    h = (h + 1) / 2
    h = max(0.0, min(1.0, h))

    if h < 0.3:
        t = h / 0.3
        return mcrfpy.Color(int(30 + t * 40), int(60 + t * 60), int(140 + t * 40))
    elif h < 0.45:
        t = (h - 0.3) / 0.15
        return mcrfpy.Color(int(70 + t * 120), int(120 + t * 60), int(100 - t * 60))
    elif h < 0.6:
        t = (h - 0.45) / 0.15
        return mcrfpy.Color(int(60 + t * 20), int(130 + t * 20), int(50 + t * 10))
    elif h < 0.75:
        t = (h - 0.6) / 0.15
        return mcrfpy.Color(int(50 + t * 50), int(110 - t * 20), int(40 + t * 20))
    elif h < 0.88:
        t = (h - 0.75) / 0.13
        return mcrfpy.Color(int(100 + t * 40), int(95 + t * 35), int(80 + t * 40))
    else:
        t = (h - 0.88) / 0.12
        return mcrfpy.Color(int(180 + t * 70), int(180 + t * 70), int(190 + t * 60))

def run_demo(runtime):
    panel_w = GRID_WIDTH // 3
    panel_h = GRID_HEIGHT // 2

    algorithms = [
        ('simplex', "SIMPLEX", "Fast, no visible artifacts"),
        ('perlin', "PERLIN", "Classic, slight grid bias"),
        ('wavelet', "WAVELET", "Smooth, no tiling"),
    ]

    # Top row: FBM (natural terrain)
    # Bottom row: Raw noise (single octave)
    for col, (algo, name, desc) in enumerate(algorithms):
        ox = col * panel_w

        # Create noise source
        noise = mcrfpy.NoiseSource(
            dimensions=2,
            algorithm=algo,
            hurst=0.5,
            lacunarity=2.0,
            seed=42
        )

        # Top panel: FBM
        for y in range(panel_h):
            for x in range(panel_w):
                # Sample at world coordinates
                wx = x * 0.15
                wy = y * 0.15
                val = noise.fbm((wx, wy), octaves=5)
                color_layer.set(((ox + x, y)), value_to_terrain(val))

        # Bottom panel: Raw (flat)
        for y in range(panel_h):
            for x in range(panel_w):
                wx = x * 0.15
                wy = y * 0.15
                val = noise.get((wx, wy))
                color_layer.set(((ox + x, panel_h + y)), value_to_terrain(val))

        # Labels
        top_label = mcrfpy.Caption(text=f"{name} (FBM)", pos=(ox * CELL_SIZE + 5, 5))
        top_label.fill_color = mcrfpy.Color(255, 255, 255)
        top_label.outline = 1
        top_label.outline_color = mcrfpy.Color(0, 0, 0)
        scene.children.append(top_label)

        bottom_label = mcrfpy.Caption(text=f"{name} (raw)", pos=(ox * CELL_SIZE + 5, panel_h * CELL_SIZE + 5))
        bottom_label.fill_color = mcrfpy.Color(255, 255, 255)
        bottom_label.outline = 1
        bottom_label.outline_color = mcrfpy.Color(0, 0, 0)
        scene.children.append(bottom_label)

        desc_label = mcrfpy.Caption(text=desc, pos=(ox * CELL_SIZE + 5, 22))
        desc_label.fill_color = mcrfpy.Color(200, 200, 200)
        desc_label.outline = 1
        desc_label.outline_color = mcrfpy.Color(0, 0, 0)
        scene.children.append(desc_label)

    # Grid lines
    for y in range(GRID_HEIGHT):
        color_layer.set(((panel_w - 1, y)), mcrfpy.Color(80, 80, 80))
        color_layer.set(((panel_w * 2 - 1, y)), mcrfpy.Color(80, 80, 80))
    for x in range(GRID_WIDTH):
        color_layer.set(((x, panel_h - 1)), mcrfpy.Color(80, 80, 80))


# Setup
scene = mcrfpy.Scene("noise_algo_demo")

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
automation.screenshot("procgen_20_noise_algorithms.png")
print("Screenshot saved: procgen_20_noise_algorithms.png")
