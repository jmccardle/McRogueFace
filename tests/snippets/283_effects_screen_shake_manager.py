# mcrf: objects=[Easing,Grid,Scene,Timer] verified=0.3.6-dev status=ok
# Screen shake manager with presets, and a directional shake built on it
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

# Give the camera something to shake: a checkerboard of two tile sprites
for y in range(12):
    for x in range(16):
        grid.at(x, y).tilesprite = 48 + (x + y) % 2

# region: manager
import mcrfpy
import random

class ScreenShakeManager:
    """Manages screen shake effects with presets and queuing."""

    def __init__(self, target, mode="frame"):
        """
        Args:
            target: Frame or Grid to shake
            mode: "frame" for Frame.x/y, "camera" for Grid.center
        """
        self.target = target
        self.mode = mode
        self.is_shaking = False
        self.shake_id = 0

        # Store original position
        if mode == "frame":
            self.original_x = target.x
            self.original_y = target.y
        else:
            self.original_x = target.center[0]
            self.original_y = target.center[1]

    def _get_position(self):
        if self.mode == "frame":
            return self.target.x, self.target.y
        else:
            return self.target.center

    def _animate_position(self, x, y, duration, easing=None):
        easing = easing or mcrfpy.Easing.EASE_OUT
        if self.mode == "frame":
            self.target.animate("x", float(x), duration, easing)
            self.target.animate("y", float(y), duration, easing)
        else:
            self.target.animate("center_x", float(x), duration, easing)
            self.target.animate("center_y", float(y), duration, easing)

    def shake(self, intensity=5, duration=0.3, shakes=4, decay=True):
        """
        Perform a screen shake.

        Args:
            intensity: Maximum pixel offset
            duration: Total duration in seconds
            shakes: Number of shake movements
            decay: If True, intensity decreases over time
        """
        if self.is_shaking:
            return  # Don't interrupt ongoing shake

        self.is_shaking = True
        self.shake_id += 1
        current_id = self.shake_id
        shake_interval = duration / shakes

        for i in range(shakes):
            # Calculate intensity with optional decay
            if decay:
                current_intensity = intensity * (1 - i / shakes)
            else:
                current_intensity = intensity

            offset_x = random.uniform(-current_intensity, current_intensity)
            offset_y = random.uniform(-current_intensity, current_intensity)

            def do_shake(timer, runtime, ox=offset_x, oy=offset_y, si=shake_interval,
                        sid=current_id):
                if self.shake_id != sid:
                    return  # Cancelled
                self._animate_position(
                    self.original_x + ox,
                    self.original_y + oy,
                    si * 0.8
                )

            mcrfpy.Timer(f"shake_{current_id}_{i}", do_shake,
                        max(1, int(i * shake_interval * 1000)), once=True)

        # Reset to original
        def reset(timer, runtime, sid=current_id):
            if self.shake_id != sid:
                return
            self._animate_position(self.original_x, self.original_y, shake_interval)
            self.is_shaking = False

        mcrfpy.Timer(f"shake_reset_{current_id}", reset,
                    int(duration * 1000), once=True)

    def update_origin(self):
        """Update stored origin (call after camera moves)."""
        if self.mode == "frame":
            self.original_x = self.target.x
            self.original_y = self.target.y
        else:
            self.original_x = self.target.center[0]
            self.original_y = self.target.center[1]

    # Preset effects
    def light_hit(self):
        """Small shake for minor impacts."""
        self.shake(intensity=3, duration=0.15, shakes=2)

    def heavy_hit(self):
        """Medium shake for significant damage."""
        self.shake(intensity=8, duration=0.25, shakes=4)

    def explosion(self):
        """Large shake for explosions."""
        self.shake(intensity=15, duration=0.4, shakes=6)

    def earthquake(self):
        """Long, rumbling shake."""
        self.shake(intensity=6, duration=1.0, shakes=12, decay=False)

    def death(self):
        """Dramatic shake for player/boss death."""
        self.shake(intensity=20, duration=0.5, shakes=8)


# Setup
shaker = ScreenShakeManager(grid, mode="camera")

# Usage
shaker.light_hit()   # Small impact
shaker.heavy_hit()   # Bigger impact
shaker.explosion()   # Boom!
shaker.earthquake()  # Environmental effect
shaker.death()       # Dramatic moment

# After player moves, update origin so shakes return to correct position
grid.center = (grid.center[0] + 32, grid.center[1])  # e.g. the camera follows the player
shaker.update_origin()
# endregion

# region: directional
import mcrfpy
import math

def directional_shake(shaker, direction_x, direction_y, intensity=10, duration=0.2):
    """
    Shake in a specific direction (e.g., direction of impact).

    Args:
        shaker: ScreenShakeManager instance
        direction_x, direction_y: Direction vector (will be normalized)
        intensity: Shake strength
        duration: Shake duration
    """
    # Normalize direction
    length = math.sqrt(direction_x * direction_x + direction_y * direction_y)
    if length == 0:
        return

    dir_x = direction_x / length
    dir_y = direction_y / length

    # Shake in the direction, then opposite, then back
    shaker._animate_position(
        shaker.original_x + dir_x * intensity,
        shaker.original_y + dir_y * intensity,
        duration / 3
    )

    def reverse(timer, runtime):
        shaker._animate_position(
            shaker.original_x - dir_x * intensity * 0.5,
            shaker.original_y - dir_y * intensity * 0.5,
            duration / 3
        )

    def reset(timer, runtime):
        shaker._animate_position(
            shaker.original_x,
            shaker.original_y,
            duration / 3
        )
        shaker.is_shaking = False

    mcrfpy.Timer("dir_shake_rev", reverse, int(duration * 333), once=True)
    mcrfpy.Timer("dir_shake_reset", reset, int(duration * 666), once=True)

# Usage: shake away from impact direction
hit_from_x, hit_from_y = -1, 0  # Hit from the left
directional_shake(shaker, hit_from_x, hit_from_y, intensity=12)
# endregion
