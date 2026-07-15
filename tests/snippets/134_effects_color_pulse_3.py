# mcrf: objects=[Color,ColorLayer,Grid,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy
import math

class PulsingCell:
    """A cell that continuously pulses until stopped."""

    def __init__(self, grid, x, y, color, period=1.0, max_alpha=180):
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
        t = runtime / 1000.0
        wave = (math.sin(2 * math.pi * t / self.period) + 1.0) / 2.0
        alpha = int(self.max_alpha * wave)
        self.layer.set((self.x, self.y), mcrfpy.Color(r, g, b, alpha))

    def start(self):
        if self.is_pulsing:
            return
        self.is_pulsing = True
        self.timer = mcrfpy.Timer(f"pulse_{id(self)}", self._tick, 33)

    def stop(self):
        self.is_pulsing = False
        if self.timer is not None:
            self.timer.stop()
            self.timer = None
        r, g, b = self.color
        self.layer.set((self.x, self.y), mcrfpy.Color(r, g, b, 0))

    def set_color(self, color):
        self.color = color


class PulseManager:
    """Manages multiple pulsing cell effects."""

    # Preset colors
    OBJECTIVE = (0, 255, 100)    # Green - goals, exits
    WARNING = (255, 100, 0)      # Orange - danger zones
    TREASURE = (255, 215, 0)     # Gold - loot
    MAGIC = (150, 50, 255)       # Purple - magical
    HEAL = (100, 200, 255)       # Light blue - healing
    DAMAGE = (255, 50, 50)       # Red - damage zones

    def __init__(self, grid):
        self.grid = grid
        self.pulses = {}  # (x, y) -> PulsingCell

    def add(self, x, y, color, period=1.0, max_alpha=180):
        """Add a pulsing cell."""
        key = (x, y)
        if key in self.pulses:
            self.pulses[key].stop()

        pulse = PulsingCell(self.grid, x, y, color, period, max_alpha)
        pulse.start()
        self.pulses[key] = pulse
        return pulse

    def remove(self, x, y):
        """Stop and remove a pulsing cell."""
        key = (x, y)
        if key in self.pulses:
            self.pulses[key].stop()
            del self.pulses[key]

    def clear(self):
        """Stop all pulsing cells."""
        for pulse in self.pulses.values():
            pulse.stop()
        self.pulses.clear()

    def has_pulse(self, x, y):
        """Check if a cell is pulsing."""
        return (x, y) in self.pulses

    # Convenience methods with presets
    def mark_objective(self, x, y):
        """Mark a cell as an objective."""
        return self.add(x, y, self.OBJECTIVE, period=1.5)

    def mark_warning(self, x, y):
        """Mark a cell as dangerous."""
        return self.add(x, y, self.WARNING, period=0.8, max_alpha=150)

    def mark_treasure(self, x, y):
        """Mark a cell with treasure."""
        return self.add(x, y, self.TREASURE, period=1.2)

    def mark_magic(self, x, y):
        """Mark a magical cell."""
        return self.add(x, y, self.MAGIC, period=2.0)


# Usage
scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(20, 16), pos=(0, 0), size=(512, 384))
scene.children.append(grid)

pulses = PulseManager(grid)

# Mark various cells
pulses.mark_objective(15, 10)   # Exit door
pulses.mark_treasure(8, 5)      # Chest location
pulses.mark_warning(12, 12)     # Trap

# When player reaches objective
pulses.remove(15, 10)

# Clear all when changing levels
pulses.clear()
