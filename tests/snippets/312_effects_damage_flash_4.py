# mcrf: objects=[Color,ColorLayer,Entity,Grid,Scene,Timer] verified=0.3.6-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(16, 12), pos=(0, 0), size=(640, 480))
scene.children.append(grid)

for y in range(12):
    for x in range(16):
        grid.at(x, y).tilesprite = 48

enemy = mcrfpy.Entity(grid_pos=(9, 5), texture=mcrfpy.default_texture)
grid.entities.append(enemy)

# region: cell_flash
import mcrfpy

# Add a color layer to your grid (do this once during setup)
color_layer = mcrfpy.ColorLayer(z_index=1, name="flash")
grid.add_layer(color_layer)

def flash_cell(grid, color_layer, x, y, color, duration=0.3, steps=10):
    """Flash a grid cell with a color overlay, fading alpha to 0 over `duration` seconds."""
    r, g, b = color
    step_ms = max(1, int(duration * 1000 / steps))

    def do_fade(timer, runtime, step=[0]):
        step[0] += 1
        alpha = max(0, int(200 * (1 - step[0] / steps)))
        color_layer.set((x, y), mcrfpy.Color(r, g, b, alpha))
        if step[0] >= steps:
            timer.stop()

    color_layer.set((x, y), mcrfpy.Color(r, g, b, 200))
    mcrfpy.Timer(f"flash_{x}_{y}", do_fade, step_ms)

def damage_at_position(grid, color_layer, x, y, duration=0.3):
    """Flash red at a grid position when damage occurs."""
    flash_cell(grid, color_layer, x, y, (255, 0, 0), duration)

# Usage when entity takes damage
damage_at_position(grid, color_layer, enemy.cell_x, enemy.cell_y)
# endregion
