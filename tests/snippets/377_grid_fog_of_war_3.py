# mcrf: objects=[Color,ColorLayer,Entity,FOV,Grid,Perspective,Scene] verified=0.3.6 status=ok
import mcrfpy

scene = mcrfpy.Scene("game")
mcrfpy.current_scene = scene

texture = mcrfpy.default_texture
grid = mcrfpy.Grid(grid_size=(50, 50), texture=texture, pos=(0, 0), size=(800, 600))
scene.children.append(grid)

for x in range(50):
    for y in range(50):
        point = grid.at(x, y)
        if x == 0 or y == 0 or x == 49 or y == 49:
            point.tilesprite = 1
            point.walkable = False
            point.transparent = False
        else:
            point.tilesprite = 0
            point.walkable = True
            point.transparent = True

for px, py in [(10, 10), (20, 15), (30, 25), (15, 35)]:
    point = grid.at(px, py)
    point.tilesprite = 2
    point.walkable = False
    point.transparent = False

player = mcrfpy.Entity(grid_pos=(25, 25), texture=texture, sprite_index=64)
grid.entities.append(player)
grid.fov_radius = 8

# Values the fences below use
x, y = 25, 25
target_x, target_y = 28, 25

# region: fov
def update_fov():
    """Recompute FOV from the player's current position."""
    player.update_visibility()

# Call after every player move
def move_player(dx, dy):
    x, y = player.grid_x, player.grid_y
    new_x, new_y = x + dx, y + dy

    # Check if destination is walkable
    cell = grid.at(new_x, new_y)
    if cell is not None and cell.walkable:
        player.grid_pos = (new_x, new_y)
        update_fov()
# endregion

# region: layer
# Add a color layer for FOV shading (behind tiles)
color_layer = mcrfpy.ColorLayer(z_index=-1, name="fog")
grid.add_layer(color_layer)

# Bind the layer to the player's perspective
color_layer.apply_perspective(
    entity=player,
    visible=mcrfpy.Color(0, 0, 0, 0),         # Transparent - fully visible
    discovered=mcrfpy.Color(40, 40, 60, 180), # Dim blue-gray overlay
    unknown=mcrfpy.Color(0, 0, 0, 255)        # Solid black
)

# Recompute + repaint together
player.update_visibility()
# endregion

# region: queries
def is_tile_visible(x, y):
    """Check if a tile is currently visible to the player."""
    return player.perspective_map[x, y] == mcrfpy.Perspective.VISIBLE

def is_tile_discovered(x, y):
    """Check if a tile has ever been seen."""
    return player.perspective_map[x, y] != mcrfpy.Perspective.UNKNOWN

def get_visible_enemies():
    """Return list of enemies the player can see."""
    return player.visible_entities()
# endregion

# region: oneoff
grid.compute_fov((player.grid_x, player.grid_y), radius=10, algorithm=mcrfpy.FOV.SHADOW)
if grid.is_in_fov(target_x, target_y):
    ...
# endregion

# region: algorithms
# Shadowcasting (default) - fast and produces nice results
grid.compute_fov((x, y), radius=10, algorithm=mcrfpy.FOV.SHADOW)

# Basic (libtcod default)
grid.compute_fov((x, y), radius=10, algorithm=mcrfpy.FOV.BASIC)

# Diamond - simple but produces diamond-shaped FOV
grid.compute_fov((x, y), radius=10, algorithm=mcrfpy.FOV.DIAMOND)

# Permissive - sees more tiles, good for tactical games (0-8, increasingly permissive)
grid.compute_fov((x, y), radius=10, algorithm=mcrfpy.FOV.PERMISSIVE_4)

# Other options: FOV.RESTRICTIVE, FOV.SYMMETRIC_SHADOWCAST
# endregion

move_player(1, 0)
print(is_tile_visible(26, 25), is_tile_discovered(26, 25), len(get_visible_enemies()))
grid.center_camera((player.grid_x + 0.5, player.grid_y + 0.5))
