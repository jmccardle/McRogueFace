# mcrf: objects=[Caption,Color,ColorLayer,Grid,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Bresenham Line - Draw lines on grid
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(
    grid_size=(20, 15),
    texture=mcrfpy.default_texture,
    pos=(112, 84),
    size=(800, 600)
)
scene.children.append(grid)

# Add color layer for line visualization
line_layer = mcrfpy.ColorLayer(z_index=1, name="line")
grid.add_layer(line_layer)

# Fill with floor
for y in range(15):
    for x in range(20):
        grid.at(x, y).tilesprite = 48

# Draw lines using bresenham
start = (2, 2)
end = (17, 12)

# Get all cells along the line
line_cells = mcrfpy.bresenham(start, end)

# Highlight the line
for x, y in line_cells:
    line_layer.set((x, y), mcrfpy.Color(255, 200, 100, 200))

# Mark start and end
line_layer.set((start[0], start[1]), mcrfpy.Color(100, 255, 100, 255))
line_layer.set((end[0], end[1]), mcrfpy.Color(255, 100, 100, 255))

status = mcrfpy.Caption(
    text=f"Bresenham line: {len(line_cells)} cells - Green=start, Red=end",
    pos=(280, 700)
)
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
