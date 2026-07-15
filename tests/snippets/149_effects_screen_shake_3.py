# mcrf: objects=[Easing,Grid,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy
import random

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

def camera_shake(grid, intensity=8, duration=0.3, shakes=4):
    """
    Shake the camera by animating grid.center.

    Args:
        grid: The Grid object
        intensity: Shake intensity in pixels
        duration: Total duration
        shakes: Number of shake movements
    """
    original_center_x = grid.center[0]
    original_center_y = grid.center[1]
    shake_interval = duration / shakes

    for i in range(shakes):
        decay = 1 - (i / shakes)  # Decreasing intensity
        offset_x = random.uniform(-intensity, intensity) * decay
        offset_y = random.uniform(-intensity, intensity) * decay

        def do_shake(timer, runtime, ox=offset_x, oy=offset_y, si=shake_interval,
                     cx=original_center_x, cy=original_center_y):
            grid.animate("center_x", cx + ox, si * 0.8, mcrfpy.Easing.EASE_OUT)
            grid.animate("center_y", cy + oy, si * 0.8, mcrfpy.Easing.EASE_OUT)

        mcrfpy.Timer(f"cam_shake_{i}", do_shake, max(1, int(i * shake_interval * 1000)), once=True)

    # Return to original
    def reset(timer, runtime):
        grid.animate("center_x", float(original_center_x), shake_interval, mcrfpy.Easing.EASE_OUT)
        grid.animate("center_y", float(original_center_y), shake_interval, mcrfpy.Easing.EASE_OUT)

    mcrfpy.Timer("cam_reset", reset, int(duration * 1000), once=True)

# Usage
camera_shake(grid, intensity=12, duration=0.25)
