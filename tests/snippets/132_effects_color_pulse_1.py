# mcrf: objects=[Color,ColorLayer,Grid,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy
import math

def get_or_create_layer(grid, name="pulse", z_index=1):
    """Find grid's named ColorLayer, or create and attach one."""
    existing = grid.layer(name)
    if existing is not None:
        return existing
    layer = mcrfpy.ColorLayer(z_index=z_index, name=name)
    grid.add_layer(layer)
    return layer

def pulse_cell(grid, x, y, color, duration=1.0):
    """
    Pulse a cell's color overlay from transparent to visible and back once.

    Args:
        grid: Grid to overlay
        x, y: Cell coordinates
        color: RGB tuple (r, g, b)
        duration: Full cycle duration in seconds
    """
    layer = get_or_create_layer(grid)
    r, g, b = color
    half_duration = duration / 2.0
    state = {"t0": None}

    def tick(timer, runtime):
        if state["t0"] is None:
            state["t0"] = runtime
        t = (runtime - state["t0"]) / 1000.0
        if t >= duration:
            layer.set((x, y), mcrfpy.Color(r, g, b, 0))
            timer.stop()
            return
        # Triangle wave: 0 -> 1 over the first half, 1 -> 0 over the second
        phase = t / half_duration
        alpha_frac = phase if phase <= 1.0 else 2.0 - phase
        layer.set((x, y), mcrfpy.Color(r, g, b, int(200 * alpha_frac)))

    mcrfpy.Timer(f"pulse_{x}_{y}", tick, 33)


# Usage
scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(16, 12), pos=(0, 0), size=(512, 384))
scene.children.append(grid)

pulse_cell(grid, 5, 5, (255, 200, 0), duration=1.5)  # Golden pulse
