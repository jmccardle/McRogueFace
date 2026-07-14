# mcrf: objects=[Caption,Color,Entity,Grid,InputState,Key,Scene] verified=0.2.8-dev@a7ba486 status=ok
# FOV Perspective Entity - View from entity's perspective
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

# Dungeon layout
for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        if x == 0 or x == 15 or y == 0 or y == 11:
            cell.tilesprite = 1
            cell.transparent = False
        elif (x == 4 or x == 12) and y > 2 and y < 9:
            cell.tilesprite = 1
            cell.transparent = False
        else:
            cell.tilesprite = 48
            cell.transparent = True

# Player entity
player = mcrfpy.Entity(grid_pos=(8, 6), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(player)

# Set perspective entity - FOV follows this entity
grid.perspective = player
grid.fov_radius = 6

status = mcrfpy.Caption(text="WASD to move, FOV follows player", pos=(350, 700))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)

def on_key(key, action):
    if action != mcrfpy.InputState.PRESSED:
        return
    x, y = player.grid_x, player.grid_y
    if key == mcrfpy.Key.W: player.grid_pos = (x, y - 1)
    elif key == mcrfpy.Key.S: player.grid_pos = (x, y + 1)
    elif key == mcrfpy.Key.A: player.grid_pos = (x - 1, y)
    elif key == mcrfpy.Key.D: player.grid_pos = (x + 1, y)

scene.on_key = on_key
