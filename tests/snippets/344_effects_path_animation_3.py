# mcrf: objects=[Easing,Entity,Grid,Scene,Timer] verified=0.3.6 status=ok
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

guard_entity = mcrfpy.Entity(grid_pos=(3, 3), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(guard_entity)

# region: patrol
import mcrfpy

class PatrolAnimator:
    """Endlessly loop through a patrol path."""

    def __init__(self, entity, path, step_duration=0.3, pause_duration=0.5):
        """
        Args:
            entity: Entity to animate
            path: List of (x, y) waypoints
            step_duration: Time per movement step
            pause_duration: Pause at each waypoint
        """
        self.entity = entity
        self.path = path
        self.step_duration = step_duration
        self.pause_duration = pause_duration
        self.index = 0
        self.is_paused = False
        self.is_running = False

    def start(self):
        """Start the patrol loop."""
        self.is_running = True
        self._move_to_next()

    def stop(self):
        """Stop the patrol."""
        self.is_running = False

    def _move_to_next(self):
        """Move to the next waypoint."""
        if not self.is_running:
            return

        target_x, target_y = self.path[self.index]

        def on_arrive(target, prop, value):
            if not self.is_running:
                return
            # Pause at waypoint
            def resume(timer, runtime):
                if self.is_running:
                    self.index = (self.index + 1) % len(self.path)
                    self._move_to_next()

            mcrfpy.Timer(f"patrol_pause_{id(self)}", resume,
                        int(self.pause_duration * 1000), once=True)

        # Animate movement (draw_pos is in tiles)
        pos = self.entity.draw_pos
        if (pos.x, pos.y) != (target_x, target_y):
            self.entity.animate("draw_pos", (target_x, target_y), self.step_duration,
                                 mcrfpy.Easing.EASE_IN_OUT, callback=on_arrive)
        else:
            # Already there, move to next after pause
            on_arrive(None, None, None)


# Usage
patrol_route = [(3, 3), (3, 7), (7, 7), (7, 3)]
guard = PatrolAnimator(guard_entity, patrol_route, pause_duration=1.0)
guard.start()

# Later, to stop:
# guard.stop()
# endregion
