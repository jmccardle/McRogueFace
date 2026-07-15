# mcrf: objects=[Easing,Frame,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

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
    frame.animate("x", float(original_x + intensity), duration / 4, mcrfpy.Easing.EASE_OUT)

    # Schedule return to center
    def return_to_center(timer, runtime):
        frame.animate("x", float(original_x), duration / 2, mcrfpy.Easing.EASE_IN_OUT)

    mcrfpy.Timer("shake_return", return_to_center, int(duration * 250), once=True)

# Usage - wrap your game content in a Frame
game_container = mcrfpy.Frame(pos=(0, 0), size=(1024, 768))
scene.children.append(game_container)
# ... add game elements to game_container.children ...
screen_shake(game_container, intensity=8, duration=0.3)
