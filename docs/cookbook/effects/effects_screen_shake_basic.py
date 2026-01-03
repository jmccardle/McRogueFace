"""McRogueFace - Screen Shake Effect (basic)

Documentation: https://mcrogueface.github.io/cookbook/effects_screen_shake
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/effects/effects_screen_shake_basic.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy

def screen_shake(frame, intensity=5, duration=0.2):
    """
    Shake a frame/container by animating its position.

    Args:
        frame: The UI Frame to shake (often a container for all game elements)
        intensity: Maximum pixel offset
        duration: Total shake duration in seconds
    """
    original_x = frame.x
    original_y = frame.y

    # Quick shake to offset position
    shake_x = mcrfpy.Animation("x", float(original_x + intensity), duration / 4, "easeOut")
    shake_x.start(frame)

    # Schedule return to center
    def return_to_center(timer_name):
        anim = mcrfpy.Animation("x", float(original_x), duration / 2, "easeInOut")
        anim.start(frame)

    mcrfpy.Timer("shake_return", return_to_center, int(duration * 250), once=True)

# Usage - wrap your game content in a Frame
game_container = mcrfpy.Frame(0, 0, 1024, 768)
# ... add game elements to game_container.children ...
screen_shake(game_container, intensity=8, duration=0.3)