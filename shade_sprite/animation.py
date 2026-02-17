"""AnimatedSprite - animation state machine for sprite sheet playback.

Wraps an mcrfpy.Sprite with frame timing and directional animation.
Call tick() each frame (or from a timer) to advance the animation.
"""
from .formats import Direction, SheetFormat, AnimDef


class AnimatedSprite:
    """Animates an mcrfpy.Sprite using a SheetFormat definition.

    The sprite's sprite_index is updated automatically based on the
    current animation, direction, and elapsed time.

    Args:
        sprite: An mcrfpy.Sprite object to animate
        fmt: SheetFormat describing the sheet layout
        direction: Initial facing direction (default: Direction.S)
    """

    def __init__(self, sprite, fmt, direction=Direction.S):
        self.sprite = sprite
        self.fmt = fmt
        self._direction = direction
        self._anim_name = None
        self._anim = None
        self._frame_idx = 0
        self._elapsed = 0.0
        self._finished = False

        # Start with idle if available
        if "idle" in fmt.animations:
            self.play("idle")

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, d):
        if not isinstance(d, Direction):
            d = Direction(d)
        if d != self._direction:
            self._direction = d
            self._update_tile()

    @property
    def animation_name(self):
        return self._anim_name

    @property
    def frame_index(self):
        return self._frame_idx

    @property
    def finished(self):
        return self._finished

    def set_direction(self, d):
        """Set facing direction. Updates tile immediately."""
        self.direction = d

    def play(self, anim_name):
        """Start playing a named animation.

        Args:
            anim_name: Animation name (must exist in the format's animations dict)

        Raises:
            KeyError: If animation name not found in format
        """
        if anim_name not in self.fmt.animations:
            raise KeyError(
                f"Animation '{anim_name}' not found in format '{self.fmt.name}'. "
                f"Available: {list(self.fmt.animations.keys())}"
            )
        self._anim_name = anim_name
        self._anim = self.fmt.animations[anim_name]
        self._frame_idx = 0
        self._elapsed = 0.0
        self._finished = False
        self._update_tile()

    def tick(self, dt_ms):
        """Advance animation clock by dt_ms milliseconds.

        Call this from a timer callback or game loop. Updates the
        sprite's sprite_index when frames change.

        Args:
            dt_ms: Time elapsed in milliseconds since last tick
        """
        if self._anim is None or self._finished:
            return

        self._elapsed += dt_ms
        frames = self._anim.frames

        # Advance frames while we have accumulated enough time
        while self._elapsed >= frames[self._frame_idx].duration:
            self._elapsed -= frames[self._frame_idx].duration
            self._frame_idx += 1

            if self._frame_idx >= len(frames):
                if self._anim.loop:
                    self._frame_idx = 0
                else:
                    # One-shot finished
                    if self._anim.chain_to and self._anim.chain_to in self.fmt.animations:
                        self.play(self._anim.chain_to)
                        return
                    else:
                        # Stay on last frame
                        self._frame_idx = len(frames) - 1
                        self._finished = True
                        self._elapsed = 0.0
                        break

        self._update_tile()

    def _update_tile(self):
        """Set sprite.sprite_index based on current animation frame and direction."""
        if self._anim is None:
            return
        frame = self._anim.frames[self._frame_idx]
        idx = self.fmt.sprite_index(frame.col, self._direction)
        self.sprite.sprite_index = idx
