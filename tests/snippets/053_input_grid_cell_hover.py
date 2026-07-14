# mcrf: objects=[Caption,Color,ColorLayer,Grid,Scene] verified=0.2.8-dev status=ok
# Input Grid Cell Hover - Hover over grid cells
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

# Add color layer for hover highlighting
hover_layer = mcrfpy.ColorLayer(z_index=1, name="hover")
grid.add_layer(hover_layer)

for y in range(12):
    for x in range(16):
        grid.at(x, y).tilesprite = 48

status = mcrfpy.Caption(text="Hover over cells", pos=(420, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)

def on_cell_enter(cell_pos):
    x, y = int(cell_pos.x), int(cell_pos.y)
    hover_layer.set((x, y), mcrfpy.Color(100, 200, 255, 180))
    status.text = f"Hovering cell ({x}, {y})"

def on_cell_exit(cell_pos):
    x, y = int(cell_pos.x), int(cell_pos.y)
    hover_layer.set((x, y), mcrfpy.Color(0, 0, 0, 0))

grid.on_cell_enter = on_cell_enter
grid.on_cell_exit = on_cell_exit
