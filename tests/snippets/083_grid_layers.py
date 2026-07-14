# mcrf: objects=[Caption,Color,ColorLayer,Grid,Scene,TileLayer] verified=0.2.8-dev@a7ba486 status=ok
# Grid Layers - Multiple tile layers
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

# Base layer - floor
for y in range(12):
    for x in range(16):
        grid.at(x, y).tilesprite = 48

# Add a color overlay layer
color_layer = mcrfpy.ColorLayer(z_index=1, name="highlights")
grid.add_layer(color_layer)

# Highlight some cells with color
for x in range(4, 12):
    color_layer.set((x, 5), mcrfpy.Color(100, 200, 255, 100))
    color_layer.set((x, 6), mcrfpy.Color(100, 200, 255, 100))

# Add a tile layer for decorations
tile_layer = mcrfpy.TileLayer(z_index=2, name="decorations", texture=mcrfpy.default_texture)
grid.add_layer(tile_layer)

# Add some decoration tiles
tile_layer.set((5, 3), 17)   # Chest
tile_layer.set((10, 3), 65)  # Door
tile_layer.set((7, 8), 80)   # Water

status = mcrfpy.Caption(text="Grid with multiple layers: base + color + decoration", pos=(280, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
