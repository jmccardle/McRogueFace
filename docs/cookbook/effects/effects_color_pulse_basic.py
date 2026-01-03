"""McRogueFace - Color Pulse Effect (basic)

Documentation: https://mcrogueface.github.io/cookbook/effects_color_pulse
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/effects/effects_color_pulse_basic.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy

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
        self.pulse_id = 0
        self.cell = None

        self._setup_layer()

    def _setup_layer(self):
        """Ensure color layer exists and get cell reference."""
        color_layer = None
        for layer in self.grid.layers:
            if isinstance(layer, mcrfpy.ColorLayer):
                color_layer = layer
                break

        if not color_layer:
            self.grid.add_layer("color")
            color_layer = self.grid.layers[-1]

        self.cell = color_layer.at(self.x, self.y)
        if self.cell:
            self.cell.color = mcrfpy.Color(self.color[0], self.color[1],
                                            self.color[2], 0)

    def start(self):
        """Start continuous pulsing."""
        if self.is_pulsing or not self.cell:
            return

        self.is_pulsing = True
        self.pulse_id += 1
        self._pulse_up()

    def _pulse_up(self):
        """Animate alpha increasing."""
        if not self.is_pulsing:
            return

        current_id = self.pulse_id
        half_period = self.period / 2

        anim = mcrfpy.Animation("a", float(self.max_alpha), half_period, "easeInOut")
        anim.start(self.cell.color)

        def next_phase(timer_name):
            if self.is_pulsing and self.pulse_id == current_id:
                self._pulse_down()

        mcrfpy.Timer(f"pulse_up_{id(self)}_{current_id}",
                     next_phase, int(half_period * 1000), once=True)

    def _pulse_down(self):
        """Animate alpha decreasing."""
        if not self.is_pulsing:
            return

        current_id = self.pulse_id
        half_period = self.period / 2

        anim = mcrfpy.Animation("a", 0.0, half_period, "easeInOut")
        anim.start(self.cell.color)

        def next_phase(timer_name):
            if self.is_pulsing and self.pulse_id == current_id:
                self._pulse_up()

        mcrfpy.Timer(f"pulse_down_{id(self)}_{current_id}",
                     next_phase, int(half_period * 1000), once=True)

    def stop(self):
        """Stop pulsing and fade out."""
        self.is_pulsing = False
        if self.cell:
            anim = mcrfpy.Animation("a", 0.0, 0.2, "easeOut")
            anim.start(self.cell.color)

    def set_color(self, color):
        """Change pulse color."""
        self.color = color
        if self.cell:
            current_alpha = self.cell.color.a
            self.cell.color = mcrfpy.Color(color[0], color[1], color[2], current_alpha)


# Usage
objective_pulse = PulsingCell(grid, 10, 10, (0, 255, 100), period=1.5)
objective_pulse.start()

# Later, when objective is reached:
objective_pulse.stop()