# mcrf: objects=[Easing,Entity,Grid,Scene] verified=0.3.6 status=ok
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

entity = mcrfpy.Entity(grid_pos=(2, 2), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(entity)

# region: diagonal
import mcrfpy

class DiagonalPathAnimator:
    """Path animator with diagonal movement support."""

    def __init__(self, entity, path, step_duration=0.2, easing=None):
        self.entity = entity
        self.path = path
        self.step_duration = step_duration
        self.easing = easing if easing is not None else mcrfpy.Easing.EASE_IN_OUT
        self.index = 0
        self.on_complete = None
        self.on_step = None

    def start(self):
        """Begin path animation."""
        self.index = 0
        self._animate_next()

    def _on_anim_done(self, target, prop, value):
        """One animation per waypoint, so one callback per step."""
        if self.on_step:
            self.on_step(self, self.index)
        self.index += 1
        self._animate_next()

    def _animate_next(self):
        """Animate to next waypoint (diagonal if needed)."""
        if self.index >= len(self.path):
            if self.on_complete:
                self.on_complete(self)
            return

        target_x, target_y = self.path[self.index]
        pos = self.entity.draw_pos

        if (pos.x, pos.y) == (target_x, target_y):
            # Already at target, move to next
            self.index += 1
            self._animate_next()
            return

        # One animation moves both axes (draw_pos is in tiles)
        self.entity.animate("draw_pos", (target_x, target_y), self.step_duration,
                             self.easing, callback=self._on_anim_done)


# Usage - diagonal path
path = [(2, 2), (5, 5), (8, 2), (5, 5)]  # Diamond pattern
animator = DiagonalPathAnimator(entity, path, step_duration=0.4)
animator.start()
# endregion
