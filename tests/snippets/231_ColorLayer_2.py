# mcrf: objects=[Caption,Color,ColorLayer,Grid,HeightMap,Scene] verified=0.2.8-dev status=ok
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

heightmap = mcrfpy.HeightMap((16, 12))
heightmap.fill(0.0)
for x in range(16):
    heightmap[x, 6] = 1.0  # simple ramp so both ranges have cells

color_layer = mcrfpy.ColorLayer(z_index=0, name="terrain")
grid.add_layer(color_layer)

# Color by height threshold (one call per range)
color_layer.apply_threshold(heightmap, range=(0.0, 0.5), color=mcrfpy.Color(0, 0, 100))   # Water (blue)
color_layer.apply_threshold(heightmap, range=(0.5, 1.0), color=mcrfpy.Color(0, 100, 0))   # Land (green)

# Or use a smooth gradient across the whole range
color_layer.apply_gradient(
    heightmap,
    range=(0.0, 1.0),
    color_low=mcrfpy.Color(0, 0, 150),      # Low = deep water
    color_high=mcrfpy.Color(200, 200, 200)  # High = mountain
)

title = mcrfpy.Caption(text="ColorLayer heightmap visualization", pos=(280, 720))
scene.children.append(title)
