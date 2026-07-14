# mcrf: objects=[Caption,Color,Entity,Grid,InputState,Key,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Grid Camera Center - Pan the view
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Large grid, smaller viewport
grid = mcrfpy.Grid(
    grid_size=(30, 30),
    texture=mcrfpy.default_texture,
    pos=(212, 134),
    size=(600, 500)
)
scene.children.append(grid)

# Fill with pattern to show scrolling
for y in range(30):
    for x in range(30):
        cell = grid.at(x, y)
        if (x + y) % 2 == 0:
            cell.tilesprite = 48
        else:
            cell.tilesprite = 49

# Center camera on specific tile (15, 15)
grid.center_camera((15, 15))

# Add marker at center
marker = mcrfpy.Entity(
    grid_pos=(15, 15),
    texture=mcrfpy.default_texture,
    sprite_index=84
)
grid.entities.append(marker)

status = mcrfpy.Caption(text="WASD to pan camera - centered on (15, 15)", pos=(300, 660))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)

# Track camera position
camera_pos = [15, 15]

def on_key(key, action):
    if action != mcrfpy.InputState.PRESSED:
        return
    dx, dy = 0, 0
    if key == mcrfpy.Key.W: dy = -1
    elif key == mcrfpy.Key.S: dy = 1
    elif key == mcrfpy.Key.A: dx = -1
    elif key == mcrfpy.Key.D: dx = 1
    else: return

    camera_pos[0] = max(0, min(29, camera_pos[0] + dx))
    camera_pos[1] = max(0, min(29, camera_pos[1] + dy))
    grid.center_camera((camera_pos[0], camera_pos[1]))
    status.text = f"WASD to pan camera - centered on ({camera_pos[0]}, {camera_pos[1]})"

scene.on_key = on_key
