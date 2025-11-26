"""Base class for geometry demo screens."""
import mcrfpy
import sys
import os

# Add scripts path for geometry module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src', 'scripts'))
from geometry import *


class GeometryDemoScreen:
    """Base class for geometry demo screens."""

    name = "Base Screen"
    description = "Override this description"

    def __init__(self, scene_name):
        self.scene_name = scene_name
        mcrfpy.createScene(scene_name)
        self.ui = mcrfpy.sceneUI(scene_name)
        self.timers = []  # Track timer names for cleanup

    def setup(self):
        """Override to set up the screen content."""
        pass

    def cleanup(self):
        """Clean up timers when leaving screen."""
        for timer_name in self.timers:
            try:
                mcrfpy.delTimer(timer_name)
            except:
                pass

    def get_screenshot_name(self):
        """Return the screenshot filename for this screen."""
        return f"{self.scene_name}.png"

    def add_title(self, text, y=10):
        """Add a title caption."""
        title = mcrfpy.Caption(text=text, pos=(400, y))
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
        """Add a timer and track it for cleanup."""
        mcrfpy.setTimer(name, callback, interval)
        self.timers.append(name)
