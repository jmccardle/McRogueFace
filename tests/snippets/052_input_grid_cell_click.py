# mcrf: objects=[Caption,Color,ColorLayer,Grid,InputState,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Input Grid Cell Click - Click on grid cells
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

# Add color layer for click highlighting
click_layer = mcrfpy.ColorLayer(z_index=1, name="clicks")
grid.add_layer(click_layer)

# Fill with floor
for y in range(12):
    for x in range(16):
        grid.at(x, y).tilesprite = 48

status = mcrfpy.Caption(text="Click on cells to highlight", pos=(350, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)

# Track clicked cells
clicked = set()

def on_cell_click(cell_pos, button, action):
    if action == mcrfpy.InputState.PRESSED:
        x, y = int(cell_pos.x), int(cell_pos.y)
        if (x, y) in clicked:
            # Clear highlight
            click_layer.set((x, y), mcrfpy.Color(0, 0, 0, 0))
            clicked.discard((x, y))
        else:
            # Add highlight
            click_layer.set((x, y), mcrfpy.Color(255, 200, 100, 180))
            clicked.add((x, y))
        status.text = f"Clicked cell ({x}, {y})"

grid.on_cell_click = on_cell_click
