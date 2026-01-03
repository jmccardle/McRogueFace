"""McRogueFace - Screen Shake Effect (multi)

Documentation: https://mcrogueface.github.io/cookbook/effects_screen_shake
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/effects/effects_screen_shake_multi.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

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

    def reverse(timer_name):
        shaker._animate_position(
            shaker.original_x - dir_x * intensity * 0.5,
            shaker.original_y - dir_y * intensity * 0.5,
            duration / 3
        )

    def reset(timer_name):
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