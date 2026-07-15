# mcrf: objects=[Color,ColorLayer,Entity,Grid,InputState,MouseButton,Scene,TileLayer] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("game")
ui = scene.children

texture = mcrfpy.default_texture
terrain = mcrfpy.TileLayer(name="terrain", z_index=-2, texture=texture)
highlight = mcrfpy.ColorLayer(name="highlight", z_index=-1)
overlay = mcrfpy.ColorLayer(name="overlay", z_index=1)

grid = mcrfpy.Grid(
    grid_size=(20, 15),
    pos=(50, 50),
    size=(640, 480),
    layers=[terrain, highlight, overlay]
)
grid.fill_color = mcrfpy.Color(20, 20, 30)
ui.append(grid)

player = mcrfpy.Entity(grid_pos=(10, 7), sprite_index=0)
grid.entities.append(player)

mcrfpy.current_scene = scene

# --- Cell Click Actions ---
def show_cell_info(x, y, point):
    print(f"Cell ({x}, {y}): walkable={point.walkable}")

def on_cell_click(cell_pos, button, action):
    x, y = int(cell_pos.x), int(cell_pos.y)
    point = grid.at(x, y)

    if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.PRESSED:
        if point.walkable:
            player.grid_x = x
            player.grid_y = y

    elif button == mcrfpy.MouseButton.RIGHT and action == mcrfpy.InputState.PRESSED:
        # Inspect cell
        show_cell_info(x, y, point)

    elif button == mcrfpy.MouseButton.MIDDLE and action == mcrfpy.InputState.PRESSED:
        # Toggle walkability (level editor)
        point.walkable = not point.walkable

grid.on_cell_click = on_cell_click
