# mcrf: objects=[Caption,Color,Entity,Grid,InputState,Key,Scene] verified=0.2.8-dev status=ok
# Game Minimap - Small overview map
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Main game grid - fills most of the screen
main_grid = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(800, 600),
    zoom=3.0
)
scene.children.append(main_grid)

# Create dungeon
for y in range(12):
    for x in range(16):
        cell = main_grid.at(x, y)
        if x == 0 or x == 15 or y == 0 or y == 11:
            cell.tilesprite = 1
        elif x == 8 and y > 2 and y < 9:
            cell.tilesprite = 1
        else:
            cell.tilesprite = 48

player = mcrfpy.Entity(grid_pos=(4, 6), texture=mcrfpy.default_texture, sprite_index=84)
main_grid.entities.append(player)

# Minimap - small overview in corner
minimap = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(820, 20),
    size=(180, 135),
    zoom=0.7
)
scene.children.append(minimap)

# Copy layout to minimap
for y in range(12):
    for x in range(16):
        minimap.at(x, y).tilesprite = main_grid.at(x, y).tilesprite

# Minimap player marker
mini_player = mcrfpy.Entity(grid_pos=(4, 6), texture=mcrfpy.default_texture, sprite_index=84)
minimap.entities.append(mini_player)

def on_key(key, action):
    if action != mcrfpy.InputState.PRESSED: return
    x, y = player.grid_x, player.grid_y
    if key == mcrfpy.Key.W and main_grid.at(x, y-1).tilesprite == 48: y -= 1
    elif key == mcrfpy.Key.S and main_grid.at(x, y+1).tilesprite == 48: y += 1
    elif key == mcrfpy.Key.A and main_grid.at(x-1, y).tilesprite == 48: x -= 1
    elif key == mcrfpy.Key.D and main_grid.at(x+1, y).tilesprite == 48: x += 1
    player.grid_pos = (x, y)
    mini_player.grid_pos = (x, y)

scene.on_key = on_key

status = mcrfpy.Caption(text="WASD to move, watch minimap", pos=(320, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
