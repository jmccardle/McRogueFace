# mcrf: objects=[Grid,Scene] verified=0.3.6-dev status=ok
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


scene = mcrfpy.Scene("cave-variations")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(60, 40), texture=mcrfpy.default_texture,
                   pos=(0, 0), size=(960, 640))
scene.children.append(grid)

# region: fill-ratios
# Open caverns
generate_caves(grid, fill_chance=0.38, iterations=4)

# Classic caves
generate_caves(grid, fill_chance=0.45, iterations=5)

# Tight tunnels
generate_caves(grid, fill_chance=0.55, iterations=6)
# endregion


# region: custom-rules
def smooth_caves_custom(grid, birth_limit=5, death_limit=4):
    """Customizable cellular automata rules.

    Args:
        birth_limit: Wall count >= this turns floor into wall
        death_limit: Wall count < this turns wall into floor
    """
    width, height = int(grid.grid_size[0]), int(grid.grid_size[1])
    walls = [[not grid.at((x, y)).walkable
              for x in range(width)]
             for y in range(height)]

    for y in range(1, height - 1):
        for x in range(1, width - 1):
            wall_count = sum(
                walls[y + dy][x + dx]
                for dy in [-1, 0, 1]
                for dx in [-1, 0, 1]
                if not (dx == 0 and dy == 0)
            )

            cell = grid.at((x, y))
            is_wall = walls[y][x]

            if is_wall:
                # Wall survives if enough neighbors
                if wall_count < death_limit:
                    cell.walkable = True
                    cell.tilesprite = 0
            else:
                # Floor becomes wall if too many neighbors
                if wall_count >= birth_limit:
                    cell.walkable = False
                    cell.tilesprite = 1
# endregion


smooth_caves_custom(grid, birth_limit=5, death_limit=4)
