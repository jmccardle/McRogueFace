# mcrf: objects=[Color,ColorLayer,Entity,Grid,Scene,TileLayer,Timer] verified=0.3.6-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("layer-stack")
mcrfpy.current_scene = scene

texture = mcrfpy.default_texture
grid = mcrfpy.Grid(
    grid_size=(24, 18),
    texture=texture,
    pos=(0, 0),
    size=(1024, 768),
    zoom=2.5
)
scene.children.append(grid)

for y in range(18):
    for x in range(24):
        grid.at(x, y).walkable = True
        grid.at(x, y).transparent = True

player = mcrfpy.Entity(grid_pos=(12, 9), texture=texture, sprite_index=84)
grid.entities.append(player)


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
            'acid': 126,   # green potion; the tileset has sprites 0-131
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
        grid_w, grid_h = int(grid_w), int(grid_h)  # grid_size components are floats

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


class EffectLayer:
    """Manage visual effects with color overlays."""

    def __init__(self, grid, z_index=2):
        self.grid = grid
        self.layer = grid.add_layer(mcrfpy.ColorLayer(z_index=z_index, name="effects"))
        self.effects = {}  # (x, y) -> effect_data

    def add_effect(self, x, y, effect_type, duration=None, **kwargs):
        """Add a visual effect."""
        self.effects[(x, y)] = {
            'type': effect_type,
            'duration': duration,
            'time': 0,
            **kwargs
        }

    def remove_effect(self, x, y):
        """Remove an effect."""
        if (x, y) in self.effects:
            del self.effects[(x, y)]
            self.layer.set((x, y), mcrfpy.Color(0, 0, 0, 0))

    def update(self, dt):
        """Update all effects."""
        import math

        to_remove = []

        for (x, y), effect in self.effects.items():
            effect['time'] += dt

            # Check expiration
            if effect['duration'] and effect['time'] >= effect['duration']:
                to_remove.append((x, y))
                continue

            # Calculate color based on effect type
            color = self._calculate_color(effect)
            self.layer.set((x, y), color)

        for pos in to_remove:
            self.remove_effect(*pos)

    def _calculate_color(self, effect):
        """Get color for an effect at current time."""
        import math

        t = effect['time']
        effect_type = effect['type']

        if effect_type == 'fire':
            # Flickering orange/red
            flicker = 0.7 + 0.3 * math.sin(t * 10)
            return mcrfpy.Color(
                255,
                int(100 + 50 * math.sin(t * 8)),
                0,
                int(180 * flicker)
            )

        elif effect_type == 'poison':
            # Pulsing green
            pulse = 0.5 + 0.5 * math.sin(t * 3)
            return mcrfpy.Color(0, 200, 0, int(100 * pulse))

        elif effect_type == 'ice':
            # Static blue with shimmer
            shimmer = 0.8 + 0.2 * math.sin(t * 5)
            return mcrfpy.Color(100, 150, 255, int(120 * shimmer))

        elif effect_type == 'blood':
            # Fading red
            duration = effect.get('duration', 5)
            fade = 1 - (t / duration) if duration else 1
            return mcrfpy.Color(150, 0, 0, int(150 * fade))

        elif effect_type == 'highlight':
            # Pulsing highlight
            pulse = 0.5 + 0.5 * math.sin(t * 4)
            base = effect.get('color', mcrfpy.Color(255, 255, 0, 100))
            return mcrfpy.Color(base.r, base.g, base.b, int(base.a * pulse))

        return mcrfpy.Color(128, 128, 128, 50)


def get_movement_range(origin, steps):
    """Cells within `steps` moves (Manhattan distance) of origin."""
    ox, oy = int(origin.x), int(origin.y)
    return [(x, y)
            for y in range(18) for x in range(24)
            if abs(x - ox) + abs(y - oy) <= steps]


# region: layer-stack
class LayeredGrid:
    """Complete multi-layer grid system."""

    def __init__(self, grid):
        self.grid = grid

        # Layer stack (bottom to top)
        self.fog = mcrfpy.ColorLayer(z_index=-1, name="fog")   # Fog of war
        grid.add_layer(self.fog)
        # z_index=0 is the base grid tiles
        self.decor_manager = DecorationManager(grid)           # Decorations (z_index=1)
        self.effect_manager = EffectLayer(grid, z_index=2)     # Effects
        self.highlight = mcrfpy.ColorLayer(z_index=3, name="highlight")  # UI highlights
        grid.add_layer(self.highlight)

    def update(self, dt):
        """Update all animated layers."""
        self.effect_manager.update(dt)

    def set_fog(self, entity):
        """Apply fog of war from entity perspective."""
        self.fog.apply_perspective(
            entity,
            visible=mcrfpy.Color(0, 0, 0, 0),
            discovered=mcrfpy.Color(20, 20, 40, 160),
            unknown=mcrfpy.Color(0, 0, 0, 255)
        )
        # apply_perspective() only binds the layer; repaint it once now, and
        # call update_perspective() again whenever the entity moves.
        self.fog.update_perspective()

    def highlight_cells(self, cells, color):
        """Highlight cells for targeting/movement."""
        self.highlight.fill(mcrfpy.Color(0, 0, 0, 0))
        for x, y in cells:
            self.highlight.set((x, y), color)

    def clear_highlights(self):
        """Clear all highlights."""
        self.highlight.fill(mcrfpy.Color(0, 0, 0, 0))


# Usage
layers = LayeredGrid(grid)

# Setup fog of war
layers.set_fog(player)

# Add decorations
layers.decor_manager.place(10, 10, 'furniture', 'chest')

# Add effect
layers.effect_manager.add_effect(15, 15, 'fire')

# Highlight movement range
movement_cells = get_movement_range(player.cell_pos, 5)
layers.highlight_cells(movement_cells, mcrfpy.Color(50, 100, 255, 80))

# Game loop
def update(timer, runtime):
    layers.update(0.016)

mcrfpy.Timer("layers", update, 16)
# endregion
