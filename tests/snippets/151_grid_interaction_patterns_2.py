# mcrf: objects=[Color,ColorLayer,Entity,Grid,Scene,TileLayer] verified=0.2.8-dev status=ok
import mcrfpy

# Scene setup
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

# --- Cell Hover Highlighting ---
current_highlight = [None]

def on_cell_enter(cell_pos):
    x, y = int(cell_pos.x), int(cell_pos.y)
    highlight.set((x, y), mcrfpy.Color(255, 255, 255, 40))
    current_highlight[0] = (x, y)

def on_cell_exit(cell_pos):
    x, y = int(cell_pos.x), int(cell_pos.y)
    highlight.set((x, y), mcrfpy.Color(0, 0, 0, 0))
    current_highlight[0] = None

grid.on_cell_enter = on_cell_enter
grid.on_cell_exit = on_cell_exit
