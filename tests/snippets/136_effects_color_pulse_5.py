# mcrf: objects=[Color,ColorLayer,Grid,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy

def ripple_effect(grid, center_x, center_y, color, max_radius=5, duration=1.0):
    """
    Create an expanding ripple effect.

    Args:
        grid: Grid with color layer
        center_x, center_y: Ripple origin
        color: RGB tuple
        max_radius: Maximum ripple size
        duration: Total animation time
    """
    layer = grid.layer("ripple")
    if layer is None:
        layer = mcrfpy.ColorLayer(z_index=1, name="ripple")
        grid.add_layer(layer)

    step_duration = duration / max_radius
    r, g, b = color

    for radius in range(max_radius + 1):
        # Cells approximately on the ring edge at this radius
        ring_cells = []
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                dist_sq = dx * dx + dy * dy
                if radius * radius - radius <= dist_sq <= radius * radius + radius:
                    ring_cells.append((center_x + dx, center_y + dy))

        fade_duration = step_duration * 2

        def make_ring_animator(cells):
            state = {"t0": None}

            def tick(timer, runtime):
                if state["t0"] is None:
                    state["t0"] = runtime
                t = (runtime - state["t0"]) / 1000.0
                frac = max(0.0, 1.0 - t / fade_duration)
                alpha = int(200 * frac)
                for cx, cy in cells:
                    layer.set((cx, cy), mcrfpy.Color(r, g, b, alpha))
                if t >= fade_duration:
                    for cx, cy in cells:
                        layer.set((cx, cy), mcrfpy.Color(r, g, b, 0))
                    timer.stop()
            return tick

        def start_ring(timer, runtime, cells=ring_cells):
            mcrfpy.Timer(f"ripple_fade_{id(cells)}", make_ring_animator(cells), 33)
            timer.stop()

        delay = int(radius * step_duration * 1000)
        mcrfpy.Timer(f"ripple_{radius}", start_ring, max(delay, 1), once=True)


# Usage
scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(24, 24), pos=(0, 0), size=(512, 512))
scene.children.append(grid)

ripple_effect(grid, 12, 12, (100, 200, 255), max_radius=6, duration=0.8)
