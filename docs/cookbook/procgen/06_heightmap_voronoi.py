"""HeightMap Voronoi Demo

Demonstrates: add_voronoi with different coefficients
Shows cell-based patterns useful for biomes, regions, and organic structures.
"""
import mcrfpy
from mcrfpy import automation

GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def biome_color(h):
    """Color cells as distinct biomes."""
    # Use value ranges to create distinct regions
    h = max(0.0, min(1.0, h))

    if h < 0.15:
        return mcrfpy.Color(30, 60, 120)   # Deep water
    elif h < 0.25:
        return mcrfpy.Color(50, 100, 180)  # Shallow water
    elif h < 0.35:
        return mcrfpy.Color(194, 178, 128) # Beach/desert
    elif h < 0.5:
        return mcrfpy.Color(80, 160, 60)   # Grassland
    elif h < 0.65:
        return mcrfpy.Color(40, 100, 40)   # Forest
    elif h < 0.8:
        return mcrfpy.Color(100, 80, 60)   # Hills
    elif h < 0.9:
        return mcrfpy.Color(130, 130, 130) # Mountains
    else:
        return mcrfpy.Color(240, 240, 250) # Snow

def cell_edges_color(h):
    """Highlight cell boundaries."""
    h = max(0.0, min(1.0, h))
    if h < 0.3:
        return mcrfpy.Color(40, 40, 60)
    elif h < 0.6:
        return mcrfpy.Color(80, 80, 100)
    else:
        return mcrfpy.Color(200, 200, 220)

def run_demo(runtime):
    panel_w = GRID_WIDTH // 3
    panel_h = GRID_HEIGHT // 2

    # Panel 1: Standard Voronoi (cell centers high)
    # coefficients (1, 0) = distance to nearest point
    v_standard = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    v_standard.add_voronoi(num_points=15, coefficients=(1.0, 0.0), seed=42)
    v_standard.normalize(0.0, 1.0)

    # Panel 2: Inverted (cell centers low, edges high)
    # coefficients (-1, 0) = inverted distance
    v_inverted = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    v_inverted.add_voronoi(num_points=15, coefficients=(-1.0, 0.0), seed=42)
    v_inverted.normalize(0.0, 1.0)

    # Panel 3: Cell difference (creates ridges)
    # coefficients (1, -1) = distance to nearest - distance to second nearest
    v_ridges = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    v_ridges.add_voronoi(num_points=15, coefficients=(1.0, -1.0), seed=42)
    v_ridges.normalize(0.0, 1.0)

    # Panel 4: Few large cells (biome-scale)
    v_biomes = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    v_biomes.add_voronoi(num_points=6, coefficients=(1.0, -0.3), seed=99)
    v_biomes.normalize(0.0, 1.0)

    # Panel 5: Many small cells (texture-scale)
    v_texture = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    v_texture.add_voronoi(num_points=50, coefficients=(1.0, -0.5), seed=77)
    v_texture.normalize(0.0, 1.0)

    # Panel 6: Voronoi + noise blend (natural regions)
    noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=42)
    v_natural = mcrfpy.HeightMap((panel_w, panel_h), fill=0.0)
    v_natural.add_voronoi(num_points=12, coefficients=(0.8, -0.4), seed=42)
    v_natural.add_noise(noise, world_size=(15, 15), mode='fbm', octaves=3, scale=0.3)
    v_natural.normalize(0.0, 1.0)

    # Apply to grid
    panels = [
        (v_standard, 0, 0, "Standard (1,0)", biome_color),
        (v_inverted, panel_w, 0, "Inverted (-1,0)", biome_color),
        (v_ridges, panel_w * 2, 0, "Ridges (1,-1)", cell_edges_color),
        (v_biomes, 0, panel_h, "Biomes (6 pts)", biome_color),
        (v_texture, panel_w, panel_h, "Texture (50 pts)", cell_edges_color),
        (v_natural, panel_w * 2, panel_h, "Voronoi + Noise", biome_color),
    ]

    for hmap, ox, oy, name, color_func in panels:
        for y in range(panel_h):
            for x in range(panel_w):
                h = hmap.get((x, y))
                color_layer.set(((ox + x, oy + y)), color_func(h))

        label = mcrfpy.Caption(text=name, pos=(ox * CELL_SIZE + 5, oy * CELL_SIZE + 5))
        label.fill_color = mcrfpy.Color(255, 255, 255)
        label.outline = 1
        label.outline_color = mcrfpy.Color(0, 0, 0)
        scene.children.append(label)

    # Grid lines
    for y in range(GRID_HEIGHT):
        color_layer.set(((panel_w - 1, y)), mcrfpy.Color(60, 60, 60))
        color_layer.set(((panel_w * 2 - 1, y)), mcrfpy.Color(60, 60, 60))
    for x in range(GRID_WIDTH):
        color_layer.set(((x, panel_h - 1)), mcrfpy.Color(60, 60, 60))


# Setup
scene = mcrfpy.Scene("voronoi_demo")

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
automation.screenshot("procgen_06_heightmap_voronoi.png")
print("Screenshot saved: procgen_06_heightmap_voronoi.png")
