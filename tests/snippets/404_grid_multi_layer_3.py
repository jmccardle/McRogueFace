# mcrf: objects=[Color,ColorLayer,Grid,Scene,TileLayer] verified=0.3.6 status=ok
import mcrfpy

scene = mcrfpy.Scene("layer-types")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(
    grid_size=(20, 20),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(1024, 768),
    zoom=3.0
)
scene.children.append(grid)

TILE_FLOOR = 48
TILE_TABLE = 100
TILE_CHAIR = 101
TILE_CHEST = 103

base = mcrfpy.TileLayer(z_index=0, name="base", texture=mcrfpy.default_texture)
grid.add_layer(base)
base.fill(TILE_FLOOR)

# region: tile-layers
# Create tile layer
decor = mcrfpy.TileLayer(z_index=1, name="decor", texture=mcrfpy.default_texture)
grid.add_layer(decor)

# Set decoration tiles
decor.set((10, 10), TILE_TABLE)
decor.set((11, 10), TILE_CHAIR)
decor.set((10, 15), TILE_CHEST)

# Clear a tile (make transparent) - TileLayer has no clear(); set index -1 instead
decor.set((10, 10), -1)
# endregion

# region: color-layers
# Create color layer
effects = mcrfpy.ColorLayer(z_index=2, name="effects")
grid.add_layer(effects)

# Set color at position - pos is always a single (x, y) tuple, not two args
effects.set((5, 5), mcrfpy.Color(255, 0, 0, 128))  # Red overlay

# Clear color at one cell
effects.set((5, 5), mcrfpy.Color(0, 0, 0, 0))  # Transparent

# Clear entire layer - ColorLayer has no clear(); fill() with a transparent color instead
effects.fill(mcrfpy.Color(0, 0, 0, 0))
# endregion
