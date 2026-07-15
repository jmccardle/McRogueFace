# mcrf: objects=[Color,ColorLayer,Entity,Grid,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(16, 12), pos=(0, 0), size=(640, 480))
scene.children.append(grid)

for y in range(12):
    for x in range(16):
        grid.at(x, y).tilesprite = 48

# One ColorLayer, reused for every flash effect on this grid.
color_layer = mcrfpy.ColorLayer(z_index=1, name="flash")
grid.add_layer(color_layer)

def flash_cell(x, y, color, duration=0.3, steps=10):
    """Flash a grid cell with a color overlay that fades out over `duration` seconds."""
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

def damage_flash(entity, duration=0.3):
    """Flash red on the cell an entity occupies."""
    flash_cell(entity.cell_x, entity.cell_y, (255, 0, 0), duration)

# Usage
player = mcrfpy.Entity(grid_pos=(8, 6), texture=mcrfpy.default_texture)
grid.entities.append(player)
damage_flash(player)
