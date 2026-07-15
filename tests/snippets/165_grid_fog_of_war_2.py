# mcrf: objects=[Color,ColorLayer,Entity,Grid,InputState,Key,Scene] verified=0.2.8-dev status=ok
import mcrfpy

# Scene setup
scene = mcrfpy.Scene("dungeon")
mcrfpy.current_scene = scene

# Load tileset
texture = mcrfpy.default_texture

# Create grid
grid = mcrfpy.Grid(grid_size=(50, 50), texture=texture, pos=(0, 0), size=(800, 600))
scene.children.append(grid)

# Initialize dungeon - walls block sight and movement
for x in range(50):
    for y in range(50):
        point = grid.at(x, y)
        if x == 0 or y == 0 or x == 49 or y == 49:
            # Outer walls
            point.tilesprite = 1  # Wall tile
            point.walkable = False
            point.transparent = False
        else:
            # Floor tiles
            point.tilesprite = 0  # Floor tile
            point.walkable = True
            point.transparent = True

# Add some pillars to test LOS blocking
pillars = [(10, 10), (20, 15), (30, 25), (15, 35)]
for px, py in pillars:
    point = grid.at(px, py)
    point.tilesprite = 2  # Pillar tile
    point.walkable = False
    point.transparent = False

# Create player
player = mcrfpy.Entity(grid_pos=(25, 25), texture=texture, sprite_index=64)  # Player sprite
grid.entities.append(player)

# Add a custom fog of war layer bound to the player
fog_layer = mcrfpy.ColorLayer(z_index=-1, name="fog")
grid.add_layer(fog_layer)
fog_layer.apply_perspective(
    entity=player,
    visible=mcrfpy.Color(0, 0, 0, 0),
    discovered=mcrfpy.Color(20, 20, 40, 160),
    unknown=mcrfpy.Color(0, 0, 0, 255)
)

grid.fov_radius = 8

def update_visibility():
    """Recompute FOV and repaint the bound fog layer."""
    player.update_visibility()

def handle_input(key, action):
    if action != mcrfpy.InputState.PRESSED:
        return

    x, y = player.grid_x, player.grid_y
    dx, dy = 0, 0

    if key in (mcrfpy.Key.W, mcrfpy.Key.Up):
        dy = -1
    elif key in (mcrfpy.Key.S, mcrfpy.Key.Down):
        dy = 1
    elif key in (mcrfpy.Key.A, mcrfpy.Key.Left):
        dx = -1
    elif key in (mcrfpy.Key.D, mcrfpy.Key.Right):
        dx = 1

    if dx != 0 or dy != 0:
        new_x, new_y = x + dx, y + dy
        cell = grid.at(new_x, new_y)
        if cell is not None and cell.walkable:
            player.grid_pos = (new_x, new_y)
            update_visibility()

scene.on_key = handle_input

# Initial FOV calculation
update_visibility()

# Center camera on player
grid.center_camera((player.grid_x + 0.5, player.grid_y + 0.5))
