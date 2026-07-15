# mcrf: objects=[Color,ColorLayer,Entity,Grid,Scene,TileLayer] verified=0.2.8-dev status=ok
import mcrfpy

# Scene setup
scene = mcrfpy.Scene("game")
ui = scene.children

# Load tileset texture (use your own atlas in a real game)
texture = mcrfpy.default_texture

# Create layers
terrain = mcrfpy.TileLayer(name="terrain", z_index=-2, texture=texture)
highlight = mcrfpy.ColorLayer(name="highlight", z_index=-1)
overlay = mcrfpy.ColorLayer(name="overlay", z_index=1)

# Create grid with layers
grid = mcrfpy.Grid(
    grid_size=(20, 15),
    pos=(50, 50),
    size=(640, 480),
    layers=[terrain, highlight, overlay]
)
grid.fill_color = mcrfpy.Color(20, 20, 30)
ui.append(grid)

# Create player entity
player = mcrfpy.Entity(grid_pos=(10, 7), sprite_index=0)
grid.entities.append(player)

# Wire up events (patterns below fill these in)
# grid.on_cell_click = ...
# grid.on_cell_enter = ...
# grid.on_cell_exit = ...

mcrfpy.current_scene = scene
