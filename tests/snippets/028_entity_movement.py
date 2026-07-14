# mcrf: objects=[Caption,Color,Entity,Grid,InputState,Key,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Entity Movement - Move entities on grid
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

# Floor tiles
for y in range(12):
    for x in range(16):
        grid.at(x, y).tilesprite = 48

# Create player entity
player = mcrfpy.Entity(
    grid_pos=(8, 6),
    texture=mcrfpy.default_texture,
    sprite_index=84
)
grid.entities.append(player)

# Movement with keyboard
def on_key(key, action):
    if action != mcrfpy.InputState.PRESSED:
        return
    x, y = player.grid_x, player.grid_y
    if key == mcrfpy.Key.UP or key == mcrfpy.Key.W:
        player.grid_pos = (x, y - 1)
    elif key == mcrfpy.Key.DOWN or key == mcrfpy.Key.S:
        player.grid_pos = (x, y + 1)
    elif key == mcrfpy.Key.LEFT or key == mcrfpy.Key.A:
        player.grid_pos = (x - 1, y)
    elif key == mcrfpy.Key.RIGHT or key == mcrfpy.Key.D:
        player.grid_pos = (x + 1, y)

scene.on_key = on_key

status = mcrfpy.Caption(text="WASD or Arrow keys to move", pos=(380, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
