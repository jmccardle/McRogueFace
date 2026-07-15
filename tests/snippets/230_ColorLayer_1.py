# mcrf: objects=[Caption,Color,ColorLayer,Grid,Scene] verified=0.2.8-dev status=ok
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

for y in range(12):
    for x in range(16):
        grid.at(x, y).tilesprite = 48

# Create standalone, then attach to a Grid
color_layer = mcrfpy.ColorLayer(z_index=1, name="tint")
grid.add_layer(color_layer)

# Set individual cell colors
color_layer.set((5, 5), mcrfpy.Color(255, 0, 0, 128))  # Semi-transparent red

# Fill entire layer
color_layer.fill(mcrfpy.Color(0, 0, 0, 200))  # Dark overlay

# Fill rectangular region
color_layer.fill_rect((2, 2), (4, 4), mcrfpy.Color(50, 50, 100))

# Get cell color
cell_color = color_layer.at((5, 5))
assert isinstance(cell_color, mcrfpy.Color)

# FOV visualization: paint cells by visibility from a source position
color_layer.draw_fov((8, 6), radius=8)

title = mcrfpy.Caption(text="ColorLayer quick reference", pos=(300, 720))
scene.children.append(title)
