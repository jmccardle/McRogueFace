# mcrf: objects=[Caption,Color,Entity,Grid,InputState,Key,Scene,Timer] verified=0.2.8-dev@a7ba486 status=ok
# Game Turn-Based - Simple turn system
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

for y in range(12):
    for x in range(16):
        grid.at(x, y).tilesprite = 48
        grid.at(x, y).walkable = True

# Player
player = mcrfpy.Entity(grid_pos=(3, 6), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(player)

# Enemy
enemy = mcrfpy.Entity(grid_pos=(12, 6), texture=mcrfpy.default_texture, sprite_index=112)
grid.entities.append(enemy)

turn = "player"
status = mcrfpy.Caption(text="Player turn - WASD to move", pos=(320, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)

def enemy_turn(timer, runtime):
    global turn
    # Simple AI: move toward player
    dx = 1 if player.grid_x > enemy.grid_x else -1 if player.grid_x < enemy.grid_x else 0
    dy = 1 if player.grid_y > enemy.grid_y else -1 if player.grid_y < enemy.grid_y else 0
    new_x = enemy.grid_x + dx
    new_y = enemy.grid_y + dy
    if grid.at(new_x, new_y).walkable:
        enemy.grid_pos = (new_x, new_y)
    turn = "player"
    status.text = "Player turn - WASD to move"

def on_key(key, action):
    global turn
    if action != mcrfpy.InputState.PRESSED or turn != "player":
        return

    x, y = player.grid_x, player.grid_y
    nx, ny = x, y
    if key == mcrfpy.Key.W: ny = y - 1
    elif key == mcrfpy.Key.S: ny = y + 1
    elif key == mcrfpy.Key.A: nx = x - 1
    elif key == mcrfpy.Key.D: nx = x + 1
    else: return

    if 0 <= nx < 16 and 0 <= ny < 12 and grid.at(nx, ny).walkable:
        player.grid_pos = (nx, ny)
        turn = "enemy"
        status.text = "Enemy turn..."
        mcrfpy.Timer("enemy", enemy_turn, 500, once=True)

scene.on_key = on_key
