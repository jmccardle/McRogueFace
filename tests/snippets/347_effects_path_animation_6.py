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

player = mcrfpy.Entity(grid_pos=(5, 5), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(player)

# region: camera
import mcrfpy

class CameraFollowingPath:
    """Path animator that also moves the camera."""

    def __init__(self, entity, grid, path, step_duration=0.2):
        self.entity = entity
        self.grid = grid
        self.path = path
        self.step_duration = step_duration
        self.index = 0
        self.on_complete = None

    def start(self):
        self.index = 0
        self._next()

    def _next(self):
        if self.index >= len(self.path):
            if self.on_complete:
                self.on_complete(self)
            return

        x, y = self.path[self.index]

        def done(target, prop, value):
            self.index += 1
            self._next()

        # Animate entity (draw_pos is in tiles)
        pos = self.entity.draw_pos
        if (pos.x, pos.y) != (x, y):
            self.entity.animate("draw_pos", (x, y), self.step_duration,
                                 mcrfpy.Easing.EASE_IN_OUT, callback=done)
        else:
            done(None, None, None)
            return

        # Animate camera to follow (center is in pixel space; tile size here is 16px)
        self.grid.animate("center", ((x + 0.5) * 16, (y + 0.5) * 16),
                           self.step_duration, mcrfpy.Easing.EASE_IN_OUT)


# Usage
path = [(5, 5), (5, 10), (10, 10)]
mover = CameraFollowingPath(player, grid, path)
mover.on_complete = lambda m: print("Journey complete!")
mover.start()
# endregion
