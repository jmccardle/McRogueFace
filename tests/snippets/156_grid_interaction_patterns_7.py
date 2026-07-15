# mcrf: objects=[Color,ColorLayer,Entity,Grid,Scene,TileLayer] verified=0.2.8-dev status=ok
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

# --- Path Preview ---
current_path_cells = []

def show_path_to(target_x, target_y):
    global current_path_cells
    # Clear previous path
    for cx, cy in current_path_cells:
        highlight.set((cx, cy), mcrfpy.Color(0, 0, 0, 0))
    current_path_cells = []

    # Calculate path
    path = grid.find_path(
        (int(player.grid_x), int(player.grid_y)),
        (target_x, target_y)
    )
    if not path:
        return

    # Draw path cells
    i = 0
    while len(path) > 0:
        step = path.walk()
        x, y = int(step.x), int(step.y)
        alpha = max(30, 100 - (i * 5))
        highlight.set((x, y), mcrfpy.Color(100, 200, 255, alpha))
        current_path_cells.append((x, y))
        i += 1

def on_cell_enter(cell_pos):
    show_path_to(int(cell_pos.x), int(cell_pos.y))

grid.on_cell_enter = on_cell_enter

# Exercise the pattern once so the layer content isn't dead code
show_path_to(15, 12)
