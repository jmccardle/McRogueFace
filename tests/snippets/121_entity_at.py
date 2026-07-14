# mcrf: objects=[Caption,Color,Entity,Grid,InputState,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Entity At - Query entity's view of grid
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
        cell = grid.at(x, y)
        if x == 8 and y > 2 and y < 9:
            cell.tilesprite = 1
            cell.transparent = False
        else:
            cell.tilesprite = 48
            cell.transparent = True

player = mcrfpy.Entity(grid_pos=(4, 6), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(player)

grid.perspective = player
grid.fov_radius = 8

status = mcrfpy.Caption(text="Click to query entity's view", pos=(350, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)

def on_cell_click(pos, button, action):
    if action == mcrfpy.InputState.PRESSED:
        x, y = int(pos.x), int(pos.y)
        # Query from entity's perspective
        state = player.at(x, y)
        if state:
            status.text = f"({x},{y}): visible={state.visible}, discovered={state.discovered}"
        else:
            status.text = f"({x},{y}): out of bounds"

grid.on_cell_click = on_cell_click
