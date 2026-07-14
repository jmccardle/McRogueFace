# mcrf: objects=[Caption,Color,Entity,Grid,Scene,Timer,Vector] verified=0.2.8-dev@a7ba486 status=ok
# Entity Draw Position - Smooth sub-tile positioning
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

# Entity at grid position with draw offset
entity = mcrfpy.Entity(
    grid_pos=(8, 6),
    texture=mcrfpy.default_texture,
    sprite_index=84
)
grid.entities.append(entity)

# Animate the draw position for smooth movement
offset = 0.0
direction = 1

def animate_offset(timer, runtime):
    global offset, direction
    offset += 0.02 * direction
    if offset > 0.5:
        direction = -1
    elif offset < -0.5:
        direction = 1
    entity.draw_pos = mcrfpy.Vector(8 + offset, 6)

timer = mcrfpy.Timer("move", animate_offset, 16)

status = mcrfpy.Caption(text="draw_pos allows sub-tile positioning", pos=(340, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
