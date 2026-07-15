# mcrf: objects=[Color,ColorLayer,Entity,Grid,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(16, 12), pos=(0, 0), size=(640, 480))
scene.children.append(grid)

for y in range(12):
    for x in range(16):
        grid.at(x, y).tilesprite = 48

color_layer = mcrfpy.ColorLayer(z_index=1, name="flash")
grid.add_layer(color_layer)

def multi_flash(grid, color_layer, x, y, color, flashes=3, flash_duration=0.1):
    """Flash a cell multiple times for emphasis."""
    r, g, b = color
    delay = 0

    for i in range(flashes):
        def do_flash(timer, runtime, fr=r, fg=g, fb=b):
            color_layer.set((x, y), mcrfpy.Color(fr, fg, fb, 200))
            mcrfpy.Timer(f"multiflash_clear_{x}_{y}_{timer.name}",
                         lambda t, rt: color_layer.set((x, y), mcrfpy.Color(fr, fg, fb, 0)),
                         int(flash_duration * 1000), once=True)

        mcrfpy.Timer(f"multiflash_{x}_{y}_{i}", do_flash, max(1, int(delay * 1000)), once=True)
        delay += flash_duration * 1.5  # Gap between flashes

enemy = mcrfpy.Entity(grid_pos=(9, 5), texture=mcrfpy.default_texture)
grid.entities.append(enemy)

# Usage for critical hit
multi_flash(grid, color_layer, enemy.cell_x, enemy.cell_y, (255, 255, 0), flashes=3)
