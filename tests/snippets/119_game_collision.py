# mcrf: objects=[Caption,Color,Entity,Grid,InputState,Key,Scene] verified=0.2.8-dev status=ok
# Game Collision - Simple collision detection
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

# Create walls and floor
for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        if x == 0 or x == 15 or y == 0 or y == 11:
            cell.tilesprite = 1
            cell.walkable = False
        elif x == 8 and y > 2 and y < 9:
            cell.tilesprite = 1
            cell.walkable = False
        else:
            cell.tilesprite = 48
            cell.walkable = True

# Player
player = mcrfpy.Entity(grid_pos=(4, 6), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(player)

# Enemies
enemies = []
for pos in [(12, 3), (12, 8)]:
    e = mcrfpy.Entity(grid_pos=pos, texture=mcrfpy.default_texture, sprite_index=112)
    grid.entities.append(e)
    enemies.append(e)

status = mcrfpy.Caption(text="Move with WASD - Avoid enemies!", pos=(350, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)

def check_collision():
    for e in enemies:
        if e.grid_x == player.grid_x and e.grid_y == player.grid_y:
            status.text = "COLLISION! Game Over!"
            status.fill_color = mcrfpy.Color(255, 100, 100)
            return True
    return False

def on_key(key, action):
    if action != mcrfpy.InputState.PRESSED: return
    x, y = player.grid_x, player.grid_y
    nx, ny = x, y
    if key == mcrfpy.Key.W: ny -= 1
    elif key == mcrfpy.Key.S: ny += 1
    elif key == mcrfpy.Key.A: nx -= 1
    elif key == mcrfpy.Key.D: nx += 1

    if grid.at(nx, ny).walkable:
        player.grid_pos = (nx, ny)
        check_collision()

scene.on_key = on_key
