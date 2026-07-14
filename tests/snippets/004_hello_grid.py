# mcrf: objects=[Grid,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Hello Grid - Create a tile-based grid
import mcrfpy

scene = mcrfpy.Scene("hello")
mcrfpy.current_scene = scene

# Create a grid that fills the screen
# zoom=4.0 with 16x16 texture means each tile is 64x64 pixels
# 16 tiles * 64 pixels = 1024, 12 tiles * 64 pixels = 768
grid = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(1024, 768),
    zoom=4.0
)
scene.children.append(grid)

# Fill with floor tiles
for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        cell.tilesprite = 48  # Floor tile
        cell.walkable = True
