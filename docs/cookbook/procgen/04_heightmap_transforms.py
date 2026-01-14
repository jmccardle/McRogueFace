"""HeightMap Transform Operations Demo

Demonstrates: scale, clamp, normalize, smooth, kernel_transform
Shows value manipulation and convolution effects.
"""
import mcrfpy
from mcrfpy import automation

GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def value_to_color(h):
    """Grayscale with enhanced contrast."""
    h = max(0.0, min(1.0, h))
    v = int(h * 255)
    return mcrfpy.Color(v, v, v)

def run_demo(runtime):
    # Create 6 panels showing different transforms
    panel_w = GRID_WIDTH // 3
    panel_h = GRID_HEIGHT // 2

    # Source noise
    noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=42)

    # Create base terrain with features
    base = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    base.add_noise(noise, world_size=(8, 8), mode='fbm', octaves=4)
    base.add_hill((panel_w // 2, panel_h // 2), 8, 0.5)
    base.normalize(0.0, 1.0)

    # Panel 1: Original
    original = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    original.copy_from(base)

    # Panel 2: SCALE (amplify contrast)
    scaled = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    scaled.copy_from(base).add_constant(-0.5).scale(2.0).clamp(0.0, 1.0)

    # Panel 3: CLAMP (plateau effect)
    clamped = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    clamped.copy_from(base).clamp(0.3, 0.7).normalize(0.0, 1.0)

    # Panel 4: SMOOTH (blur/average)
    smoothed = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    smoothed.copy_from(base).smooth(3)

    # Panel 5: SHARPEN kernel
    sharpened = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    sharpened.copy_from(base)
    sharpen_kernel = {
        (0, -1): -1.0, (-1, 0): -1.0, (0, 0): 5.0, (1, 0): -1.0, (0, 1): -1.0
    }
    sharpened.kernel_transform(sharpen_kernel).clamp(0.0, 1.0)

    # Panel 6: EDGE DETECTION kernel
    edges = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    edges.copy_from(base)
    edge_kernel = {
        (-1, -1): -1, (0, -1): -1, (1, -1): -1,
        (-1,  0): -1, (0,  0):  8, (1,  0): -1,
        (-1,  1): -1, (0,  1): -1, (1,  1): -1,
    }
    edges.kernel_transform(edge_kernel).normalize(0.0, 1.0)

    # Apply to grid
    panels = [
        (original, 0, 0, "ORIGINAL"),
        (scaled, panel_w, 0, "SCALE (contrast)"),
        (clamped, panel_w * 2, 0, "CLAMP (plateau)"),
        (smoothed, 0, panel_h, "SMOOTH (blur)"),
        (sharpened, panel_w, panel_h, "SHARPEN kernel"),
        (edges, panel_w * 2, panel_h, "EDGE DETECT"),
    ]

    for hmap, ox, oy, name in panels:
        for y in range(panel_h):
            for x in range(panel_w):
                h = hmap.get((x, y))
                color_layer.set(((ox + x, oy + y)), value_to_color(h))

        label = mcrfpy.Caption(text=name, pos=(ox * CELL_SIZE + 5, oy * CELL_SIZE + 5))
        label.fill_color = mcrfpy.Color(255, 255, 0)
        label.outline = 1
        label.outline_color = mcrfpy.Color(0, 0, 0)
        scene.children.append(label)

    # Grid lines
    for y in range(GRID_HEIGHT):
        color_layer.set(((panel_w - 1, y)), mcrfpy.Color(100, 100, 100))
        color_layer.set(((panel_w * 2 - 1, y)), mcrfpy.Color(100, 100, 100))
    for x in range(GRID_WIDTH):
        color_layer.set(((x, panel_h - 1)), mcrfpy.Color(100, 100, 100))


# Setup
scene = mcrfpy.Scene("transforms_demo")

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
automation.screenshot("procgen_04_heightmap_transforms.png")
print("Screenshot saved: procgen_04_heightmap_transforms.png")
