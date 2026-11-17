# mcrf: objects=[Grid,Scene] verified=0.3.6-dev status=ok
import mcrfpy
import random

# The WFC class from the Quick Start, which every fence below builds on.
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


scene = mcrfpy.Scene("wfc_rules")
scene.activate()
mcrfpy.step(0.1)

grid = mcrfpy.Grid(grid_size=(30, 20), texture=mcrfpy.default_texture,
                   pos=(0, 0), size=(480, 320))
scene.children.append(grid)

# region: rules
# Simple path tiles
# 0 = grass, 1 = path, 2 = water

rules = {
    0: {  # Grass
        'N': [0, 1, 2],  # Grass can have grass, path, or water above
        'S': [0, 1, 2],
        'E': [0, 1, 2],
        'W': [0, 1, 2]
    },
    1: {  # Path
        'N': [0, 1],     # Path connects to grass or more path
        'S': [0, 1],
        'E': [0, 1],
        'W': [0, 1]
    },
    2: {  # Water
        'N': [0, 2],     # Water connects to grass or more water
        'S': [0, 2],
        'E': [0, 2],
        'W': [0, 2]
    }
}
# endregion

# region: road
# Road tile indices
GRASS = 0
ROAD_H = 1   # Horizontal road
ROAD_V = 2   # Vertical road
ROAD_X = 3   # Crossroads
ROAD_NE = 4  # Corner NE
ROAD_NW = 5  # Corner NW
ROAD_SE = 6  # Corner SE
ROAD_SW = 7  # Corner SW

road_rules = {
    GRASS: {
        'N': [GRASS, ROAD_H, ROAD_SE, ROAD_SW],
        'S': [GRASS, ROAD_H, ROAD_NE, ROAD_NW],
        'E': [GRASS, ROAD_V, ROAD_NW, ROAD_SW],
        'W': [GRASS, ROAD_V, ROAD_NE, ROAD_SE]
    },
    ROAD_H: {  # Horizontal: connects E-W
        'N': [GRASS, ROAD_H],
        'S': [GRASS, ROAD_H],
        'E': [ROAD_H, ROAD_X, ROAD_NW, ROAD_SW],
        'W': [ROAD_H, ROAD_X, ROAD_NE, ROAD_SE]
    },
    ROAD_V: {  # Vertical: connects N-S
        'N': [ROAD_V, ROAD_X, ROAD_SE, ROAD_SW],
        'S': [ROAD_V, ROAD_X, ROAD_NE, ROAD_NW],
        'E': [GRASS, ROAD_V],
        'W': [GRASS, ROAD_V]
    },
    ROAD_X: {  # Crossroads: connects all
        'N': [ROAD_V, ROAD_X, ROAD_SE, ROAD_SW],
        'S': [ROAD_V, ROAD_X, ROAD_NE, ROAD_NW],
        'E': [ROAD_H, ROAD_X, ROAD_NW, ROAD_SW],
        'W': [ROAD_H, ROAD_X, ROAD_NE, ROAD_SE]
    },
    # Corners connect specific directions
    ROAD_NE: {'N': [ROAD_V, ROAD_X, ROAD_SE, ROAD_SW],
              'S': [GRASS], 'E': [ROAD_H, ROAD_X, ROAD_NW, ROAD_SW], 'W': [GRASS]},
    ROAD_NW: {'N': [ROAD_V, ROAD_X, ROAD_SE, ROAD_SW],
              'S': [GRASS], 'E': [GRASS], 'W': [ROAD_H, ROAD_X, ROAD_NE, ROAD_SE]},
    ROAD_SE: {'N': [GRASS], 'S': [ROAD_V, ROAD_X, ROAD_NE, ROAD_NW],
              'E': [ROAD_H, ROAD_X, ROAD_NW, ROAD_SW], 'W': [GRASS]},
    ROAD_SW: {'N': [GRASS], 'S': [ROAD_V, ROAD_X, ROAD_NE, ROAD_NW],
              'E': [GRASS], 'W': [ROAD_H, ROAD_X, ROAD_NE, ROAD_SE]}
}

# Generate
wfc = WFC(grid, road_rules)
success = wfc.collapse()
print("Generation successful!" if success else "Contradiction occurred")
# endregion

# region: walls
# Wall tiles that connect correctly
FLOOR = 0
WALL_SOLID = 1
WALL_N = 2   # Wall on north side
WALL_S = 3
WALL_E = 4
WALL_W = 5
WALL_NE = 6  # Corner
WALL_NW = 7
WALL_SE = 8
WALL_SW = 9

wall_rules = {
    FLOOR: {
        'N': [FLOOR, WALL_S, WALL_SE, WALL_SW],
        'S': [FLOOR, WALL_N, WALL_NE, WALL_NW],
        'E': [FLOOR, WALL_W, WALL_NW, WALL_SW],
        'W': [FLOOR, WALL_E, WALL_NE, WALL_SE]
    },
    WALL_SOLID: {
        'N': [WALL_SOLID, WALL_N, WALL_NE, WALL_NW],
        'S': [WALL_SOLID, WALL_S, WALL_SE, WALL_SW],
        'E': [WALL_SOLID, WALL_E, WALL_NE, WALL_SE],
        'W': [WALL_SOLID, WALL_W, WALL_NW, WALL_SW]
    },
    # Edge walls connect solid to floor correctly
    WALL_N: {
        'N': [WALL_SOLID, WALL_N],
        'S': [FLOOR, WALL_S],
        'E': [WALL_N, WALL_NE, WALL_SOLID],
        'W': [WALL_N, WALL_NW, WALL_SOLID]
    },
    # ... similar rules for other edge/corner tiles
}
# endregion

# region: seed
def seed_wfc(wfc, constraints):
    """Pre-seed WFC with fixed tiles.

    Args:
        constraints: Dict of {(x, y): tile_id}
    """
    for (x, y), tile in constraints.items():
        wfc.possibilities[(x, y)] = {tile}
        wfc.grid.at((x, y)).tilesprite = tile

# Example: Force roads at specific points
constraints = {
    (0, 10): ROAD_H,   # Road enters from west
    (29, 10): ROAD_H,  # Road exits to east
    (15, 0): ROAD_V,   # Road enters from north
    (15, 19): ROAD_V   # Road exits to south
}

wfc = WFC(grid, road_rules)
seed_wfc(wfc, constraints)

# Run propagation from seeded cells
for pos in constraints:
    wfc._propagate(*pos)

# Then collapse the rest
wfc.collapse()
# endregion

# region: retries
def generate_with_retries(grid, rules, max_attempts=10):
    """Generate with automatic retry on contradiction."""
    for attempt in range(max_attempts):
        wfc = WFC(grid, rules)
        if wfc.collapse():
            print(f"Success on attempt {attempt + 1}")
            return True

        print(f"Contradiction on attempt {attempt + 1}, retrying...")

    print("Failed after all attempts")
    return False

# Or use backtracking (more complex but more reliable)
# NOTE: this sketch is illustrative, not production-ready — on a failed
# _propagate, it pops history and subtracts `tried` but never restores the
# grid's tiles or re-propagates the reverted possibilities. A real
# implementation needs to undo grid.at(...).tilesprite writes made during
# the failed branch (and re-propagate) before continuing.
class WFCBacktracking(WFC):
    """WFC with backtracking on contradiction."""

    def collapse(self):
        history = []  # Stack of (pos, old_possibilities)

        while True:
            cell = self._lowest_entropy_cell()
            if cell is None:
                return True

            x, y = cell
            options = list(self.possibilities[(x, y)])

            if not options:
                # Contradiction - backtrack
                if not history:
                    return False

                # Restore previous state
                pos, old_poss, tried = history.pop()
                self.possibilities[pos] = old_poss - tried
                continue

            # Save state for backtracking
            chosen = random.choice(options)
            history.append(((x, y), self.possibilities[(x, y)].copy(), {chosen}))

            self.possibilities[(x, y)] = {chosen}
            self.grid.at((x, y)).tilesprite = chosen

            if not self._propagate(x, y):
                # Undo this choice
                pos, old_poss, tried = history.pop()
                self.possibilities[pos] = old_poss - tried
# endregion

# region: weighted
def collapse_weighted(self):
    """Collapse with weighted tile selection."""
    weights = {
        GRASS: 10,    # Very common
        ROAD_H: 2,
        ROAD_V: 2,
        ROAD_X: 1,    # Rare
        # ... etc
    }

    cell = self._lowest_entropy_cell()
    if cell is None:
        return True

    x, y = cell
    options = list(self.possibilities[(x, y)])

    if not options:
        return False

    # Weighted random choice
    option_weights = [weights.get(t, 1) for t in options]
    total = sum(option_weights)
    r = random.random() * total

    cumulative = 0
    for opt, w in zip(options, option_weights):
        cumulative += w
        if r <= cumulative:
            chosen = opt
            break

    self.possibilities[(x, y)] = {chosen}
    self.grid.at((x, y)).tilesprite = chosen

    return self._propagate(x, y)
# endregion

