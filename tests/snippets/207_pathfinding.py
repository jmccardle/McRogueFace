# mcrf: objects=[Entity,Grid,InputState,Key,Scene] verified=0.2.8-dev status=ok
import mcrfpy
import random

# Setup
scene = mcrfpy.Scene("game")
mcrfpy.current_scene = scene

# Create grid
grid = mcrfpy.Grid(
    grid_size=(40, 30),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(800, 600)
)
scene.children.append(grid)

# Initialize map
for y in range(30):
    for x in range(40):
        point = grid.at(x, y)
        if x == 0 or x == 39 or y == 0 or y == 29:
            point.tilesprite = 1
            point.walkable = False
        else:
            point.tilesprite = 0
            point.walkable = True

# Add some obstacles
for _ in range(50):
    x = random.randint(2, 37)
    y = random.randint(2, 27)
    point = grid.at(x, y)
    point.tilesprite = 1
    point.walkable = False

# Create player
player = mcrfpy.Entity(grid_pos=(5, 5), texture=mcrfpy.default_texture, sprite_index=64)
grid.entities.append(player)

# Create enemies
enemies = []
for _ in range(5):
    while True:
        x = random.randint(20, 35)
        y = random.randint(5, 25)
        if grid.at(x, y).walkable:
            break

    enemy = mcrfpy.Entity(grid_pos=(x, y), texture=mcrfpy.default_texture, sprite_index=111)
    grid.entities.append(enemy)
    enemies.append(enemy)

# Enemy AI
def update_enemies():
    """Move all enemies toward player."""
    # Use Dijkstra for efficiency with multiple enemies; cached by root position
    dijkstra = grid.get_dijkstra_map(player.grid_pos)

    for enemy in enemies:
        dist = dijkstra.distance(enemy.grid_pos)

        if dist is not None and dist <= 15:  # Only chase if close enough
            step = dijkstra.step_from(enemy.grid_pos)

            if step is not None:
                next_x, next_y = int(step.x), int(step.y)

                # Don't walk into player (would be attack in real game)
                if next_x == player.grid_x and next_y == player.grid_y:
                    continue

                # Don't walk into other enemies
                blocked = False
                for other in enemies:
                    if other != enemy:
                        if other.grid_x == next_x and other.grid_y == next_y:
                            blocked = True
                            break

                if not blocked:
                    enemy.grid_pos = (next_x, next_y)

# Player movement
def on_key(key, action):
    if action != mcrfpy.InputState.PRESSED:
        return

    dx, dy = 0, 0

    if key == mcrfpy.Key.UP or key == mcrfpy.Key.W: dy = -1
    elif key == mcrfpy.Key.DOWN or key == mcrfpy.Key.S: dy = 1
    elif key == mcrfpy.Key.LEFT or key == mcrfpy.Key.A: dx = -1
    elif key == mcrfpy.Key.RIGHT or key == mcrfpy.Key.D: dx = 1
    else:
        return

    new_x = player.grid_x + dx
    new_y = player.grid_y + dy

    if grid.at(new_x, new_y).walkable:
        player.grid_pos = (new_x, new_y)
        grid.center = player.pos

        # Enemy turn after player moves. get_dijkstra_map() is cached by root
        # position, so a moved root simply produces a fresh map on next call.
        update_enemies()

scene.on_key = on_key

# Initialize camera
grid.center = player.pos
