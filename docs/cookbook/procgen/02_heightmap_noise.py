"""HeightMap Noise Integration Demo

Demonstrates: add_noise, multiply_noise with NoiseSource
Shows terrain generation using different noise modes (flat, fbm, turbulence).
"""
import mcrfpy
from mcrfpy import automation

GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def terrain_color(h):
    """Height-based terrain coloring."""
    if h < 0.25:
        # Water - deep to shallow blue
        t = h / 0.25
        return mcrfpy.Color(int(30 + t * 30), int(60 + t * 60), int(120 + t * 80))
    elif h < 0.35:
        # Beach/sand
        t = (h - 0.25) / 0.1
        return mcrfpy.Color(int(180 + t * 40), int(160 + t * 30), int(100 + t * 20))
    elif h < 0.6:
        # Grass - varies with height
        t = (h - 0.35) / 0.25
        return mcrfpy.Color(int(50 + t * 30), int(120 + t * 40), int(40 + t * 20))
    elif h < 0.75:
        # Forest/hills
        t = (h - 0.6) / 0.15
        return mcrfpy.Color(int(40 - t * 10), int(80 + t * 20), int(30 + t * 10))
    elif h < 0.88:
        # Rock/mountain
        t = (h - 0.75) / 0.13
        return mcrfpy.Color(int(100 + t * 40), int(90 + t * 40), int(80 + t * 40))
    else:
        # Snow peaks
        t = (h - 0.88) / 0.12
        return mcrfpy.Color(int(200 + t * 55), int(200 + t * 55), int(210 + t * 45))

def apply_to_layer(hmap, layer):
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            h = hmap.get((x, y))
            layer.set(x, y, terrain_color(h))

def run_demo(runtime):
    # Create three panels showing different noise modes
    panel_width = GRID_WIDTH // 3
    right_panel_width = GRID_WIDTH - 2 * panel_width  # Handle non-divisible widths

    # Create noise source with consistent seed
    noise = mcrfpy.NoiseSource(
        dimensions=2,
        algorithm='simplex',
        hurst=0.5,
        lacunarity=2.0,
        seed=42
    )

    # Left panel: Flat noise (single octave, raw)
    left_hmap = mcrfpy.HeightMap((panel_width, GRID_HEIGHT), fill=0.0)
    left_hmap.add_noise(noise, world_origin=(0, 0), world_size=(20, 20), mode='flat', octaves=1)
    left_hmap.normalize(0.0, 1.0)

    # Middle panel: FBM noise (fractal brownian motion - natural terrain)
    mid_hmap = mcrfpy.HeightMap((panel_width, GRID_HEIGHT), fill=0.0)
    mid_hmap.add_noise(noise, world_origin=(0, 0), world_size=(20, 20), mode='fbm', octaves=6)
    mid_hmap.normalize(0.0, 1.0)

    # Right panel: Turbulence (absolute value - clouds, marble)
    right_hmap = mcrfpy.HeightMap((right_panel_width, GRID_HEIGHT), fill=0.0)
    right_hmap.add_noise(noise, world_origin=(0, 0), world_size=(20, 20), mode='turbulence', octaves=6)
    right_hmap.normalize(0.0, 1.0)

    # Apply to color layer with panel divisions
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if x < panel_width:
                h = left_hmap.get((x, y))
            elif x < panel_width * 2:
                h = mid_hmap.get((x - panel_width, y))
            else:
                h = right_hmap.get((x - panel_width * 2, y))
            color_layer.set(((x, y)), terrain_color(h))

    # Add divider lines
    for y in range(GRID_HEIGHT):
        color_layer.set(((panel_width - 1, y)), mcrfpy.Color(255, 255, 255, 100))
        color_layer.set(((panel_width * 2 - 1, y)), mcrfpy.Color(255, 255, 255, 100))


# Setup scene
scene = mcrfpy.Scene("noise_demo")

grid = mcrfpy.Grid(
    grid_size=(GRID_WIDTH, GRID_HEIGHT),
    pos=(0, 0),
    size=(GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE),
    layers={}
)
grid.fill_color = mcrfpy.Color(0, 0, 0)
color_layer = grid.add_layer("color", z_index=-1)
scene.children.append(grid)

# Labels for each panel
labels = [
    ("FLAT (raw)", 10),
    ("FBM (terrain)", GRID_WIDTH * CELL_SIZE // 3 + 10),
    ("TURBULENCE (clouds)", GRID_WIDTH * CELL_SIZE * 2 // 3 + 10)
]
for text, x in labels:
    label = mcrfpy.Caption(text=text, pos=(x, 10))
    label.fill_color = mcrfpy.Color(255, 255, 255)
    label.outline = 1
    label.outline_color = mcrfpy.Color(0, 0, 0)
    scene.children.append(label)

scene.activate()

# Run the demo
run_demo(0)

# Take screenshot
automation.screenshot("procgen_02_heightmap_noise.png")
print("Screenshot saved: procgen_02_heightmap_noise.png")
