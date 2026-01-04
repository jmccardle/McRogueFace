"""Base class for geometry demo screens."""
import mcrfpy
import sys
import os
import math

# Add scripts path for geometry module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src', 'scripts'))
from geometry import *

# Screen resolution
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768


def screen_angle_between(p1, p2):
    """
    Calculate angle from p1 to p2 in screen coordinates.
    In screen coords, Y increases downward, so we negate dy.
    Returns angle in degrees where 0=right, 90=up, 180=left, 270=down.
    """
    dx = p2[0] - p1[0]
    dy = p1[1] - p2[1]  # Negate because screen Y is inverted
    angle = math.degrees(math.atan2(dy, dx))
    if angle < 0:
        angle += 360
    return angle


class GeometryDemoScreen:
    """Base class for geometry demo screens."""

    name = "Base Screen"
    description = "Override this description"

    def __init__(self, scene_name):
        self.scene_name = scene_name
        _scene = mcrfpy.Scene(scene_name)
        self.ui = mcrfpy.sceneUI(scene_name)
        self.timers = []  # Track timer names for cleanup
        self._timer_configs = []  # Store timer configs for restart

    def setup(self):
        """Override to set up the screen content."""
        pass

    def cleanup(self):
        """Clean up timers when leaving screen."""
        for timer in self.timers:
            try:
                timer.stop()
            except:
                pass

    def restart_timers(self):
        """Re-register timers after cleanup."""
        self.timers = []  # Clear old timer references
        for name, callback, interval in self._timer_configs:
            try:
                timer = mcrfpy.Timer(name, callback, interval)
                self.timers.append(timer)
            except Exception as e:
                print(f"Timer restart failed: {e}")

    def get_screenshot_name(self):
        """Return the screenshot filename for this screen."""
        return f"{self.scene_name}.png"

    def add_title(self, text, y=10):
        """Add a title caption centered at top."""
        title = mcrfpy.Caption(text=text, pos=(SCREEN_WIDTH // 2, y))
        title.fill_color = mcrfpy.Color(255, 255, 255)
        title.outline = 2
        title.outline_color = mcrfpy.Color(0, 0, 0)
        self.ui.append(title)
        return title

    def add_description(self, text, y=50):
        """Add a description caption."""
        desc = mcrfpy.Caption(text=text, pos=(50, y))
        desc.fill_color = mcrfpy.Color(200, 200, 200)
        self.ui.append(desc)
        return desc

    def add_label(self, text, x, y, color=(200, 200, 200)):
        """Add a label caption."""
        label = mcrfpy.Caption(text=text, pos=(x, y))
        label.fill_color = mcrfpy.Color(*color)
        self.ui.append(label)
        return label

    def create_grid(self, grid_size, pos, size, cell_size=16):
        """Create a grid for visualization."""
        grid = mcrfpy.Grid(
            grid_size=grid_size,
            pos=pos,
            size=size
        )
        grid.fill_color = mcrfpy.Color(20, 20, 30)
        self.ui.append(grid)
        return grid

    def color_grid_cell(self, grid, x, y, color):
        """Color a specific grid cell."""
        try:
            point = grid.at(x, y)
            point.color = mcrfpy.Color(*color) if isinstance(color, tuple) else color
        except:
            pass  # Out of bounds

    def add_timer(self, name, callback, interval):
        """Add a timer and track it for cleanup/restart."""
        if callback is None:
            print(f"Warning: Timer '{name}' callback is None, skipping")
            return
        timer = mcrfpy.Timer(name, callback, interval)
        self.timers.append(timer)
        self._timer_configs.append((name, callback, interval))
