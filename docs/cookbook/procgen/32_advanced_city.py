"""Advanced: Procedural City Map

Combines: BSP (city blocks/buildings) + Noise (terrain/parks) + Voronoi (districts)
Creates a city map with districts, buildings, roads, and parks.
"""
import mcrfpy
from mcrfpy import automation

GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def run_demo(runtime):
    # Step 1: Create district map using voronoi
    districts = mcrfpy.HeightMap((GRID_WIDTH, GRID_HEIGHT), fill=0.0)
    districts.add_voronoi(num_points=6, coefficients=(1.0, 0.0), seed=42)
    districts.normalize(0.0, 1.0)

    # District types based on value
    # 0.0-0.2: Residential (green-ish)
    # 0.2-0.4: Commercial (blue-ish)
    # 0.4-0.6: Industrial (gray)
    # 0.6-0.8: Park/nature
    # 0.8-1.0: Downtown (tall buildings)

    # Step 2: Create building blocks using BSP
    bsp = mcrfpy.BSP(pos=(1, 1), size=(GRID_WIDTH - 2, GRID_HEIGHT - 2))
    bsp.split_recursive(depth=4, min_size=(6, 5), max_ratio=2.0, seed=42)

    # Step 3: Create park areas using noise
    noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=99)
    parks = mcrfpy.HeightMap((GRID_WIDTH, GRID_HEIGHT), fill=0.0)
    parks.add_noise(noise, world_size=(8, 8), mode='fbm', octaves=3)
    parks.normalize(0.0, 1.0)

    # Step 4: Render base (roads)
    color_layer.fill(mcrfpy.Color(60, 60, 65))  # Asphalt

    # Step 5: Draw buildings based on BSP and district type
    for leaf in bsp.leaves():
        pos = leaf.pos
        size = leaf.size
        cx, cy = leaf.center()

        # Get district type at center
        district_val = districts.get((cx, cy))

        # Shrink for roads between buildings
        shrink = 1

        # Determine building style based on district
        if district_val < 0.2:
            # Residential
            building_color = mcrfpy.Color(140, 160, 140)
            roof_color = mcrfpy.Color(160, 100, 80)
            shrink = 2  # More space between houses
        elif district_val < 0.4:
            # Commercial
            building_color = mcrfpy.Color(120, 140, 170)
            roof_color = mcrfpy.Color(80, 100, 130)
        elif district_val < 0.6:
            # Industrial
            building_color = mcrfpy.Color(100, 100, 105)
            roof_color = mcrfpy.Color(70, 70, 75)
        elif district_val < 0.8:
            # Park area - check noise for actual park placement
            park_val = parks.get((cx, cy))
            if park_val > 0.4:
                # This block is a park
                for y in range(pos[1] + 1, pos[1] + size[1] - 1):
                    for x in range(pos[0] + 1, pos[0] + size[0] - 1):
                        t = parks.get((x, y))
                        if t > 0.6:
                            color_layer.set(((x, y)), mcrfpy.Color(50, 120, 50))  # Trees
                        else:
                            color_layer.set(((x, y)), mcrfpy.Color(80, 150, 80))  # Grass
                continue
            else:
                building_color = mcrfpy.Color(130, 150, 130)
                roof_color = mcrfpy.Color(100, 80, 70)
        else:
            # Downtown
            building_color = mcrfpy.Color(150, 155, 165)
            roof_color = mcrfpy.Color(90, 95, 110)
            shrink = 1  # Dense buildings

        # Draw building
        for y in range(pos[1] + shrink, pos[1] + size[1] - shrink):
            for x in range(pos[0] + shrink, pos[0] + size[0] - shrink):
                # Building edge (roof)
                if y == pos[1] + shrink or y == pos[1] + size[1] - shrink - 1:
                    color_layer.set(((x, y)), roof_color)
                elif x == pos[0] + shrink or x == pos[0] + size[0] - shrink - 1:
                    color_layer.set(((x, y)), roof_color)
                else:
                    color_layer.set(((x, y)), building_color)

    # Step 6: Add main roads (cross the city)
    road_color = mcrfpy.Color(70, 70, 75)
    marking_color = mcrfpy.Color(200, 200, 100)

    # Horizontal main road
    main_y = GRID_HEIGHT // 2
    for x in range(GRID_WIDTH):
        for dy in range(-1, 2):
            if 0 <= main_y + dy < GRID_HEIGHT:
                color_layer.set(((x, main_y + dy)), road_color)
        # Road markings
        if x % 4 == 0:
            color_layer.set(((x, main_y)), marking_color)

    # Vertical main road
    main_x = GRID_WIDTH // 2
    for y in range(GRID_HEIGHT):
        for dx in range(-1, 2):
            if 0 <= main_x + dx < GRID_WIDTH:
                color_layer.set(((main_x + dx, y)), road_color)
        if y % 4 == 0:
            color_layer.set(((main_x, y)), marking_color)

    # Intersection
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            color_layer.set(((main_x + dx, main_y + dy)), road_color)

    # Step 7: Add a central plaza
    plaza_x, plaza_y = main_x, main_y
    for dy in range(-3, 4):
        for dx in range(-4, 5):
            nx, ny = plaza_x + dx, plaza_y + dy
            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                if abs(dx) <= 1 and abs(dy) <= 1:
                    color_layer.set(((nx, ny)), mcrfpy.Color(180, 160, 140))  # Fountain
                else:
                    color_layer.set(((nx, ny)), mcrfpy.Color(160, 150, 140))  # Plaza tiles

    # Title
    title = mcrfpy.Caption(text="Procedural City: BSP + Voronoi Districts + Noise Parks", pos=(10, 10))
    title.fill_color = mcrfpy.Color(255, 255, 255)
    title.outline = 1
    title.outline_color = mcrfpy.Color(0, 0, 0)
    scene.children.append(title)


# Setup
scene = mcrfpy.Scene("city")

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
automation.screenshot("procgen_32_advanced_city.png")
print("Screenshot saved: procgen_32_advanced_city.png")
