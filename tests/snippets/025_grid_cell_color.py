# mcrf: objects=[Caption,Color,ColorLayer,Grid,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Grid Cell Colors - Use color layer for cell colors
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

# Set tiles
for y in range(12):
    for x in range(16):
        grid.at(x, y).tilesprite = 48

# Add a color layer for tinting
color_layer = mcrfpy.ColorLayer(z_index=1, name="tint")
grid.add_layer(color_layer)

# Create colorful gradient pattern using color layer
for y in range(12):
    for x in range(16):
        # Rainbow gradient based on position
        r = int(255 * x / 16)
        g = int(255 * y / 12)
        b = int(255 * (16 - x) / 16)
        color_layer.set((x, y), mcrfpy.Color(r, g, b, 180))

title = mcrfpy.Caption(text="Per-Cell Color Tinting via Layer", pos=(350, 720))
title.fill_color = mcrfpy.Color(255, 220, 100)
title.outline = 2
title.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(title)
