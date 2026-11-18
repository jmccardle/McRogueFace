# mcrf: objects=[Color,ColorLayer,Grid,Scene,Timer] verified=0.3.6 status=ok
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

for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        cell.tilesprite = 48
        cell.walkable = True

# region: animated
class AnimatedHighlight:
    """Highlights that pulse or animate."""

    def __init__(self, grid, layer_z=1):
        self.grid = grid
        self.layer = mcrfpy.ColorLayer(name="highlight", z_index=layer_z)
        grid.add_layer(self.layer)
        self.animated_cells = {}  # (x, y) -> base_color
        self.phase = 0

    def add_pulse(self, cells, base_color):
        """Add cells that will pulse."""
        for cell in cells:
            self.animated_cells[cell] = base_color

    def clear(self):
        """Stop all animations."""
        self.animated_cells = {}
        self.layer.fill(mcrfpy.Color(0, 0, 0, 0))

    def update(self, dt):
        """Update animation state."""
        import math

        self.phase += dt * 3  # Speed of pulse

        # Calculate current alpha multiplier (0.5 to 1.0)
        pulse = 0.75 + 0.25 * math.sin(self.phase)

        for (x, y), base_color in self.animated_cells.items():
            # Modulate alpha
            animated_color = mcrfpy.Color(
                base_color.r,
                base_color.g,
                base_color.b,
                int(base_color.a * pulse)
            )
            self.layer.set((x, y), animated_color)


# Update in game loop
animated_highlights = AnimatedHighlight(grid)

def game_update(timer, runtime):
    dt = 0.016  # ~60 FPS
    animated_highlights.update(dt)

mcrfpy.Timer("highlight_anim", game_update, 16)
# endregion

animated_highlights.add_pulse([(3, 3), (4, 3), (5, 3)], mcrfpy.Color(255, 100, 0, 200))
animated_highlights.update(0.016)
