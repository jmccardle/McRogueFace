"""Advanced: Natural Cave System

Combines: Noise (cave formation) + Threshold (open areas) + Kernel (smoothing) + BSP (structured areas)
Creates organic cave networks with some structured rooms.
"""
import mcrfpy
from mcrfpy import automation

GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def run_demo(runtime):
    # Step 1: Generate cave base using turbulent noise
    noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=42)

    cave_noise = mcrfpy.HeightMap((GRID_WIDTH, GRID_HEIGHT), fill=0.0)
    cave_noise.add_noise(noise, world_size=(10, 8), mode='turbulence', octaves=4)
    cave_noise.normalize(0.0, 1.0)

    # Step 2: Create cave mask via threshold
    # Values > 0.45 become open cave, rest is rock
    cave_mask = cave_noise.threshold_binary((0.4, 1.0), 1.0)

    # Step 3: Apply smoothing kernel to remove isolated pixels
    smooth_kernel = {
        (-1, -1): 1, (0, -1): 2, (1, -1): 1,
        (-1,  0): 2, (0,  0): 4, (1,  0): 2,
        (-1,  1): 1, (0,  1): 2, (1,  1): 1,
    }
    cave_mask.kernel_transform(smooth_kernel)
    cave_mask.normalize(0.0, 1.0)

    # Re-threshold after smoothing
    cave_mask = cave_mask.threshold_binary((0.5, 1.0), 1.0)

    # Step 4: Add some structured rooms using BSP in one corner
    # This represents ancient ruins within the caves
    bsp = mcrfpy.BSP(pos=(GRID_WIDTH - 22, GRID_HEIGHT - 18), size=(18, 14))
    bsp.split_recursive(depth=2, min_size=(6, 5), seed=42)

    ruins_hmap = bsp.to_heightmap(
        size=(GRID_WIDTH, GRID_HEIGHT),
        select='leaves',
        shrink=1,
        value=1.0
    )

    # Step 5: Combine caves and ruins
    combined = mcrfpy.HeightMap((GRID_WIDTH, GRID_HEIGHT), fill=0.0)
    combined.copy_from(cave_mask)
    combined.max(ruins_hmap)

    # Step 6: Add connecting tunnels from ruins to main cave
    # Find a cave entrance point
    tunnel_points = []
    for y in range(GRID_HEIGHT - 18, GRID_HEIGHT - 10):
        for x in range(GRID_WIDTH - 25, GRID_WIDTH - 20):
            if cave_mask.get((x, y)) > 0.5:
                tunnel_points.append((x, y))
                break
        if tunnel_points:
            break

    if tunnel_points:
        tx, ty = tunnel_points[0]
        # Carve tunnel to ruins entrance
        combined.dig_bezier(
            points=((tx, ty), (tx + 3, ty), (GRID_WIDTH - 22, ty + 2), (GRID_WIDTH - 20, GRID_HEIGHT - 15)),
            start_radius=1.5, end_radius=1.5,
            start_height=1.0, end_height=1.0
        )

    # Step 7: Add large cavern (central chamber)
    combined.add_hill((GRID_WIDTH // 3, GRID_HEIGHT // 2), 8, 0.6)

    # Step 8: Create water pools in low noise areas
    water_noise = mcrfpy.NoiseSource(dimensions=2, algorithm='perlin', seed=99)
    water_map = mcrfpy.HeightMap((GRID_WIDTH, GRID_HEIGHT), fill=0.0)
    water_map.add_noise(water_noise, world_size=(15, 12), mode='fbm', octaves=3)
    water_map.normalize(0.0, 1.0)

    # Step 9: Render
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            cave_val = combined.get((x, y))
            water_val = water_map.get((x, y))
            original_noise = cave_noise.get((x, y))

            # Check if in ruins area
            in_ruins = (x >= GRID_WIDTH - 22 and x < GRID_WIDTH - 4 and
                       y >= GRID_HEIGHT - 18 and y < GRID_HEIGHT - 4)

            if cave_val < 0.3:
                # Solid rock
                base = 30 + int(original_noise * 25)
                color_layer.set(((x, y)), mcrfpy.Color(base + 10, base + 5, base + 15))
            elif cave_val < 0.5:
                # Cave wall edge
                color_layer.set(((x, y)), mcrfpy.Color(45, 40, 50))
            else:
                # Open cave floor
                if water_val > 0.7 and not in_ruins:
                    # Water pool
                    t = (water_val - 0.7) / 0.3
                    color_layer.set(((x, y)), mcrfpy.Color(
                        int(30 + t * 20), int(50 + t * 30), int(100 + t * 50)
                    ))
                elif in_ruins and ruins_hmap.get((x, y)) > 0.5:
                    # Ruins floor (worked stone)
                    base = 85 + ((x + y) % 3) * 5
                    color_layer.set(((x, y)), mcrfpy.Color(base + 10, base + 5, base))
                else:
                    # Natural cave floor
                    base = 55 + int(original_noise * 20)
                    var = ((x * 3 + y * 5) % 8)
                    color_layer.set(((x, y)), mcrfpy.Color(base + var, base - 5 + var, base - 8))

    # Glowing fungi spots
    fungi_noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=777)
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if combined.get((x, y)) > 0.5:  # Only in open areas
                fungi_val = fungi_noise.get((x * 0.5, y * 0.5))
                if fungi_val > 0.8:
                    color_layer.set(((x, y)), mcrfpy.Color(80, 180, 120))

    # Border
    for x in range(GRID_WIDTH):
        color_layer.set(((x, 0)), mcrfpy.Color(20, 18, 25))
        color_layer.set(((x, GRID_HEIGHT - 1)), mcrfpy.Color(20, 18, 25))
    for y in range(GRID_HEIGHT):
        color_layer.set(((0, y)), mcrfpy.Color(20, 18, 25))
        color_layer.set(((GRID_WIDTH - 1, y)), mcrfpy.Color(20, 18, 25))

    # Title
    title = mcrfpy.Caption(text="Cave System: Noise + Threshold + Kernel + BSP Ruins", pos=(10, 10))
    title.fill_color = mcrfpy.Color(255, 255, 255)
    title.outline = 1
    title.outline_color = mcrfpy.Color(0, 0, 0)
    scene.children.append(title)


# Setup
scene = mcrfpy.Scene("caves")

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
automation.screenshot("procgen_33_advanced_caves.png")
print("Screenshot saved: procgen_33_advanced_caves.png")
