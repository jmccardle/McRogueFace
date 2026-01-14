"""Advanced: Volcanic Crater Region

Combines: Hills (mountains) + dig_hill (craters) + Voronoi (lava flows) + Erosion + Noise
Creates a volcanic landscape with active lava, ash fields, and rocky terrain.
"""
import mcrfpy
from mcrfpy import automation

GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def volcanic_color(elevation, lava_intensity, ash_level):
    """Color based on elevation, lava presence, and ash coverage."""
    # Lava overrides everything
    if lava_intensity > 0.6:
        t = (lava_intensity - 0.6) / 0.4
        return mcrfpy.Color(
            int(200 + t * 55),
            int(80 + t * 80),
            int(20 + t * 30)
        )
    elif lava_intensity > 0.4:
        # Cooling lava
        t = (lava_intensity - 0.4) / 0.2
        return mcrfpy.Color(
            int(80 + t * 120),
            int(30 + t * 50),
            int(20)
        )

    # Check for crater interior (very low elevation)
    if elevation < 0.15:
        t = elevation / 0.15
        return mcrfpy.Color(int(40 + t * 30), int(20 + t * 20), int(10 + t * 15))

    # Ash coverage
    if ash_level > 0.6:
        t = (ash_level - 0.6) / 0.4
        base = int(60 + t * 40)
        return mcrfpy.Color(base, base - 5, base - 10)

    # Normal terrain by elevation
    if elevation < 0.3:
        # Volcanic plain
        t = (elevation - 0.15) / 0.15
        return mcrfpy.Color(int(50 + t * 30), int(40 + t * 25), int(35 + t * 20))
    elif elevation < 0.5:
        # Rocky slopes
        t = (elevation - 0.3) / 0.2
        return mcrfpy.Color(int(70 + t * 20), int(60 + t * 15), int(50 + t * 15))
    elif elevation < 0.7:
        # Mountain sides
        t = (elevation - 0.5) / 0.2
        return mcrfpy.Color(int(85 + t * 25), int(75 + t * 20), int(65 + t * 20))
    elif elevation < 0.85:
        # High slopes
        t = (elevation - 0.7) / 0.15
        return mcrfpy.Color(int(100 + t * 30), int(90 + t * 25), int(80 + t * 25))
    else:
        # Peaks
        t = (elevation - 0.85) / 0.15
        return mcrfpy.Color(int(130 + t * 50), int(120 + t * 50), int(115 + t * 50))

def run_demo(runtime):
    # Step 1: Create base terrain with noise
    noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=42)

    terrain = mcrfpy.HeightMap((GRID_WIDTH, GRID_HEIGHT), fill=0.3)
    terrain.add_noise(noise, world_size=(12, 10), mode='fbm', octaves=4, scale=0.2)

    # Step 2: Add volcanic mountains
    # Main volcano
    terrain.add_hill((GRID_WIDTH // 2, GRID_HEIGHT // 2), 20, 0.7)
    terrain.add_hill((GRID_WIDTH // 2, GRID_HEIGHT // 2), 12, 0.3)  # Steep peak

    # Secondary volcanoes
    terrain.add_hill((15, 15), 10, 0.4)
    terrain.add_hill((GRID_WIDTH - 12, GRID_HEIGHT - 15), 8, 0.35)
    terrain.add_hill((10, GRID_HEIGHT - 10), 6, 0.25)

    # Step 3: Create craters
    terrain.dig_hill((GRID_WIDTH // 2, GRID_HEIGHT // 2), 6, 0.1)  # Main crater
    terrain.dig_hill((15, 15), 4, 0.15)  # Secondary crater
    terrain.dig_hill((GRID_WIDTH - 12, GRID_HEIGHT - 15), 3, 0.18)  # Third crater

    # Step 4: Create lava flow pattern using voronoi
    lava = mcrfpy.HeightMap((GRID_WIDTH, GRID_HEIGHT), fill=0.0)
    lava.add_voronoi(num_points=12, coefficients=(1.0, -0.8), seed=77)
    lava.normalize(0.0, 1.0)

    # Lava originates from craters - enhance around crater centers
    lava.add_hill((GRID_WIDTH // 2, GRID_HEIGHT // 2), 8, 0.5)
    lava.add_hill((15, 15), 5, 0.3)

    # Lava flows downhill - multiply by inverted terrain
    terrain_inv = terrain.inverse()
    terrain_inv.normalize(0.0, 1.0)
    lava.multiply(terrain_inv)
    lava.normalize(0.0, 1.0)

    # Step 5: Create ash distribution using noise
    ash_noise = mcrfpy.NoiseSource(dimensions=2, algorithm='perlin', seed=123)
    ash = mcrfpy.HeightMap((GRID_WIDTH, GRID_HEIGHT), fill=0.0)
    ash.add_noise(ash_noise, world_size=(8, 6), mode='turbulence', octaves=3)
    ash.normalize(0.0, 1.0)

    # Ash settles on lower areas
    ash.multiply(terrain_inv)

    # Step 6: Apply erosion for realistic channels
    terrain.rain_erosion(drops=1500, erosion=0.1, sedimentation=0.03, seed=42)
    terrain.normalize(0.0, 1.0)

    # Step 7: Add lava rivers from craters
    lava.dig_bezier(
        points=((GRID_WIDTH // 2, GRID_HEIGHT // 2 + 5),
                (GRID_WIDTH // 2 - 5, GRID_HEIGHT // 2 + 15),
                (GRID_WIDTH // 3, GRID_HEIGHT - 10),
                (10, GRID_HEIGHT - 5)),
        start_radius=2, end_radius=3,
        start_height=0.9, end_height=0.7
    )

    lava.dig_bezier(
        points=((GRID_WIDTH // 2 + 3, GRID_HEIGHT // 2 + 3),
                (GRID_WIDTH // 2 + 15, GRID_HEIGHT // 2 + 8),
                (GRID_WIDTH - 15, GRID_HEIGHT // 2 + 5),
                (GRID_WIDTH - 5, GRID_HEIGHT // 2 + 10)),
        start_radius=1.5, end_radius=2.5,
        start_height=0.85, end_height=0.65
    )

    # Step 8: Render
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            elev = terrain.get((x, y))
            lava_val = lava.get((x, y))
            ash_val = ash.get((x, y))

            color_layer.set(((x, y)), volcanic_color(elev, lava_val, ash_val))

    # Add smoke/steam particles around crater rims
    crater_centers = [
        (GRID_WIDTH // 2, GRID_HEIGHT // 2, 6),
        (15, 15, 4),
        (GRID_WIDTH - 12, GRID_HEIGHT - 15, 3)
    ]

    import math
    for cx, cy, radius in crater_centers:
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            px = int(cx + math.cos(rad) * radius)
            py = int(cy + math.sin(rad) * radius)
            if 0 <= px < GRID_WIDTH and 0 <= py < GRID_HEIGHT:
                # Smoke color
                color_layer.set(((px, py)), mcrfpy.Color(150, 140, 130, 180))

    # Title
    title = mcrfpy.Caption(text="Volcanic Region: Hills + Craters + Voronoi Lava + Erosion", pos=(10, 10))
    title.fill_color = mcrfpy.Color(255, 255, 255)
    title.outline = 1
    title.outline_color = mcrfpy.Color(0, 0, 0)
    scene.children.append(title)


# Setup
scene = mcrfpy.Scene("volcanic")

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
automation.screenshot("procgen_34_advanced_volcanic.png")
print("Screenshot saved: procgen_34_advanced_volcanic.png")
