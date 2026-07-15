# mcrf: objects=[Entity,Grid,Scene] verified=0.2.8-dev status=ok
import mcrfpy
import random


def generate_caves(grid, fill_chance=0.45, iterations=5):
    """Generate organic caves using cellular automata."""
    width, height = int(grid.grid_size[0]), int(grid.grid_size[1])

    # Step 1: Random noise
    for y in range(height):
        for x in range(width):
            cell = grid.at((x, y))
            # Border is always wall
            if x == 0 or x == width-1 or y == 0 or y == height-1:
                cell.walkable = False
                cell.tilesprite = 1  # Wall
            else:
                is_wall = random.random() < fill_chance
                cell.walkable = not is_wall
                cell.tilesprite = 1 if is_wall else 0

    # Step 2: Smooth with cellular automata rules
    for _ in range(iterations):
        smooth_caves(grid)

    return grid

def smooth_caves(grid):
    """Apply one iteration of cellular automata smoothing."""
    width, height = int(grid.grid_size[0]), int(grid.grid_size[1])

    # Create a copy of current state
    walls = [[not grid.at((x, y)).walkable
              for x in range(width)]
             for y in range(height)]

    for y in range(1, height - 1):
        for x in range(1, width - 1):
            # Count wall neighbors (including diagonals)
            wall_count = 0
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    if walls[y + dy][x + dx]:
                        wall_count += 1

            cell = grid.at((x, y))
            # Rule: >=5 walls = become wall, <=3 walls = become floor
            if wall_count >= 5:
                cell.walkable = False
                cell.tilesprite = 1
            elif wall_count <= 3:
                cell.walkable = True
                cell.tilesprite = 0


def find_largest_cave(grid):
    """Find the largest connected walkable region."""
    width, height = int(grid.grid_size[0]), int(grid.grid_size[1])
    visited = set()
    regions = []

    def flood_fill(start_x, start_y):
        """Flood fill from a point, return all connected cells."""
        cells = []
        stack = [(start_x, start_y)]

        while stack:
            x, y = stack.pop()
            if (x, y) in visited:
                continue
            if x < 0 or x >= width or y < 0 or y >= height:
                continue
            if not grid.at((x, y)).walkable:
                continue

            visited.add((x, y))
            cells.append((x, y))

            stack.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])

        return cells

    # Find all regions
    for y in range(height):
        for x in range(width):
            if (x, y) not in visited and grid.at((x, y)).walkable:
                region = flood_fill(x, y)
                if region:
                    regions.append(region)

    # Keep only the largest
    if not regions:
        return []

    largest = max(regions, key=len)

    # Fill in smaller regions as walls
    for region in regions:
        if region is not largest:
            for x, y in region:
                cell = grid.at((x, y))
                cell.walkable = False
                cell.tilesprite = 1

    return largest


def find_cave_features(grid, spawn_point):
    """Find dead ends, wide areas, and chokepoints."""
    width, height = int(grid.grid_size[0]), int(grid.grid_size[1])

    dead_ends = []      # Cells with only one walkable neighbor
    wide_areas = []     # Cells with 6+ walkable neighbors
    chokepoints = []    # Cells where path width is narrow

    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if not grid.at((x, y)).walkable:
                continue

            # Count walkable neighbors
            walkable_neighbors = sum(
                1 for dy in [-1, 0, 1]
                for dx in [-1, 0, 1]
                if not (dx == 0 and dy == 0)
                and grid.at((x + dx, y + dy)).walkable
            )

            if walkable_neighbors <= 1:
                dead_ends.append((x, y))
            elif walkable_neighbors >= 6:
                wide_areas.append((x, y))
            elif walkable_neighbors == 2:
                chokepoints.append((x, y))

    return {
        'dead_ends': dead_ends,      # Good for treasure, secrets
        'wide_areas': wide_areas,    # Good for boss arenas
        'chokepoints': chokepoints   # Good for traps, doors
    }


# Setup
scene = mcrfpy.Scene("caves")
scene.activate()

# Create grid
texture = mcrfpy.default_texture
grid = mcrfpy.Grid(grid_size=(60, 40), texture=texture,
                   pos=(0, 0), size=(960, 640))
scene.children.append(grid)

# Generate caves
generate_caves(grid, fill_chance=0.45, iterations=5)

# Find largest connected region
largest = find_largest_cave(grid)
print(f"Largest cave has {len(largest)} cells")

# Find features
spawn = largest[0]  # Start at first cell of largest region
features = find_cave_features(grid, spawn)
print(f"Found {len(features['dead_ends'])} dead ends")
print(f"Found {len(features['wide_areas'])} wide areas")

# Place player at spawn
player = mcrfpy.Entity(spawn, texture, sprite_index=64)
grid.entities.append(player)

# Place treasure at dead ends
for i, pos in enumerate(features['dead_ends'][:5]):
    treasure = mcrfpy.Entity(pos, texture, sprite_index=32)
    grid.entities.append(treasure)

# Place boss in widest area (if any)
if features['wide_areas']:
    boss_pos = features['wide_areas'][0]
    boss = mcrfpy.Entity(boss_pos, texture, sprite_index=80)
    grid.entities.append(boss)

grid.center_camera(spawn)
