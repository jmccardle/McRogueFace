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

# --- Entity Selection ---
selected = [None]

def select_entity(entity):
    # Clear previous selection
    if selected[0]:
        ex, ey = int(selected[0].grid_x), int(selected[0].grid_y)
        overlay.set((ex, ey), mcrfpy.Color(0, 0, 0, 0))

    selected[0] = entity

    if entity:
        overlay.set((int(entity.grid_x), int(entity.grid_y)),
                     mcrfpy.Color(255, 200, 0, 80))

def on_cell_click(cell_pos, button, action):
    if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.PRESSED:
        x, y = int(cell_pos.x), int(cell_pos.y)
        for entity in grid.entities:
            if int(entity.grid_x) == x and int(entity.grid_y) == y:
                select_entity(entity)
                return
        select_entity(None)

grid.on_cell_click = on_cell_click
