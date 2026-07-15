# mcrf: objects=[Grid,Scene,TileLayer] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("tilelayer_demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(512, 384),
)
scene.children.append(grid)

# Create standalone, then attach with Grid.add_layer() (a layer OBJECT, not a string)
floor_layer = mcrfpy.TileLayer(z_index=0, texture=mcrfpy.default_texture)
grid.add_layer(floor_layer)

wall_layer = mcrfpy.TileLayer(z_index=1, texture=mcrfpy.default_texture)
grid.add_layer(wall_layer)

# Fill entire layer with one tile
floor_layer.fill(0)

# Set individual tile sprites
floor_layer.set((5, 5), 42)

# Fill rectangular region
wall_layer.fill_rect((0, 0), (16, 1), 16)  # Top wall

# Get tile at position
sprite_idx = floor_layer.at((5, 5))
assert sprite_idx == 42
