# mcrf: objects=[Color,ColorLayer,Entity,Grid,InputState,Key,Scene,TileLayer] verified=0.2.8-dev status=ok
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

# --- WASD Movement ---
move_map = {
    mcrfpy.Key.W: (0, -1),
    mcrfpy.Key.A: (-1, 0),
    mcrfpy.Key.S: (0, 1),
    mcrfpy.Key.D: (1, 0),
}

def handle_key(key, action):
    if action != mcrfpy.InputState.PRESSED:
        return
    if key in move_map:
        dx, dy = move_map[key]
        new_x = int(player.grid_x + dx)
        new_y = int(player.grid_y + dy)
        grid_w, grid_h = player.grid.grid_size
        if 0 <= new_x < grid_w and 0 <= new_y < grid_h:
            point = player.grid.at(new_x, new_y)
            if point.walkable:
                player.grid_x = new_x
                player.grid_y = new_y

scene.on_key = handle_key
