# mcrf: objects=[Caption,Color,ColorLayer,Grid,InputState,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Grid Point State - Cell properties
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

# Add visual layer for highlighting
highlight_layer = mcrfpy.ColorLayer(z_index=1, name="highlight")
grid.add_layer(highlight_layer)

# Setup cells with different properties
for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        cell.tilesprite = 48
        cell.walkable = True
        cell.transparent = True

# Mark some cells as walls
for i in range(5):
    cell = grid.at(8, 3 + i)
    cell.tilesprite = 1
    cell.walkable = False
    cell.transparent = False

# Highlight left half as "explored"
for x in range(8):
    for y in range(12):
        highlight_layer.set((x, y), mcrfpy.Color(100, 200, 100, 80))

# Show cell info on click
status = mcrfpy.Caption(text="Click a cell to see properties", pos=(350, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)

def on_cell_click(pos, button, action):
    if action == mcrfpy.InputState.PRESSED:
        x, y = int(pos.x), int(pos.y)
        if 0 <= x < 16 and 0 <= y < 12:
            cell = grid.at(x, y)
            status.text = f"Cell ({x},{y}): walkable={cell.walkable}, transparent={cell.transparent}"

grid.on_cell_click = on_cell_click
