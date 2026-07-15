# mcrf: objects=[Grid,Scene,TileLayer] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("layers-decor")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(1024, 768),
    zoom=4.0
)
scene.children.append(grid)

for y in range(12):
    for x in range(16):
        grid.at(x, y).walkable = True


class DecorationManager:
    """Manage decorative tile overlays."""

    # Decoration categories with sprite indices
    DECORATIONS = {
        'furniture': {
            'table': 100,
            'chair': 101,
            'bed': 102,
            'chest': 103,
            'bookshelf': 104,
        },
        'debris': {
            'bones': 110,
            'rubble': 111,
            'cobweb': 112,
        },
        'nature': {
            'grass_tuft': 120,
            'mushroom': 121,
            'flower': 122,
            'moss': 123,
        },
        'stains': {
            'blood': 130,
            'water': 131,
            'acid': 132,
        }
    }

    def __init__(self, grid):
        self.grid = grid
        self.layer = grid.add_layer(
            mcrfpy.TileLayer(z_index=1, name="decor", texture=mcrfpy.default_texture)
        )
        self.placed = {}  # (x, y) -> decoration_name

    def place(self, x, y, category, name):
        """Place a decoration."""
        if category in self.DECORATIONS:
            if name in self.DECORATIONS[category]:
                sprite_idx = self.DECORATIONS[category][name]
                self.layer.set((x, y), sprite_idx)
                self.placed[(x, y)] = (category, name)

    def remove(self, x, y):
        """Remove a decoration."""
        self.layer.set((x, y), -1)
        if (x, y) in self.placed:
            del self.placed[(x, y)]

    def get(self, x, y):
        """Get decoration at position."""
        return self.placed.get((x, y))

    def scatter(self, category, count, walkable_only=True):
        """Randomly scatter decorations."""
        import random

        if category not in self.DECORATIONS:
            return

        names = list(self.DECORATIONS[category].keys())
        grid_w, grid_h = self.grid.grid_size
        grid_w, grid_h = int(grid_w), int(grid_h)

        placed = 0
        attempts = 0
        max_attempts = count * 10

        while placed < count and attempts < max_attempts:
            attempts += 1

            x = random.randint(0, grid_w - 1)
            y = random.randint(0, grid_h - 1)

            # Check if position is valid
            point = self.grid.at(x, y)
            if walkable_only and not point.walkable:
                continue
            if (x, y) in self.placed:
                continue

            name = random.choice(names)
            self.place(x, y, category, name)
            placed += 1


# Usage
decor = DecorationManager(grid)

# Place specific decorations
decor.place(10, 10, 'furniture', 'table')
decor.place(11, 10, 'furniture', 'chair')

# Scatter random debris
decor.scatter('debris', 20)
decor.scatter('nature', 15)
