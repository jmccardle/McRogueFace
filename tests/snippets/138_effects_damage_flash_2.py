# mcrf: objects=[Color,ColorLayer,Entity,Grid,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(16, 12), pos=(0, 0), size=(640, 480))
scene.children.append(grid)

for y in range(12):
    for x in range(16):
        grid.at(x, y).tilesprite = 48

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
        self.color_layer = mcrfpy.ColorLayer(z_index=1, name="flash")
        self.grid.add_layer(self.color_layer)

    def flash_entity(self, entity, color, duration=0.3):
        """Flash the cell an entity currently occupies."""
        self.flash_cell(entity.cell_x, entity.cell_y, color, duration)

    def flash_cell(self, x, y, color, duration=0.3, steps=10):
        """Flash a specific grid cell, fading out over `duration` seconds."""
        if not self.color_layer:
            return

        r, g, b = color
        step_ms = max(1, int(duration * 1000 / steps))

        def do_fade(timer, runtime, step=[0]):
            step[0] += 1
            alpha = max(0, int(180 * (1 - step[0] / steps)))
            self.color_layer.set((x, y), mcrfpy.Color(r, g, b, alpha))
            if step[0] >= steps:
                timer.stop()

        self.color_layer.set((x, y), mcrfpy.Color(r, g, b, 180))
        mcrfpy.Timer(f"flash_{x}_{y}", do_fade, step_ms)

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

player = mcrfpy.Entity(grid_pos=(5, 5), texture=mcrfpy.default_texture)
grid.entities.append(player)
enemy = mcrfpy.Entity(grid_pos=(9, 5), texture=mcrfpy.default_texture)
grid.entities.append(enemy)

# Usage examples
effects.damage(player, 10)           # Red flash
effects.heal(player, 5)              # Green flash
effects.poison(enemy)                # Purple flash
effects.area_damage(5, 5, 3, effects.FIRE_ORANGE)  # Area effect
