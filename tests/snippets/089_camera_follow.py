# mcrf: objects=[Caption,Color,Easing,Entity,Grid,InputState,Key,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Camera Follow - Camera tracks entity
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(
    grid_size=(30, 30),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(1024, 768),
    zoom=2.0
)
scene.children.append(grid)

# Create large map
for y in range(30):
    for x in range(30):
        cell = grid.at(x, y)
        if x == 0 or x == 29 or y == 0 or y == 29:
            cell.tilesprite = 1
            cell.walkable = False
        elif (x + y) % 7 == 0 and x > 1 and x < 28 and y > 1 and y < 28:
            cell.tilesprite = 1
            cell.walkable = False
        else:
            cell.tilesprite = 48
            cell.walkable = True

# Player in center
player = mcrfpy.Entity(grid_pos=(15, 15), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(player)

# Center camera on player
grid.center_camera((15, 15))

def on_key(key, action):
    if action != mcrfpy.InputState.PRESSED:
        return
    x, y = player.grid_x, player.grid_y
    nx, ny = x, y
    if key == mcrfpy.Key.W: ny -= 1
    elif key == mcrfpy.Key.S: ny += 1
    elif key == mcrfpy.Key.A: nx -= 1
    elif key == mcrfpy.Key.D: nx += 1
    else: return

    if grid.at(nx, ny).walkable:
        player.grid_pos = (nx, ny)
        # Animate camera to follow (center uses pixel coords: tile * 16 for 16x16 sprites)
        grid.animate("center_x", nx * 16 + 8, 0.2, mcrfpy.Easing.EASE_OUT)
        grid.animate("center_y", ny * 16 + 8, 0.2, mcrfpy.Easing.EASE_OUT)

scene.on_key = on_key

status = mcrfpy.Caption(text="WASD - Camera follows player", pos=(380, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
