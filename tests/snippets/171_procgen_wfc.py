# mcrf: objects=[Grid,Scene] verified=0.2.8-dev status=ok
import mcrfpy
import random


class WFC:
    """Simple Wave Function Collapse for tile grids."""

    def __init__(self, grid, rules):
        self.grid = grid
        self.rules = rules
        self.width, self.height = int(grid.grid_size[0]), int(grid.grid_size[1])
        self.tiles = set(rules.keys())

        self.possibilities = {}
        for y in range(self.height):
            for x in range(self.width):
                self.possibilities[(x, y)] = set(self.tiles)

    def collapse(self):
        """Run WFC until complete or contradiction."""
        while True:
            cell = self._lowest_entropy_cell()
            if cell is None:
                return True  # All cells collapsed

            x, y = cell
            options = self.possibilities[(x, y)]

            if not options:
                return False  # Contradiction!

            chosen = random.choice(list(options))
            self.possibilities[(x, y)] = {chosen}

            self.grid.at((x, y)).tilesprite = chosen

            if not self._propagate(x, y):
                return False

        return True

    def _lowest_entropy_cell(self):
        best = None
        best_entropy = float('inf')

        for pos, options in self.possibilities.items():
            if len(options) > 1:
                entropy = len(options) + random.random() * 0.1
                if entropy < best_entropy:
                    best_entropy = entropy
                    best = pos

        return best

    def _propagate(self, start_x, start_y):
        stack = [(start_x, start_y)]

        directions = {
            'N': (0, -1), 'S': (0, 1),
            'E': (1, 0), 'W': (-1, 0)
        }

        while stack:
            x, y = stack.pop()
            current_options = self.possibilities[(x, y)]

            for dir_name, (dx, dy) in directions.items():
                nx, ny = x + dx, y + dy

                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue

                neighbor_options = self.possibilities[(nx, ny)]
                if len(neighbor_options) == 1:
                    continue

                allowed = set()
                for tile in current_options:
                    if dir_name in self.rules[tile]:
                        allowed.update(self.rules[tile][dir_name])

                new_options = neighbor_options & allowed
                if new_options != neighbor_options:
                    if not new_options:
                        return False

                    self.possibilities[(nx, ny)] = new_options
                    stack.append((nx, ny))

        return True


# Setup
scene = mcrfpy.Scene("wfc_demo")
scene.activate()
mcrfpy.step(0.1)

texture = mcrfpy.default_texture
grid = mcrfpy.Grid(grid_size=(30, 20), texture=texture,
                   pos=(0, 0), size=(480, 320))
scene.children.append(grid)

# Simple terrain rules
GRASS = 0
DIRT = 1
WATER = 2
SAND = 3  # Transition between grass/water

terrain_rules = {
    GRASS: {'N': [GRASS, DIRT, SAND], 'S': [GRASS, DIRT, SAND],
            'E': [GRASS, DIRT, SAND], 'W': [GRASS, DIRT, SAND]},
    DIRT:  {'N': [GRASS, DIRT], 'S': [GRASS, DIRT],
            'E': [GRASS, DIRT], 'W': [GRASS, DIRT]},
    WATER: {'N': [WATER, SAND], 'S': [WATER, SAND],
            'E': [WATER, SAND], 'W': [WATER, SAND]},
    SAND:  {'N': [GRASS, WATER, SAND], 'S': [GRASS, WATER, SAND],
            'E': [GRASS, WATER, SAND], 'W': [GRASS, WATER, SAND]}
}

# Seed with water in center
wfc = WFC(grid, terrain_rules)
for x in range(12, 18):
    for y in range(8, 12):
        wfc.possibilities[(x, y)] = {WATER}
        grid.at((x, y)).tilesprite = WATER
        wfc._propagate(x, y)

# Generate rest
if wfc.collapse():
    print("Terrain generated successfully!")
else:
    print("Generation failed")

# Set walkability based on tiles
width, height = int(grid.grid_size[0]), int(grid.grid_size[1])
for y in range(height):
    for x in range(width):
        cell = grid.at((x, y))
        cell.walkable = cell.tilesprite != WATER
