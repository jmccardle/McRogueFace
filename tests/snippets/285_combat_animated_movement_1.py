# mcrf: objects=[Easing,Entity,Grid,InputState,Key,Scene,Timer] verified=0.3.6 status=ok
import mcrfpy

scene = mcrfpy.Scene("animated_movement")
mcrfpy.current_scene = scene

# A tiled grid, every cell walkable, so the screenshot shows a world to move through.
game_grid = grid = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(1024, 768),
    zoom=4.0,
)
scene.children.append(grid)

for gy in range(12):
    for gx in range(16):
        cell = grid.at(gx, gy)
        cell.tilesprite = 48 if (gx + gy) % 2 == 0 else 49
        cell.walkable = True

player = mcrfpy.Entity(grid_pos=(3, 5), texture=mcrfpy.default_texture, sprite_index=84)
enemy = mcrfpy.Entity(grid_pos=(12, 8), texture=mcrfpy.default_texture, sprite_index=112)
scout = mcrfpy.Entity(grid_pos=(2, 9), texture=mcrfpy.default_texture, sprite_index=85)
grid.entities.append(player)
grid.entities.append(enemy)
grid.entities.append(scout)


def end_player_turn():
    print("player turn over")


def end_enemy_turn():
    print("enemy turn over")


# region: basic
import mcrfpy

def move_with_animation(entity, new_x, new_y, duration=0.2):
    """Move entity smoothly to new position."""
    entity.grid_pos = (new_x, new_y)   # logical cell, immediately
    entity.animate("draw_pos", (new_x, new_y), duration, mcrfpy.Easing.EASE_IN_OUT)
# endregion


# region: callback
import mcrfpy

# Track animation state
is_animating = False

def move_with_callback(entity, new_x, new_y, duration=0.2, on_complete=None):
    """Move entity with completion callback."""
    global is_animating
    is_animating = True

    def animation_done(target, prop, value):
        global is_animating
        is_animating = False
        if on_complete:
            on_complete()

    entity.grid_pos = (new_x, new_y)
    entity.animate("draw_pos", (new_x, new_y), duration, mcrfpy.Easing.EASE_IN_OUT,
                   callback=animation_done)


# Usage in turn-based game
def player_move(direction):
    if is_animating:
        return  # Block input during animation

    dx, dy = direction
    new_x = player.grid_x + dx
    new_y = player.grid_y + dy

    def on_move_complete():
        end_player_turn()

    move_with_callback(player, new_x, new_y, on_complete=on_move_complete)
# endregion


# region: easings
# Easing options (mcrfpy.Easing enum):
# LINEAR       - Constant speed
# EASE_IN      - Slow start, fast end
# EASE_OUT     - Fast start, slow end
# EASE_IN_OUT  - Slow start and end (smooth)
# (also: *_QUAD, *_CUBIC, *_SINE, *_ELASTIC, *_BOUNCE, *_BACK, *_EXPO variants)

# Examples of each (target is a cell, in tiles)
def demo_easings(entity, target):
    # Linear - mechanical, robotic movement
    entity.animate("draw_pos", target, 0.5, mcrfpy.Easing.LINEAR)

    # EaseIn - accelerating (good for falling)
    entity.animate("draw_pos", target, 0.5, mcrfpy.Easing.EASE_IN)

    # EaseOut - decelerating (good for stopping)
    entity.animate("draw_pos", target, 0.5, mcrfpy.Easing.EASE_OUT)

    # EaseInOut - natural movement (best for walking)
    entity.animate("draw_pos", target, 0.5, mcrfpy.Easing.EASE_IN_OUT)
# endregion


# region: camera
def animate_camera_follow(grid, target_x, target_y, duration=0.2):
    """Smoothly pan camera to follow entity."""
    # Grid center is in pixel coordinates (tile_size = 16)
    center_x = (target_x + 0.5) * 16
    center_y = (target_y + 0.5) * 16

    grid.animate("center", (center_x, center_y), duration, mcrfpy.Easing.LINEAR)


def move_player_with_camera(player, grid, new_x, new_y, duration=0.2):
    """Move player and camera together."""

    def on_complete(target, prop, value):
        # Ensure camera is exactly centered after animation
        grid.center = ((new_x + 0.5) * 16, (new_y + 0.5) * 16)

    # Animate player
    player.grid_pos = (new_x, new_y)
    player.animate("draw_pos", (new_x, new_y), duration, mcrfpy.Easing.EASE_IN_OUT,
                   callback=on_complete)

    # Animate camera
    animate_camera_follow(grid, new_x, new_y, duration)
# endregion


# region: path
class PathAnimator:
    """Animate entity movement along a path."""

    def __init__(self, entity, path, step_duration=0.2, on_complete=None):
        self.entity = entity
        self.path = list(path)  # Copy the path
        self.step_duration = step_duration
        self.on_complete = on_complete
        self.current_step = 0
        self.animating = False

    def start(self):
        """Begin path animation."""
        if not self.path or self.animating:
            return

        self.animating = True
        self.current_step = 0
        self._animate_next_step()

    def _animate_next_step(self):
        """Animate to next path position."""
        if self.current_step >= len(self.path):
            # Path complete
            self.animating = False
            if self.on_complete:
                self.on_complete()
            return

        target_x, target_y = self.path[self.current_step]

        # Update the logical cell immediately; draw_pos animates separately
        self.entity.grid_pos = (target_x, target_y)

        # Create step animation
        self.entity.animate("draw_pos", (target_x, target_y), self.step_duration,
                            mcrfpy.Easing.EASE_IN_OUT)

        # Schedule next step
        self.current_step += 1
        delay_ms = int(self.step_duration * 1000) + 20  # Small buffer

        def continue_path(timer, runtime):
            if self.animating:  # Check if still active
                self._animate_next_step()

        mcrfpy.Timer(f"path_{id(self)}", continue_path, delay_ms)

    def stop(self):
        """Stop path animation."""
        self.animating = False  # Timer callbacks will check this flag


# Usage
def move_enemy_along_path(enemy, player, grid):
    path = enemy.path_to(player.grid_x, player.grid_y)

    if not path:
        return

    # Only move a few steps per turn
    path = path[:3]

    def on_path_complete():
        end_enemy_turn()

    animator = PathAnimator(enemy, path, step_duration=0.15, on_complete=on_path_complete)
    animator.start()
# endregion


# region: queue
class MovementController:
    """Handles queued movement with animations."""

    def __init__(self, entity, grid, move_duration=0.2):
        self.entity = entity
        self.grid = grid
        self.move_duration = move_duration
        self.is_moving = False
        self.move_queue = []
        self.max_queue = 2

    def queue_move(self, dx, dy):
        """Add a move to the queue."""
        if len(self.move_queue) < self.max_queue:
            self.move_queue.append((dx, dy))

        if not self.is_moving:
            self._process_queue()

    def _process_queue(self):
        """Process the next queued move."""
        if not self.move_queue:
            self.is_moving = False
            return

        dx, dy = self.move_queue.pop(0)
        current_x = self.entity.grid_x
        current_y = self.entity.grid_y
        new_x = current_x + dx
        new_y = current_y + dy

        # Validate move
        if not self._is_valid_move(new_x, new_y):
            self._process_queue()  # Try next queued move
            return

        self.is_moving = True
        self._animate_move(new_x, new_y)

    def _is_valid_move(self, x, y):
        """Check if move is valid."""
        grid_w, grid_h = self.grid.grid_size
        if x < 0 or x >= grid_w or y < 0 or y >= grid_h:
            return False
        return self.grid.at(x, y).walkable

    def _animate_move(self, new_x, new_y):
        """Perform the animated move."""

        def on_complete(target, prop, value):
            self.entity.grid_pos = (new_x, new_y)
            self._process_queue()

        self.entity.animate("draw_pos", (new_x, new_y), self.move_duration,
                            mcrfpy.Easing.EASE_IN_OUT, callback=on_complete)

        # Also animate camera
        center_x = (new_x + 0.5) * 16
        center_y = (new_y + 0.5) * 16

        self.grid.animate("center", (center_x, center_y), self.move_duration, mcrfpy.Easing.LINEAR)


# Usage (assumes scene, player, game_grid already defined)
controller = MovementController(player, game_grid, move_duration=0.15)

def handle_input(key, action):
    if action == mcrfpy.InputState.RELEASED:  # PRESSED and REPEATED: a held key keeps moving (#549)
        return

    if key in (mcrfpy.Key.W, mcrfpy.Key.UP):
        controller.queue_move(0, -1)
    elif key in (mcrfpy.Key.S, mcrfpy.Key.DOWN):
        controller.queue_move(0, 1)
    elif key in (mcrfpy.Key.A, mcrfpy.Key.LEFT):
        controller.queue_move(-1, 0)
    elif key in (mcrfpy.Key.D, mcrfpy.Key.RIGHT):
        controller.queue_move(1, 0)

scene.on_key = handle_input
# endregion


# region: bump
def move_or_bump(entity, new_x, new_y, grid, duration=0.2):
    """Move to position, or bump animation if blocked."""

    if grid.at(new_x, new_y).walkable:
        # Normal move
        entity.grid_pos = (new_x, new_y)
        entity.animate("draw_pos", (new_x, new_y), duration, mcrfpy.Easing.EASE_IN_OUT)
    else:
        # Bump animation - move partway then back
        current_x = entity.draw_pos.x
        current_y = entity.draw_pos.y

        # Calculate bump position (1/4 of the way)
        bump_x = current_x + (new_x - current_x) * 0.25
        bump_y = current_y + (new_y - current_y) * 0.25

        def bump_back(target, prop, value):
            # Return to original position
            target.animate("draw_pos", (current_x, current_y), duration * 0.5,
                           mcrfpy.Easing.EASE_OUT)

        # Bump forward
        entity.animate("draw_pos", (bump_x, bump_y), duration * 0.5, mcrfpy.Easing.EASE_OUT,
                       callback=bump_back)
# endregion


# region: lunge
def attack_lunge(attacker, target, duration=0.15):
    """Lunge toward target for attack animation."""
    start_x = attacker.draw_pos.x
    start_y = attacker.draw_pos.y

    # Calculate lunge position (halfway to target)
    lunge_x = start_x + (target.draw_pos.x - start_x) * 0.5
    lunge_y = start_y + (target.draw_pos.y - start_y) * 0.5

    def return_to_start(anim_target, prop, value):
        # Return to starting position
        anim_target.animate("draw_pos", (start_x, start_y), duration, mcrfpy.Easing.EASE_OUT)

    # Lunge forward
    attacker.animate("draw_pos", (lunge_x, lunge_y), duration, mcrfpy.Easing.EASE_IN,
                     callback=return_to_start)
# endregion


# What a reader does with the helpers above: the player walks, the enemy is chased
# along a path, and the scout keeps a handle on its animation.
move_with_animation(player, 7, 5)
move_enemy_along_path(enemy, player, grid)

entity = scout
# region: tip
current_anim = entity.animate("draw_pos", (5, 3), 0.5, mcrfpy.Easing.LINEAR)
current_anim.is_complete   # False while running
current_anim.stop()        # cancel where it is (no final value, no callback)
# endregion
