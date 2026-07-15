# mcrf: objects=[Color,Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy

class HealthBar:
    """A simple health bar with background and fill."""

    def __init__(self, x, y, w, h, current, maximum):
        """
        Create a health bar.

        Args:
            x, y: Position on screen
            w, h: Size of the bar
            current: Current health value
            maximum: Maximum health value
        """
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.current = current
        self.maximum = maximum

        # Background (empty bar)
        self.background = mcrfpy.Frame(pos=(x, y), size=(w, h))
        self.background.fill_color = mcrfpy.Color(40, 40, 40)
        self.background.outline = 1
        self.background.outline_color = mcrfpy.Color(80, 80, 80)

        # Fill (current health)
        self.fill = mcrfpy.Frame(pos=(x, y), size=(w, h))
        self.fill.fill_color = mcrfpy.Color(220, 50, 50)
        self.fill.outline = 0

        # Update fill width
        self._update_fill()

    def _update_fill(self):
        """Update the fill frame width based on current/max ratio."""
        ratio = max(0, min(1, self.current / self.maximum))
        self.fill.w = self.w * ratio

    def set_health(self, current, maximum=None):
        """
        Update health values.

        Args:
            current: New current health
            maximum: New maximum health (optional)
        """
        self.current = current
        if maximum is not None:
            self.maximum = maximum
        self._update_fill()

    def add_to_scene(self, ui):
        """Add both frames to scene UI (background first, then fill)."""
        ui.append(self.background)
        ui.append(self.fill)


# Usage Example
scene = mcrfpy.Scene("health_demo")

# Create a health bar
hp_bar = HealthBar(50, 50, 200, 20, current=75, maximum=100)
hp_bar.add_to_scene(scene.children)

# Update health
hp_bar.set_health(50)  # Now at 50%

scene.activate()
