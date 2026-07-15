# mcrf: objects=[Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy


def flash_transition(current_scene, target_scene, color=(255, 255, 255), duration=0.4):
    """
    Flash to a color, then switch scene.

    Args:
        current_scene: The mcrfpy.Scene object to transition from
        target_scene: The mcrfpy.Scene object to transition to
        color: Flash color RGB tuple
        duration: Total transition time
    """
    # Create colored overlay in current scene
    overlay = mcrfpy.Frame(pos=(0, 0), size=(1024, 768))
    overlay.fill_color = mcrfpy.Color(color[0], color[1], color[2], 0)
    overlay.z_index = 9999
    current_scene.children.append(overlay)

    quarter = duration / 4

    # Flash in (fast)
    overlay.animate("opacity", 1.0, quarter, mcrfpy.Easing.EASE_OUT)

    # Hold, then switch and fade out
    def switch_scene(timer, runtime):
        target_scene.activate()

        # Create overlay in new scene
        new_overlay = mcrfpy.Frame(pos=(0, 0), size=(1024, 768))
        new_overlay.fill_color = mcrfpy.Color(color[0], color[1], color[2], 255)
        new_overlay.z_index = 9999
        target_scene.children.append(new_overlay)

        # Fade out (slower)
        new_overlay.animate("opacity", 0.0, duration / 2, mcrfpy.Easing.EASE_IN)

        # Cleanup
        def cleanup(timer, runtime):
            target_scene.children.remove(new_overlay)

        mcrfpy.Timer("flash_cleanup", cleanup, int(duration * 500) + 50, once=True)

    mcrfpy.Timer("flash_switch", switch_scene, int(quarter * 2000), once=True)


# Usage
game_scene = mcrfpy.Scene("game")
next_level_scene = mcrfpy.Scene("next_level")
death_scene = mcrfpy.Scene("death_screen")

mcrfpy.current_scene = game_scene
game_scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768)))

flash_transition(game_scene, next_level_scene, color=(255, 255, 255), duration=0.5)  # White flash
flash_transition(game_scene, death_scene, color=(255, 0, 0), duration=0.8)   # Red flash
