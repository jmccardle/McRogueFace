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

player = mcrfpy.Entity(grid_pos=(2, 2), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(player)


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

        # Called after each leg; a diagonal waypoint takes two legs (X, then Y)
        def on_step_complete(target, prop, value):
            pos = self.entity.draw_pos
            if (pos.x, pos.y) == (target_x, target_y):
                # Arrived at this waypoint
                if self.on_step:
                    self.on_step(self, self.index)
                self.index += 1
            self._animate_next()

        # Move along X, then along Y: one leg per animation. draw_pos is in
        # tiles (entity.x/entity.y are pixel coordinates).
        pos = self.entity.draw_pos
        if pos.x != target_x:
            self.entity.animate("draw_pos", (target_x, pos.y), self.step_duration,
                                 self.easing, callback=on_step_complete)
        elif pos.y != target_y:
            self.entity.animate("draw_pos", (pos.x, target_y), self.step_duration,
                                 self.easing, callback=on_step_complete)
        else:
            # Already at position, skip to next
            self.index += 1
            self._animate_next()

# region: pathfinding
import mcrfpy

def animate_to_target(entity, grid, target_x, target_y, step_duration=0.15):
    """
    Find path and animate entity to target.

    Args:
        entity: Entity to move
        grid: Grid with walkable tiles (unused directly - entity.find_path
               consults the grid the entity is attached to)
        target_x, target_y: Destination in grid coordinates
        step_duration: Animation time per tile
    """
    # Use the entity's own pathfinding (A* algorithm)
    path = entity.find_path((target_x, target_y))

    if not path:
        print("No path found!")
        return None

    # Consume the path into a waypoint list
    waypoints = []
    while path:
        step = path.walk()
        waypoints.append((step.x, step.y))

    # Create and start animator
    animator = PathAnimator(entity, waypoints, step_duration)
    animator.start()
    return animator


# Usage
animator = animate_to_target(player, grid, 15, 10)
if animator:
    animator.on_complete = lambda a: print("Arrived at destination!")
# endregion
