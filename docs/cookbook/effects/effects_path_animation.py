"""McRogueFace - Path Animation (Multi-Step Movement) (effects_path_animation)

Documentation: https://mcrogueface.github.io/cookbook/effects_path_animation
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/effects/effects_path_animation.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

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

        def done(anim, target):
            self.index += 1
            self._next()

        # Animate entity
        if self.entity.x != x:
            anim = mcrfpy.Animation("x", float(x), self.step_duration,
                                    "easeInOut", callback=done)
            anim.start(self.entity)
        elif self.entity.y != y:
            anim = mcrfpy.Animation("y", float(y), self.step_duration,
                                    "easeInOut", callback=done)
            anim.start(self.entity)
        else:
            done(None, None)
            return

        # Animate camera to follow
        cam_x = mcrfpy.Animation("center_x", (x + 0.5) * 16,
                                  self.step_duration, "easeInOut")
        cam_y = mcrfpy.Animation("center_y", (y + 0.5) * 16,
                                  self.step_duration, "easeInOut")
        cam_x.start(self.grid)
        cam_y.start(self.grid)


# Usage
path = [(5, 5), (5, 10), (10, 10)]
mover = CameraFollowingPath(player, grid, path)
mover.on_complete = lambda m: print("Journey complete!")
mover.start()