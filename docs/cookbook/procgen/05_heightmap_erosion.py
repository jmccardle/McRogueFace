"""HeightMap Erosion and Terrain Generation Demo

Demonstrates: rain_erosion, mid_point_displacement, smooth
Shows natural terrain formation through erosion simulation.
"""
import mcrfpy
from mcrfpy import automation

GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def terrain_color(h):
    """Natural terrain coloring."""
    if h < 0.2:
        # Deep water
        t = h / 0.2
        return mcrfpy.Color(int(20 + t * 30), int(40 + t * 40), int(100 + t * 55))
    elif h < 0.3:
        # Shallow water
        t = (h - 0.2) / 0.1
        return mcrfpy.Color(int(50 + t * 50), int(80 + t * 60), int(155 + t * 40))
    elif h < 0.35:
        # Beach
        t = (h - 0.3) / 0.05
        return mcrfpy.Color(int(194 - t * 30), int(178 - t * 30), int(128 - t * 20))
    elif h < 0.55:
        # Lowland grass
        t = (h - 0.35) / 0.2
        return mcrfpy.Color(int(80 + t * 20), int(140 - t * 30), int(60 + t * 10))
    elif h < 0.7:
        # Highland grass/forest
        t = (h - 0.55) / 0.15
        return mcrfpy.Color(int(50 + t * 30), int(100 + t * 10), int(40 + t * 20))
    elif h < 0.85:
        # Rock
        t = (h - 0.7) / 0.15
        return mcrfpy.Color(int(100 + t * 30), int(95 + t * 30), int(85 + t * 35))
    else:
        # Snow
        t = (h - 0.85) / 0.15
        return mcrfpy.Color(int(180 + t * 75), int(185 + t * 70), int(190 + t * 65))

def run_demo(runtime):
    panel_w = GRID_WIDTH // 3
    panel_h = GRID_HEIGHT // 2

    # Panel 1: Mid-point displacement (raw)
    mpd_raw = mcrfpy.HeightMap((panel_w, panel_h), fill=0.5)
    mpd_raw.mid_point_displacement(roughness=0.6, seed=42)
    mpd_raw.normalize(0.0, 1.0)

    # Panel 2: Mid-point displacement + smoothing
    mpd_smooth = mcrfpy.HeightMap((panel_w, panel_h), fill=0.5)
    mpd_smooth.mid_point_displacement(roughness=0.6, seed=42)
    mpd_smooth.smooth(2)
    mpd_smooth.normalize(0.0, 1.0)

    # Panel 3: Mid-point + light erosion
    mpd_light_erode = mcrfpy.HeightMap((panel_w, panel_h), fill=0.5)
    mpd_light_erode.mid_point_displacement(roughness=0.6, seed=42)
    mpd_light_erode.rain_erosion(drops=1000, erosion=0.05, sedimentation=0.03, seed=42)
    mpd_light_erode.normalize(0.0, 1.0)

    # Panel 4: Noise-based + moderate erosion
    noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=123)
    noise_erode = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    noise_erode.add_noise(noise, world_size=(12, 12), mode='fbm', octaves=5)
    noise_erode.add_hill((panel_w // 2, panel_h // 2), 10, 0.4)
    noise_erode.rain_erosion(drops=3000, erosion=0.1, sedimentation=0.05, seed=42)
    noise_erode.normalize(0.0, 1.0)

    # Panel 5: Heavy erosion (river valleys)
    heavy_erode = mcrfpy.HeightMap((panel_w, panel_h), fill=0.5)
    heavy_erode.mid_point_displacement(roughness=0.7, seed=99)
    heavy_erode.rain_erosion(drops=8000, erosion=0.15, sedimentation=0.02, seed=42)
    heavy_erode.normalize(0.0, 1.0)

    # Panel 6: Extreme erosion (canyon-like)
    extreme_erode = mcrfpy.HeightMap((panel_w, panel_h), fill=0.5)
    extreme_erode.mid_point_displacement(roughness=0.5, seed=77)
    extreme_erode.rain_erosion(drops=15000, erosion=0.2, sedimentation=0.01, seed=42)
    extreme_erode.smooth(1)
    extreme_erode.normalize(0.0, 1.0)

    # Apply to grid
    panels = [
        (mpd_raw, 0, 0, "MPD Raw"),
        (mpd_smooth, panel_w, 0, "MPD + Smooth"),
        (mpd_light_erode, panel_w * 2, 0, "Light Erosion"),
        (noise_erode, 0, panel_h, "Noise + Erosion"),
        (heavy_erode, panel_w, panel_h, "Heavy Erosion"),
        (extreme_erode, panel_w * 2, panel_h, "Extreme Erosion"),
    ]

    for hmap, ox, oy, name in panels:
        for y in range(panel_h):
            for x in range(panel_w):
                h = hmap.get((x, y))
                color_layer.set(((ox + x, oy + y)), terrain_color(h))

        label = mcrfpy.Caption(text=name, pos=(ox * CELL_SIZE + 5, oy * CELL_SIZE + 5))
        label.fill_color = mcrfpy.Color(255, 255, 255)
        label.outline = 1
        label.outline_color = mcrfpy.Color(0, 0, 0)
        scene.children.append(label)

    # Grid lines
    for y in range(GRID_HEIGHT):
        color_layer.set(((panel_w - 1, y)), mcrfpy.Color(80, 80, 80))
        color_layer.set(((panel_w * 2 - 1, y)), mcrfpy.Color(80, 80, 80))
    for x in range(GRID_WIDTH):
        color_layer.set(((x, panel_h - 1)), mcrfpy.Color(80, 80, 80))


# Setup
scene = mcrfpy.Scene("erosion_demo")

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
automation.screenshot("procgen_05_heightmap_erosion.png")
print("Screenshot saved: procgen_05_heightmap_erosion.png")
