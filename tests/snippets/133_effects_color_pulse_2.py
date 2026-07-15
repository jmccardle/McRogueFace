# mcrf: objects=[Color,ColorLayer,Grid,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy
import math

class PulsingCell:
    """A cell that continuously pulses until stopped."""

    def __init__(self, grid, x, y, color, period=1.0, max_alpha=180):
        """
        Args:
            grid: Grid with color layer
            x, y: Cell position
            color: RGB tuple
            period: Time for one complete pulse cycle
            max_alpha: Maximum alpha value (0-255)
        """
        self.grid = grid
        self.x = x
        self.y = y
        self.color = color
        self.period = period
        self.max_alpha = max_alpha
        self.is_pulsing = False
        self.layer = self._get_or_create_layer()
        self.timer = None

    def _get_or_create_layer(self):
        """Ensure a named color layer exists on the grid."""
        existing = self.grid.layer("pulse")
        if existing is not None:
            return existing
        layer = mcrfpy.ColorLayer(z_index=1, name="pulse")
        self.grid.add_layer(layer)
        return layer

    def _tick(self, timer, runtime):
        if not self.is_pulsing:
            return
        r, g, b = self.color
        # Sine wave oscillating between 0 and max_alpha
        t = runtime / 1000.0
        wave = (math.sin(2 * math.pi * t / self.period) + 1.0) / 2.0
        alpha = int(self.max_alpha * wave)
        self.layer.set((self.x, self.y), mcrfpy.Color(r, g, b, alpha))

    def start(self):
        """Start continuous pulsing."""
        if self.is_pulsing:
            return
        self.is_pulsing = True
        self.timer = mcrfpy.Timer(f"pulse_{id(self)}", self._tick, 33)

    def stop(self):
        """Stop pulsing and clear the cell."""
        self.is_pulsing = False
        if self.timer is not None:
            self.timer.stop()
            self.timer = None
        r, g, b = self.color
        self.layer.set((self.x, self.y), mcrfpy.Color(r, g, b, 0))

    def set_color(self, color):
        """Change pulse color for subsequent ticks."""
        self.color = color


# Usage
scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(16, 12), pos=(0, 0), size=(512, 384))
scene.children.append(grid)

objective_pulse = PulsingCell(grid, 10, 10, (0, 255, 100), period=1.5)
objective_pulse.start()

# Later, when objective is reached:
objective_pulse.stop()
