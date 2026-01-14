"""Advanced: Island Terrain Generation

Combines: Noise (base terrain) + Voronoi (biomes) + Hills + Erosion + Bezier (rivers)
Creates a tropical island with varied biomes and water features.
"""
import mcrfpy
from mcrfpy import automation

GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def biome_color(elevation, moisture):
    """Determine color based on elevation and moisture."""
    if elevation < 0.25:
        # Water
        t = elevation / 0.25
        return mcrfpy.Color(int(30 + t * 30), int(80 + t * 40), int(160 + t * 40))
    elif elevation < 0.32:
        # Beach
        return mcrfpy.Color(220, 200, 150)
    elif elevation < 0.5:
        # Lowland - varies by moisture
        if moisture < 0.3:
            return mcrfpy.Color(180, 170, 110)  # Desert/savanna
        elif moisture < 0.6:
            return mcrfpy.Color(80, 140, 60)    # Grassland
        else:
            return mcrfpy.Color(40, 100, 50)    # Rainforest
    elif elevation < 0.7:
        # Highland
        if moisture < 0.4:
            return mcrfpy.Color(100, 90, 70)    # Dry hills
        else:
            return mcrfpy.Color(50, 90, 45)     # Forest
    elif elevation < 0.85:
        # Mountain
        return mcrfpy.Color(110, 105, 100)
    else:
        # Peak
        return mcrfpy.Color(220, 225, 230)

def run_demo(runtime):
    # Step 1: Create base elevation using noise
    noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=42)

    elevation = mcrfpy.HeightMap((GRID_WIDTH, GRID_HEIGHT), fill=0.0)
    elevation.add_noise(noise, world_size=(12, 10), mode='fbm', octaves=5)
    elevation.normalize(0.0, 1.0)

    # Step 2: Create island shape using radial falloff
    cx, cy = GRID_WIDTH / 2, GRID_HEIGHT / 2
    max_dist = min(cx, cy) * 0.85

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            falloff = max(0, 1 - (dist / max_dist) ** 1.5)
            current = elevation.get((x, y))
            elevation.fill(current * falloff, pos=(x, y), size=(1, 1))

    # Step 3: Add central mountain range
    elevation.add_hill((GRID_WIDTH // 2, GRID_HEIGHT // 2), 15, 0.5)
    elevation.add_hill((GRID_WIDTH // 2 - 8, GRID_HEIGHT // 2 + 3), 8, 0.3)
    elevation.add_hill((GRID_WIDTH // 2 + 10, GRID_HEIGHT // 2 - 5), 6, 0.25)

    # Step 4: Create moisture map using different noise
    moisture_noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=123)
    moisture = mcrfpy.HeightMap((GRID_WIDTH, GRID_HEIGHT), fill=0.0)
    moisture.add_noise(moisture_noise, world_size=(8, 8), mode='fbm', octaves=3)
    moisture.normalize(0.0, 1.0)

    # Step 5: Add voronoi for biome boundaries
    biome_regions = mcrfpy.HeightMap((GRID_WIDTH, GRID_HEIGHT), fill=0.0)
    biome_regions.add_voronoi(num_points=8, coefficients=(0.5, -0.3), seed=77)
    biome_regions.normalize(0.0, 1.0)

    # Blend voronoi into moisture
    moisture.lerp(biome_regions, 0.4)

    # Step 6: Apply erosion to elevation
    elevation.rain_erosion(drops=2000, erosion=0.08, sedimentation=0.04, seed=42)
    elevation.normalize(0.0, 1.0)

    # Step 7: Carve rivers from mountains to sea
    # Main river
    elevation.dig_bezier(
        points=((GRID_WIDTH // 2, GRID_HEIGHT // 2 - 5),
                (GRID_WIDTH // 2 - 10, GRID_HEIGHT // 2),
                (GRID_WIDTH // 4, GRID_HEIGHT // 2 + 5),
                (5, GRID_HEIGHT // 2 + 8)),
        start_radius=0.5, end_radius=2,
        start_height=0.3, end_height=0.15
    )

    # Secondary river
    elevation.dig_bezier(
        points=((GRID_WIDTH // 2 + 5, GRID_HEIGHT // 2),
                (GRID_WIDTH // 2 + 15, GRID_HEIGHT // 3),
                (GRID_WIDTH - 15, GRID_HEIGHT // 4),
                (GRID_WIDTH - 5, GRID_HEIGHT // 4 + 3)),
        start_radius=0.5, end_radius=1.5,
        start_height=0.32, end_height=0.18
    )

    # Step 8: Render
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            elev = elevation.get((x, y))
            moist = moisture.get((x, y))
            color_layer.set(((x, y)), biome_color(elev, moist))

    # Title
    title = mcrfpy.Caption(text="Island Terrain: Noise + Voronoi + Hills + Erosion + Rivers", pos=(10, 10))
    title.fill_color = mcrfpy.Color(255, 255, 255)
    title.outline = 1
    title.outline_color = mcrfpy.Color(0, 0, 0)
    scene.children.append(title)


# Setup
scene = mcrfpy.Scene("island")

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
automation.screenshot("procgen_31_advanced_island.png")
print("Screenshot saved: procgen_31_advanced_island.png")
