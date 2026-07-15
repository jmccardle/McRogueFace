# mcrf: objects=[Easing,Entity,Grid,Scene] verified=0.2.8-dev status=ok
import mcrfpy

class PathAnimator:
    """Animate an entity along a series of waypoints."""

    def __init__(self, entity, path, step_duration=0.2, easing=None):
        """
        Args:
            entity: The Entity to animate
            path: List of (x, y) waypoints in grid coordinates
            step_duration: Seconds per step
            easing: mcrfpy.Easing value (default: EASE_IN_OUT)
        """
        self.entity = entity
        self.path = path
        self.step_duration = step_duration
        self.easing = easing if easing is not None else mcrfpy.Easing.EASE_IN_OUT
        self.index = 0
        self.on_complete = None
        self.on_step = None

    def start(self):
        """Begin path animation from current position."""
        self.index = 0
        self._animate_next()

    def _animate_next(self):
        """Animate to the next waypoint."""
        if self.index >= len(self.path):
            # Path complete
            if self.on_complete:
                self.on_complete(self)
            return

        target_x, target_y = self.path[self.index]

        # Create animations for this step
        def on_step_complete(target, prop, value):
            # Callback for step completion
            if self.on_step:
                self.on_step(self, self.index)
            self.index += 1
            self._animate_next()

        # Animate X (draw_x/draw_y are the tile-coordinate properties used
        # for smooth movement between grid cells; compare against draw_pos,
        # not entity.x/entity.y, which are pixel coordinates)
        pos = self.entity.draw_pos
        if pos.x != target_x:
            self.entity.animate("draw_x", float(target_x), self.step_duration,
                                 self.easing, callback=on_step_complete)
        # Animate Y
        elif pos.y != target_y:
            self.entity.animate("draw_y", float(target_y), self.step_duration,
                                 self.easing, callback=on_step_complete)
        else:
            # Already at position, skip to next
            self.index += 1
            self._animate_next()


scene = mcrfpy.Scene("path_animation_demo")
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

enemy = mcrfpy.Entity(grid_pos=(5, 5), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(enemy)

# Usage
path = [(5, 5), (5, 8), (8, 8), (8, 5)]  # Square patrol route
animator = PathAnimator(enemy, path, step_duration=0.3)
animator.on_complete = lambda a: print("Patrol complete!")
animator.start()
