# mcrf: objects=[Color,ColorLayer,Grid,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy
import math

class AreaPulse:
    """Pulse a rectangular or circular area."""

    def __init__(self, grid):
        self.grid = grid
        self.cells = []  # list of (x, y)
        self.is_pulsing = False
        self.timer = None
        self.color_layer = self._get_or_create_layer()

    def _get_or_create_layer(self):
        existing = self.grid.layer("area_pulse")
        if existing is not None:
            return existing
        layer = mcrfpy.ColorLayer(z_index=1, name="area_pulse")
        self.grid.add_layer(layer)
        return layer

    def set_rect(self, x, y, width, height, color):
        """Set a rectangular area to pulse."""
        self.color = color
        self.cells = [
            (x + dx, y + dy)
            for dy in range(height)
            for dx in range(width)
        ]

    def set_circle(self, center_x, center_y, radius, color):
        """Set a circular area to pulse."""
        self.color = color
        self.cells = [
            (center_x + dx, center_y + dy)
            for dy in range(-radius, radius + 1)
            for dx in range(-radius, radius + 1)
            if dx * dx + dy * dy <= radius * radius
        ]

    def _write(self, alpha):
        r, g, b = self.color
        for (x, y) in self.cells:
            self.color_layer.set((x, y), mcrfpy.Color(r, g, b, alpha))

    def pulse_once(self, duration=0.5, max_alpha=180):
        """Single pulse of the area: fade in, then fade out."""
        half = duration / 2.0
        state = {"t0": None}

        def tick(timer, runtime):
            if state["t0"] is None:
                state["t0"] = runtime
            t = (runtime - state["t0"]) / 1000.0
            if t >= duration:
                self._write(0)
                timer.stop()
                return
            phase = t / half
            frac = phase if phase <= 1.0 else 2.0 - phase
            self._write(int(max_alpha * frac))

        mcrfpy.Timer(f"area_once_{id(self)}", tick, 33)

    def start_continuous(self, period=1.0, max_alpha=150):
        """Start continuous pulsing of the area."""
        self.is_pulsing = True
        state = {"t0": None}

        def tick(timer, runtime):
            if not self.is_pulsing:
                return
            if state["t0"] is None:
                state["t0"] = runtime
            t = (runtime - state["t0"]) / 1000.0
            wave = (math.sin(2 * math.pi * t / period) + 1.0) / 2.0
            self._write(int(max_alpha * wave))

        self.timer = mcrfpy.Timer(f"area_continuous_{id(self)}", tick, 33)

    def stop(self):
        """Stop pulsing and clear."""
        self.is_pulsing = False
        if self.timer is not None:
            self.timer.stop()
            self.timer = None
        self._write(0)


# Usage
scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(20, 16), pos=(0, 0), size=(512, 384))
scene.children.append(grid)

area = AreaPulse(grid)

# Highlight a room
area.set_rect(5, 5, 4, 4, (100, 200, 255))
area.start_continuous(period=2.0)

# Or highlight explosion radius
area.set_circle(10, 10, 3, (255, 100, 0))
area.pulse_once(duration=0.8)
