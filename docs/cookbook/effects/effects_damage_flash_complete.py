"""McRogueFace - Damage Flash Effect (complete)

Documentation: https://mcrogueface.github.io/cookbook/effects_damage_flash
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/effects/effects_damage_flash_complete.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy

class DamageEffects:
    """Manages visual damage feedback effects."""

    # Color presets
    DAMAGE_RED = (255, 50, 50)
    HEAL_GREEN = (50, 255, 50)
    POISON_PURPLE = (150, 50, 200)
    FIRE_ORANGE = (255, 150, 50)
    ICE_BLUE = (100, 200, 255)

    def __init__(self, grid):
        self.grid = grid
        self.color_layer = None
        self._setup_color_layer()

    def _setup_color_layer(self):
        """Ensure grid has a color layer for effects."""
        self.grid.add_layer("color")
        self.color_layer = self.grid.layers[-1]

    def flash_entity(self, entity, color, duration=0.3):
        """Flash an entity with a color tint."""
        # Flash at entity's grid position
        x, y = int(entity.x), int(entity.y)
        self.flash_cell(x, y, color, duration)

    def flash_cell(self, x, y, color, duration=0.3):
        """Flash a specific grid cell."""
        if not self.color_layer:
            return

        cell = self.color_layer.at(x, y)
        if cell:
            cell.color = mcrfpy.Color(color[0], color[1], color[2], 180)

            # Fade out
            anim = mcrfpy.Animation("a", 0.0, duration, "easeOut")
            anim.start(cell.color)

    def damage(self, entity, amount, duration=0.3):
        """Standard damage flash."""
        self.flash_entity(entity, self.DAMAGE_RED, duration)

    def heal(self, entity, amount, duration=0.4):
        """Healing effect - green flash."""
        self.flash_entity(entity, self.HEAL_GREEN, duration)

    def poison(self, entity, duration=0.5):
        """Poison damage - purple flash."""
        self.flash_entity(entity, self.POISON_PURPLE, duration)

    def fire(self, entity, duration=0.3):
        """Fire damage - orange flash."""
        self.flash_entity(entity, self.FIRE_ORANGE, duration)

    def ice(self, entity, duration=0.4):
        """Ice damage - blue flash."""
        self.flash_entity(entity, self.ICE_BLUE, duration)

    def area_damage(self, center_x, center_y, radius, color, duration=0.4):
        """Flash all cells in a radius."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    self.flash_cell(center_x + dx, center_y + dy, color, duration)

# Setup
effects = DamageEffects(grid)

# Usage examples
effects.damage(player, 10)           # Red flash
effects.heal(player, 5)              # Green flash
effects.poison(enemy)                # Purple flash
effects.area_damage(5, 5, 3, effects.FIRE_ORANGE)  # Area effect