# mcrf: objects=[ColorLayer,Grid,Scene,TileLayer] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("layers")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(1024, 768),
    zoom=4.0
)
scene.children.append(grid)

TILE_FLOOR = 48
TILE_RUG = 65

# Add layers with different z-indices
base_layer = mcrfpy.TileLayer(z_index=0, name="base", texture=mcrfpy.default_texture)     # Base terrain
decor_layer = mcrfpy.TileLayer(z_index=1, name="decor", texture=mcrfpy.default_texture)   # Decorations
effect_layer = mcrfpy.ColorLayer(z_index=2, name="effects")                               # Color effects
ui_layer = mcrfpy.ColorLayer(z_index=3, name="ui")                                        # UI highlights

for layer in (base_layer, decor_layer, effect_layer, ui_layer):
    grid.add_layer(layer)

# Set tiles on each layer
base_layer.set((5, 5), TILE_FLOOR)
decor_layer.set((5, 5), TILE_RUG)  # Rug on top of floor
