"""McRogueFace - Multi-Layer Tiles (basic)

Documentation: https://mcrogueface.github.io/cookbook/grid_multi_layer
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/grid/grid_multi_layer_basic.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

class EffectLayer:
    """Manage visual effects with color overlays."""

    def __init__(self, grid, z_index=2):
        self.grid = grid
        self.layer = grid.add_layer("color", z_index=z_index)
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
            self.layer.set(x, y, mcrfpy.Color(0, 0, 0, 0))

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
            self.layer.set(x, y, color)

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


# Usage
effects = EffectLayer(grid)

# Add fire effect (permanent)
effects.add_effect(5, 5, 'fire')

# Add blood stain (fades over 10 seconds)
effects.add_effect(10, 10, 'blood', duration=10)

# Add poison cloud
for x in range(8, 12):
    for y in range(8, 12):
        effects.add_effect(x, y, 'poison', duration=5)

# Update in game loop
def game_update(runtime):
    effects.update(0.016)  # 60 FPS

mcrfpy.setTimer("effects", game_update, 16)