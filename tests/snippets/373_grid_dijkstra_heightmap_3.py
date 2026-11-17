# mcrf: objects=[Color,ColorLayer,Entity,Grid,HeightMap,Scene] verified=0.3.6-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("dijkstra_heightmap")
mcrfpy.current_scene = scene

grid_w, grid_h = 40, 40
width, height = 40, 40
grid = mcrfpy.Grid(
    grid_size=(grid_w, grid_h),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(960, 720)
)
scene.children.append(grid)

for y in range(grid_h):
    for x in range(grid_w):
        cell = grid.at(x, y)
        cell.tilesprite = 48
        cell.walkable = True

fog_layer = mcrfpy.ColorLayer(z_index=1, name="fog")
grid.add_layer(fog_layer)

# The fences below assume these (they are yours to supply)
source_x, source_y = 5, 5
x, y = 7, 3
WATER_TILE = 12


def find_valid_spawns(grid):
    """Every walkable cell, in reading order."""
    return [(cx, cy) for cy in range(grid_h) for cx in range(grid_w)
            if grid.at(cx, cy).walkable and (cx + cy) % 7 == 0]


def create_enemy(enemy_type, point):
    """Place an enemy sprite; the sprite stands in for its type."""
    sprites = {"rat": 112, "goblin": 113, "orc": 114, "troll": 115}
    enemy = mcrfpy.Entity(grid_pos=point, texture=mcrfpy.default_texture,
                          sprite_index=sprites[enemy_type])
    grid.entities.append(enemy)
    return enemy


# region: get_map
# From a grid, compute distances from a source point
dijkstra = grid.get_dijkstra_map((source_x, source_y))

# Query individual distances
distance = dijkstra.distance((x, y))
# endregion

# region: convert
# Basic conversion - the size of the map's window (the whole grid, unless the
# grid is over 1023 on a side or you passed radius=)
hmap = dijkstra.to_heightmap()

# A windowed map's heightmap starts at dijkstra.window[:2]; place it on a
# grid-sized HeightMap with copy_from
full = mcrfpy.HeightMap((grid_w, grid_h))
full.fill(-1.0)
full.copy_from(dijkstra.to_heightmap(), pos=dijkstra.window[:2])

# Custom unreachable value (default is -1.0)
hmap = dijkstra.to_heightmap(unreachable=0.0)
hmap = dijkstra.to_heightmap(unreachable=999.0)

# Custom output size
hmap = dijkstra.to_heightmap(size=(width, height))
# endregion

# region: access
# Get height at position
height = hmap[(x, y)]

# HeightMaps also support standard operations
# (see HeightMap documentation for full API)
# endregion

# region: spawn
def spawn_enemies(grid, player_start, enemy_count):
    """Spawn enemies with difficulty based on distance from start."""
    dijkstra = grid.get_dijkstra_map(player_start)
    hmap = dijkstra.to_heightmap(unreachable=0.0)

    enemies = []
    spawn_points = find_valid_spawns(grid)

    for point in spawn_points[:enemy_count]:
        distance = hmap[point]

        if distance < 5:
            enemy_type = "rat"      # Easy enemies near spawn
        elif distance < 10:
            enemy_type = "goblin"   # Medium difficulty
        elif distance < 15:
            enemy_type = "orc"      # Hard enemies
        else:
            enemy_type = "troll"    # Boss-tier far from spawn

        enemies.append(create_enemy(enemy_type, point))

    return enemies
# endregion

# region: fog
def update_fog(grid, fog_layer, player_pos):
    """Update fog intensity based on distance from player."""
    dijkstra = grid.get_dijkstra_map(player_pos)
    hmap = dijkstra.to_heightmap(unreachable=20.0)

    width, height = int(grid.grid_size[0]), int(grid.grid_size[1])

    for y in range(height):
        for x in range(width):
            distance = hmap[(x, y)]

            # Calculate fog alpha based on distance
            if distance <= 3:
                alpha = 0        # Clear near player
            elif distance <= 8:
                alpha = int((distance - 3) * 30)  # Gradual fade
            else:
                alpha = 200      # Dense fog far away

            fog_layer.set((x, y), mcrfpy.Color(20, 20, 40, alpha))
# endregion

# region: river
def carve_river(grid, source, destination):
    """Carve a river-like path between two points."""
    # Get distance from destination
    dijkstra = grid.get_dijkstra_map(destination)
    hmap = dijkstra.to_heightmap(unreachable=999.0)

    # Start at source, follow decreasing distance
    current = source
    path = [current]

    while current != destination:
        x, y = current
        best_neighbor = None
        best_dist = hmap[current]

        # Check all neighbors
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < grid.grid_size[0] and 0 <= ny < grid.grid_size[1]:
                neighbor_dist = hmap[(nx, ny)]
                if neighbor_dist < best_dist:
                    best_dist = neighbor_dist
                    best_neighbor = (nx, ny)

        if best_neighbor is None:
            break  # No path found

        current = best_neighbor
        path.append(current)

        # Carve the path (make it water/floor)
        # NOTE: GridPoint.tilesprite is legacy - write to a TileLayer instead,
        # e.g. tile_layer.set(current, WATER_TILE)
        grid.at(current).tilesprite = WATER_TILE
        grid.at(current).walkable = True

    return path
# endregion

# region: influence
def create_influence_map(grid, player_pos, enemy_positions):
    """Create influence map for AI decision-making."""
    width, height = int(grid.grid_size[0]), int(grid.grid_size[1])

    # Player influence
    player_dijkstra = grid.get_dijkstra_map(player_pos)
    player_hmap = player_dijkstra.to_heightmap(unreachable=100.0)

    # Combined enemy influence (take minimum distance to any enemy)
    # Compute each enemy's heightmap once, outside the per-cell loop
    # (recomputing it width*height times per enemy is wasteful).
    enemy_hmaps = []
    for enemy_pos in enemy_positions:
        enemy_dijkstra = grid.get_dijkstra_map(enemy_pos)
        enemy_hmaps.append(enemy_dijkstra.to_heightmap(unreachable=100.0))

    influence = {}

    for y in range(height):
        for x in range(width):
            player_dist = player_hmap[(x, y)]

            # Find closest enemy
            min_enemy_dist = 100.0
            for enemy_hmap in enemy_hmaps:
                enemy_dist = enemy_hmap[(x, y)]
                min_enemy_dist = min(min_enemy_dist, enemy_dist)

            # Influence: positive = player controlled, negative = enemy
            influence[(x, y)] = min_enemy_dist - player_dist

    return influence
# endregion


# Use them once
spawn_enemies(grid, (2, 2), 12)
update_fog(grid, fog_layer, (2, 2))
path = carve_river(grid, (30, 35), (12, 30))
influence = create_influence_map(grid, (2, 2), [(30, 35), (35, 5)])
print(len(path), influence[(20, 20)])
