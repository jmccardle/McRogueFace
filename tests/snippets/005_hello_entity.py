# mcrf: objects=[Entity,Grid,Scene] verified=0.2.8-dev status=ok
# Hello Entity - Add entities to a grid
import mcrfpy

scene = mcrfpy.Scene("hello")
mcrfpy.current_scene = scene

# Create grid filling the screen
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

# Add a player entity
player = mcrfpy.Entity(
    grid_pos=(8, 6),
    texture=mcrfpy.default_texture,
    sprite_index=84  # Knight
)
grid.entities.append(player)
