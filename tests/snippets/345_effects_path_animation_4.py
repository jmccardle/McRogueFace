# mcrf: objects=[Easing,Entity,Grid,Scene] verified=0.3.6-dev status=ok
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

entity = mcrfpy.Entity(grid_pos=(5, 5), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(entity)

# region: variable-speed
import mcrfpy

class VariableSpeedPath:
    """Path animator with per-segment speed control."""

    def __init__(self, entity, waypoints):
        """
        Args:
            entity: Entity to animate
            waypoints: List of (x, y, duration, easing) tuples
                       duration and easing are optional
        """
        self.entity = entity
        self.waypoints = []
        for wp in waypoints:
            if len(wp) == 2:
                self.waypoints.append((wp[0], wp[1], 0.3, mcrfpy.Easing.EASE_IN_OUT))
            elif len(wp) == 3:
                self.waypoints.append((wp[0], wp[1], wp[2], mcrfpy.Easing.EASE_IN_OUT))
            else:
                self.waypoints.append(wp)

        self.index = 0
        self.on_complete = None

    def start(self):
        self.index = 0
        self._next()

    def _next(self):
        if self.index >= len(self.waypoints):
            if self.on_complete:
                self.on_complete(self)
            return

        x, y, duration, easing = self.waypoints[self.index]

        def done(target, prop, value):
            self.index += 1
            self._next()

        # Animate draw_pos (tiles); one animation covers both axes
        pos = self.entity.draw_pos
        if (pos.x, pos.y) != (x, y):
            self.entity.animate("draw_pos", (x, y), duration, easing, callback=done)
        else:
            done(None, None, None)


# Usage - different speeds for different segments
waypoints = [
    (5, 5),                                        # Default speed
    (5, 10, 0.5),                                   # Slower
    (10, 10, 0.2, mcrfpy.Easing.LINEAR),             # Fast, linear
    (10, 5, 1.0, mcrfpy.Easing.EASE_OUT),            # Slow arrival
]
path = VariableSpeedPath(entity, waypoints)
path.start()
# endregion
