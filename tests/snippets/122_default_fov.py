# mcrf: objects=[Caption,Color,Entity,FOV,Frame,Grid,Scene] verified=0.2.8-dev status=ok
# Default FOV - Set default algorithm
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Display current default
current = mcrfpy.default_fov
_caption = mcrfpy.Caption(
    text=f"Current default_fov: {current}",
    pos=(350, 100))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

# Change default
mcrfpy.default_fov = mcrfpy.FOV.SHADOW

scene.children.append(mcrfpy.Caption(
    text=f"Changed to: {mcrfpy.default_fov}",
    pos=(380, 200)
))

# Create grid with default FOV
grid = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(212, 280),
    size=(600, 400)
)
scene.children.append(grid)

for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        if x == 8 and y > 2 and y < 9:
            cell.tilesprite = 1
            cell.transparent = False
        else:
            cell.tilesprite = 48
            cell.transparent = True

player = mcrfpy.Entity(grid_pos=(4, 6), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(player)
grid.perspective = player
grid.fov_radius = 8

status = mcrfpy.Caption(text="New grids use the default FOV algorithm", pos=(330, 700))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
