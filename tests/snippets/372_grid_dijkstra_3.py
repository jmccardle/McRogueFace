# mcrf: objects=[Color,ColorLayer,Entity,Grid,Scene] verified=0.3.6 status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(1024, 768),
    zoom=4.0
)
scene.children.append(grid)

# Two overlays: one for movement range, one for influence
highlight_layer = mcrfpy.ColorLayer(z_index=1, name="highlight")
grid.add_layer(highlight_layer)
influence_layer = mcrfpy.ColorLayer(z_index=2, name="influence")
grid.add_layer(influence_layer)

# Floor tiles with a wall down the middle
for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        cell.tilesprite = 48
        cell.walkable = True

for i in range(5):
    grid.at(8, 2 + i).tilesprite = 1
    grid.at(8, 2 + i).walkable = False


class Enemy(mcrfpy.Entity):
    """An Entity subclass carrying its own health attributes."""
    hp = 10
    max_hp = 10


player = mcrfpy.Entity(grid_pos=(3, 6), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(player)

enemy = Enemy(grid_pos=(13, 6), texture=mcrfpy.default_texture, sprite_index=112)
grid.entities.append(enemy)
enemies = [enemy]

# Positions the Quick Start fence refers to
target_x, target_y = 12, 9
start_x, start_y = 13, 6

# region: quickstart
import mcrfpy

# grid is an existing mcrfpy.Grid; player is an mcrfpy.Entity on that grid

# Get (or reuse the cached) distance map rooted at the player's position
dijkstra = grid.get_dijkstra_map(player.grid_pos)

# Get distance from any cell to the root
distance = dijkstra.distance((target_x, target_y))

# Get a single step from any cell toward the root
step = dijkstra.step_from((start_x, start_y))

# Get the full path from any cell to the root
path = dijkstra.path_from((start_x, start_y))
# endregion

# region: chase
def ai_chase(grid, entity, target_x, target_y):
    """Move entity toward target using a Dijkstra map."""
    dijkstra = grid.get_dijkstra_map((target_x, target_y))

    # descent_step returns the single best neighbor toward the root,
    # or None if entity is already at a local minimum / off-grid
    step = dijkstra.descent_step(entity.grid_pos)

    if step is not None:
        entity.grid_pos = step
# endregion

# region: multi
def get_distance_to_nearest(grid, positions, cell):
    """Distance from cell to the nearest of several source positions."""
    dijkstra = grid.get_dijkstra_map(roots=positions)
    return dijkstra.distance(cell)


# Usage: flee from the nearest of several threats
def ai_flee_group(grid, entity, threats):
    threat_positions = [t.grid_pos for t in threats]
    toward_threats = grid.get_dijkstra_map(roots=threat_positions)
    away_from_threats = toward_threats.invert()

    step = away_from_threats.descent_step(entity.grid_pos)
    if step is not None:
        entity.grid_pos = step
# endregion

# region: manager
class DijkstraManager:
    """Cache several named Dijkstra maps for weighted AI decisions."""

    def __init__(self, grid):
        self.grid = grid
        self.maps = {}  # name -> DijkstraMap

    def set_goal(self, name, root_or_roots):
        """Compute (or fetch the cached) map for a named goal."""
        if isinstance(root_or_roots, list):
            self.maps[name] = self.grid.get_dijkstra_map(roots=root_or_roots)
        else:
            self.maps[name] = self.grid.get_dijkstra_map(root_or_roots)

    def get_distance(self, name, pos):
        """Get distance to a named goal, or None if not reachable/not set."""
        dmap = self.maps.get(name)
        if dmap is None:
            return None
        return dmap.distance(pos)

    def get_combined_value(self, pos, weights):
        """Get a weighted combination of multiple named maps."""
        value = 0.0
        for name, weight in weights.items():
            dist = self.get_distance(name, pos)
            if dist is not None:
                value += dist * weight
        return value


def ai_decision(grid, manager, enemy):
    """Make an AI decision based on multiple weighted factors."""
    # hp/max_hp are attributes YOU add on your Entity subclass;
    # mcrfpy.Entity has no built-in health property.
    if enemy.hp < enemy.max_hp * 0.3:
        # Low health - prioritize potions, avoid player
        weights = {
            'potions': -1.0,  # Move toward potions
            'player': 0.5,    # Move away from player
        }
    else:
        # Healthy - chase player
        weights = {
            'player': -1.0,   # Move toward player
        }

    ex, ey = enemy.grid_pos
    best_move = None
    best_value = float('inf')

    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
        nx, ny = ex + dx, ey + dy

        if grid.at(nx, ny).walkable:
            value = manager.get_combined_value((nx, ny), weights)
            if value < best_value:
                best_value = value
                best_move = (nx, ny)

    if best_move:
        enemy.grid_pos = best_move
# endregion

# region: range
def get_reachable_cells(grid, start_x, start_y, max_cost):
    """Get all cells reachable within a movement budget."""
    dijkstra = grid.get_dijkstra_map((start_x, start_y))

    reachable = []
    for x in range(grid.grid_w):
        for y in range(grid.grid_h):
            dist = dijkstra.distance((x, y))
            if dist is not None and dist <= max_cost:
                reachable.append((x, y, dist))

    return reachable


def show_movement_range(grid, highlight_layer, entity, movement_points):
    """Highlight reachable cells with distance coloring."""
    ex, ey = entity.grid_pos
    reachable = get_reachable_cells(grid, ex, ey, movement_points)

    for x, y, dist in reachable:
        # Color intensity based on remaining movement
        remaining = movement_points - dist
        intensity = int(200 * remaining / movement_points)
        color = mcrfpy.Color(50, 50 + intensity, 255, 100)
        highlight_layer.set((x, y), color)
# endregion

# region: influence
def compute_influence_map(grid, player_team, enemy_team):
    """Show which team controls which areas."""
    influence = {}

    # Player team influence
    for ally in player_team:
        dijkstra = grid.get_dijkstra_map(ally.grid_pos)
        for x in range(grid.grid_w):
            for y in range(grid.grid_h):
                dist = dijkstra.distance((x, y))
                if dist is not None:
                    influence[(x, y)] = influence.get((x, y), 0.0) + 1.0 / (1.0 + dist)

    # Subtract enemy team influence
    for enemy in enemy_team:
        dijkstra = grid.get_dijkstra_map(enemy.grid_pos)
        for x in range(grid.grid_w):
            for y in range(grid.grid_h):
                dist = dijkstra.distance((x, y))
                if dist is not None:
                    influence[(x, y)] = influence.get((x, y), 0.0) - 1.0 / (1.0 + dist)

    return influence


def show_influence_map(influence_layer, influence):
    """Visualize influence values on a ColorLayer."""
    for (x, y), val in influence.items():
        if val > 0:
            # Player controlled - blue
            alpha = min(150, int(abs(val) * 50))
            influence_layer.set((x, y), mcrfpy.Color(50, 50, 200, alpha))
        elif val < 0:
            # Enemy controlled - red
            alpha = min(150, int(abs(val) * 50))
            influence_layer.set((x, y), mcrfpy.Color(200, 50, 50, alpha))
# endregion

# region: cost
# Cheaper diagonal movement, and block on any entity labeled "blocker"
dijkstra = grid.get_dijkstra_map(player.grid_pos, diagonal_cost=1.0, collide="blocker")
# endregion

# region: visibility
def compute_safe_dijkstra(grid, player, goal_pos):
    """Compute a distance map that avoids cells the player hasn't discovered."""
    original_walkable = {}

    for x in range(grid.grid_w):
        for y in range(grid.grid_h):
            if player.perspective_map[x, y] == 0:  # unknown
                point = grid.at(x, y)
                original_walkable[(x, y)] = point.walkable
                point.walkable = False

    dijkstra = grid.get_dijkstra_map(goal_pos)  # built against the masked terrain

    for (x, y), walkable in original_walkable.items():
        grid.at(x, y).walkable = walkable
    # The map we hold is a snapshot, so it keeps the explored-only distances;
    # the next get_dijkstra_map() call sees the real walkability again.

    return dijkstra
# endregion

# region: radius
dijkstra = grid.get_dijkstra_map(player.grid_pos, radius=64)
for enemy in enemies:
    if not dijkstra.is_exact(enemy.grid_pos):
        continue  # far away: let it idle, or take the greedy step_from()
    step = dijkstra.step_from(enemy.grid_pos)
# endregion


# Use them once
ai_chase(grid, enemy, target_x, target_y)
ai_flee_group(grid, enemy, [player])
print(get_distance_to_nearest(grid, [player.grid_pos, (13, 2)], enemy.grid_pos))

manager = DijkstraManager(grid)
manager.set_goal('player', player.grid_pos)
manager.set_goal('potions', [(2, 2), (14, 10)])
ai_decision(grid, manager, enemy)
enemy.hp = 2
ai_decision(grid, manager, enemy)

show_movement_range(grid, highlight_layer, player, 6)

influence = compute_influence_map(grid, [player], [enemy])
show_influence_map(influence_layer, influence)

player.update_visibility()
safe = compute_safe_dijkstra(grid, player, (5, 6))
print(safe.distance((5, 6)))
