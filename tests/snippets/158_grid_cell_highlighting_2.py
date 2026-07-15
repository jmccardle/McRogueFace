# mcrf: objects=[Color,ColorLayer,Grid,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(1024, 768),
    zoom=4.0
)
scene.children.append(grid)


class HighlightManager:
    """Manage multiple highlight layers."""

    COLORS = {
        'move': mcrfpy.Color(50, 100, 255, 80),      # Blue
        'attack': mcrfpy.Color(255, 50, 50, 100),     # Red
        'heal': mcrfpy.Color(50, 255, 50, 100),       # Green
        'danger': mcrfpy.Color(255, 100, 0, 120),     # Orange
        'select': mcrfpy.Color(255, 255, 50, 150),    # Yellow
        'path': mcrfpy.Color(255, 255, 255, 80),      # White
    }

    def __init__(self, grid):
        self.grid = grid
        self.layer = mcrfpy.ColorLayer(name="highlight", z_index=1)
        grid.add_layer(self.layer)
        self.highlights = {}  # category -> set of cells

    def add(self, category, cells):
        """Add highlights for a category."""
        self.highlights[category] = set(cells)
        self._refresh()

    def remove(self, category):
        """Remove highlights for a category."""
        if category in self.highlights:
            del self.highlights[category]
            self._refresh()

    def clear(self):
        """Clear all highlights."""
        self.highlights = {}
        self.layer.fill(mcrfpy.Color(0, 0, 0, 0))

    def _refresh(self):
        """Redraw all highlights with proper layering."""
        self.layer.fill(mcrfpy.Color(0, 0, 0, 0))

        # Draw in priority order (later categories draw on top)
        priority = ['move', 'attack', 'heal', 'danger', 'path', 'select']

        for category in priority:
            if category in self.highlights:
                color = self.COLORS.get(category, mcrfpy.Color(128, 128, 128, 100))
                for x, y in self.highlights[category]:
                    self.layer.set((x, y), color)


# Usage example
highlights = HighlightManager(grid)
highlights.add('move', [(2, 2), (3, 2), (4, 2)])
highlights.add('attack', [(5, 5)])
highlights.remove('attack')
