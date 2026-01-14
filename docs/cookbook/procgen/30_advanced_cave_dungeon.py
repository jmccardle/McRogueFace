"""Advanced: Cave-Carved Dungeon

Combines: BSP (room structure) + Noise (organic cave walls) + Erosion
Creates a dungeon where rooms have been carved from natural cave formations.
"""
import mcrfpy
from mcrfpy import automation

GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def run_demo(runtime):
    # Step 1: Create base cave system using noise
    noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=42)

    cave_map = mcrfpy.HeightMap((GRID_WIDTH, GRID_HEIGHT), fill=0.0)
    cave_map.add_noise(noise, world_size=(12, 10), mode='fbm', octaves=4)
    cave_map.normalize(0.0, 1.0)

    # Step 2: Create BSP rooms
    bsp = mcrfpy.BSP(pos=(3, 3), size=(GRID_WIDTH - 6, GRID_HEIGHT - 6))
    bsp.split_recursive(depth=3, min_size=(10, 8), max_ratio=1.5, seed=42)

    rooms_hmap = bsp.to_heightmap(
        size=(GRID_WIDTH, GRID_HEIGHT),
        select='leaves',
        shrink=2,
        value=1.0
    )

    # Step 3: Combine - rooms carve into cave, cave affects walls
    combined = mcrfpy.HeightMap((GRID_WIDTH, GRID_HEIGHT), fill=0.0)
    combined.copy_from(cave_map)

    # Scale cave values to mid-range so rooms stand out
    combined.scale(0.5)
    combined.add_constant(0.2)

    # Add room interiors (rooms become high values)
    combined.max(rooms_hmap)

    # Step 4: Apply GENTLE erosion for organic edges
    # Use fewer drops and lower erosion rate
    combined.rain_erosion(drops=100, erosion=0.02, sedimentation=0.01, seed=42)

    # Re-normalize to ensure we use the full value range
    combined.normalize(0.0, 1.0)

    # Step 5: Create corridor connections
    adjacency = bsp.adjacency
    connected = set()

    corridor_map = mcrfpy.HeightMap((GRID_WIDTH, GRID_HEIGHT), fill=0.0)

    for leaf_idx in range(len(bsp)):
        leaf = bsp.get_leaf(leaf_idx)
        cx1, cy1 = leaf.center()

        for neighbor_idx in adjacency[leaf_idx]:
            pair = (min(leaf_idx, neighbor_idx), max(leaf_idx, neighbor_idx))
            if pair in connected:
                continue
            connected.add(pair)

            neighbor = bsp.get_leaf(neighbor_idx)
            cx2, cy2 = neighbor.center()

            # Draw corridor using bezier for organic feel
            mid_x = (cx1 + cx2) // 2 + ((leaf_idx * 3) % 5 - 2)
            mid_y = (cy1 + cy2) // 2 + ((neighbor_idx * 7) % 5 - 2)

            corridor_map.dig_bezier(
                points=((cx1, cy1), (mid_x, cy1), (mid_x, cy2), (cx2, cy2)),
                start_radius=1.5, end_radius=1.5,
                start_height=0.0, end_height=0.0
            )

    # Add corridors - dig_bezier creates low values where corridors are
    # We want high values there, so invert the corridor map logic
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            corr_val = corridor_map.get((x, y))
            if corr_val < 0.5:  # Corridor was dug here
                current = combined.get((x, y))
                combined.fill(max(current, 0.7), pos=(x, y), size=(1, 1))

    # Step 6: Render with cave aesthetics
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            h = combined.get((x, y))

            if h < 0.30:
                # Solid rock/wall - darker
                base = 30 + int(cave_map.get((x, y)) * 20)
                color_layer.set(((x, y)), mcrfpy.Color(base + 10, base + 5, base + 15))
            elif h < 0.40:
                # Cave wall edge (rough transition)
                t = (h - 0.30) / 0.10
                base = int(40 + t * 15)
                color_layer.set(((x, y)), mcrfpy.Color(base + 10, base + 5, base + 15))
            elif h < 0.55:
                # Cave floor (natural stone)
                t = (h - 0.40) / 0.15
                base = 65 + int(t * 20)
                var = ((x * 7 + y * 11) % 10)
                color_layer.set(((x, y)), mcrfpy.Color(base + var, base - 5 + var, base - 10))
            elif h < 0.70:
                # Corridor/worked passage
                base = 85 + ((x + y) % 2) * 5
                color_layer.set(((x, y)), mcrfpy.Color(base, base - 3, base - 6))
            else:
                # Room floor (finely worked stone)
                base = 105 + ((x + y) % 2) * 8
                color_layer.set(((x, y)), mcrfpy.Color(base, base - 8, base - 12))

    # Mark room centers with special tile
    for leaf in bsp.leaves():
        cx, cy = leaf.center()
        if 0 <= cx < GRID_WIDTH and 0 <= cy < GRID_HEIGHT:
            color_layer.set(((cx, cy)), mcrfpy.Color(160, 140, 120))
            # Cross pattern
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                    color_layer.set(((nx, ny)), mcrfpy.Color(140, 125, 105))

    # Outer border
    for x in range(GRID_WIDTH):
        color_layer.set(((x, 0)), mcrfpy.Color(20, 15, 25))
        color_layer.set(((x, GRID_HEIGHT - 1)), mcrfpy.Color(20, 15, 25))
    for y in range(GRID_HEIGHT):
        color_layer.set(((0, y)), mcrfpy.Color(20, 15, 25))
        color_layer.set(((GRID_WIDTH - 1, y)), mcrfpy.Color(20, 15, 25))

    # Title
    title = mcrfpy.Caption(text="Cave-Carved Dungeon: BSP + Noise + Erosion", pos=(10, 10))
    title.fill_color = mcrfpy.Color(255, 255, 255)
    title.outline = 1
    title.outline_color = mcrfpy.Color(0, 0, 0)
    scene.children.append(title)


# Setup
scene = mcrfpy.Scene("cave_dungeon")

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
automation.screenshot("procgen_30_advanced_cave_dungeon.png")
print("Screenshot saved: procgen_30_advanced_cave_dungeon.png")
