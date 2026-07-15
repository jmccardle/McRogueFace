# mcrf: objects=[Easing,Frame,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy
import random

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

game_container = mcrfpy.Frame(pos=(0, 0), size=(1024, 768))
scene.children.append(game_container)

def screen_shake_multi(frame, intensity=5, duration=0.3, shakes=4):
    """
    Shake frame in multiple random directions.

    Args:
        frame: The UI Frame to shake
        intensity: Maximum pixel offset
        duration: Total shake duration
        shakes: Number of shake movements
    """
    original_x = frame.x
    original_y = frame.y
    shake_interval = duration / shakes

    for i in range(shakes):
        # Decreasing intensity over time
        current_intensity = intensity * (1 - i / shakes)

        # Random offset direction
        offset_x = random.uniform(-current_intensity, current_intensity)
        offset_y = random.uniform(-current_intensity, current_intensity)

        def do_shake(timer, runtime, ox=offset_x, oy=offset_y, si=shake_interval):
            frame.animate("x", float(original_x + ox), si * 0.8, mcrfpy.Easing.EASE_OUT)
            frame.animate("y", float(original_y + oy), si * 0.8, mcrfpy.Easing.EASE_OUT)

        mcrfpy.Timer(f"shake_{i}", do_shake, max(1, int(i * shake_interval * 1000)), once=True)

    # Return to original position
    def reset(timer, runtime):
        frame.animate("x", float(original_x), shake_interval, mcrfpy.Easing.EASE_OUT)
        frame.animate("y", float(original_y), shake_interval, mcrfpy.Easing.EASE_OUT)

    mcrfpy.Timer("shake_reset", reset, int(duration * 1000), once=True)

# Usage
screen_shake_multi(game_container, intensity=10, duration=0.4, shakes=6)
