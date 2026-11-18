# mcrf: objects=[Caption,Color,Easing,Entity,Grid,Scene] verified=0.3.6 status=ok
import mcrfpy

game_scene = mcrfpy.Scene("game")
mcrfpy.current_scene = game_scene

grid = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(1024, 768)
)
game_scene.children.append(grid)
for y in range(12):
    for x in range(16):
        grid.at(x, y).tilesprite = 48

enemy = mcrfpy.Entity(grid_pos=(1, 1), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(enemy)


def show_damage(scene, x, y, amount, color=(255, 50, 50)):
    """Floating damage number (see the Quick Example): rises and fades."""
    caption = mcrfpy.Caption(text=str(amount), x=x, y=y)
    caption.fill_color = mcrfpy.Color(color[0], color[1], color[2], 255)
    caption.font_size = 24
    scene.children.append(caption)
    caption.animate("y", float(y - 50), 0.8, mcrfpy.Easing.EASE_OUT)
    caption.animate("opacity", 0.0, 0.8, mcrfpy.Easing.EASE_IN)

# region: grid-aware
import mcrfpy

def grid_to_screen(grid, grid_x, grid_y):
    """Convert grid tile coordinates to screen pixel coordinates."""
    # Account for grid position, zoom, and center offset
    tile_size = 16 * grid.zoom
    center_offset_x = grid.center[0] * grid.zoom
    center_offset_y = grid.center[1] * grid.zoom
    grid_center_x = grid.x + (grid.w / 2)
    grid_center_y = grid.y + (grid.h / 2)

    screen_x = grid_center_x + (grid_x * tile_size) - center_offset_x + (tile_size / 2)
    screen_y = grid_center_y + (grid_y * tile_size) - center_offset_y

    return screen_x, screen_y

def show_grid_damage(scene, grid, grid_x, grid_y, amount, color=(255, 50, 50)):
    """Show floating damage at a grid position."""
    screen_x, screen_y = grid_to_screen(grid, grid_x, grid_y)
    show_damage(scene, screen_x, screen_y, amount, color)

# Usage
show_grid_damage(game_scene, grid, int(enemy.x), int(enemy.y), 25)
# endregion
