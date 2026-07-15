# mcrf: objects=[Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy


def wipe_transition(current_scene, target_scene, direction="right", duration=0.5, color=(0, 0, 0)):
    """
    Wipe transition from one edge.

    Args:
        current_scene: The mcrfpy.Scene object to transition from
        target_scene: The mcrfpy.Scene object to transition to
        direction: "left", "right", "up", "down"
        duration: Total transition time
        color: Wipe color
    """
    half = duration / 2

    # Set up wipe overlay based on direction
    if direction == "right":
        overlay = mcrfpy.Frame(pos=(0, 0), size=(0, 768))
        anim_prop = "w"
        anim_target = 1024
    elif direction == "left":
        overlay = mcrfpy.Frame(pos=(1024, 0), size=(0, 768))
        anim_prop = "x"  # Move left edge
        anim_target = 0
    elif direction == "down":
        overlay = mcrfpy.Frame(pos=(0, 0), size=(1024, 0))
        anim_prop = "h"
        anim_target = 768
    else:  # up
        overlay = mcrfpy.Frame(pos=(0, 768), size=(1024, 0))
        anim_prop = "y"
        anim_target = 0

    overlay.fill_color = mcrfpy.Color(color[0], color[1], color[2], 255)
    overlay.z_index = 9999
    current_scene.children.append(overlay)

    # Wipe in
    overlay.animate(anim_prop, float(anim_target), half, mcrfpy.Easing.EASE_IN_OUT)

    # Switch and wipe out
    def switch_and_wipe(timer, runtime):
        target_scene.activate()

        # Create covering overlay
        if direction == "right":
            new_overlay = mcrfpy.Frame(pos=(0, 0), size=(1024, 768))
            new_anim_prop = "x"
            new_anim_target = 1024
        elif direction == "left":
            new_overlay = mcrfpy.Frame(pos=(0, 0), size=(1024, 768))
            new_anim_prop = "w"
            new_anim_target = 0
        elif direction == "down":
            new_overlay = mcrfpy.Frame(pos=(0, 0), size=(1024, 768))
            new_anim_prop = "y"
            new_anim_target = -768
        else:
            new_overlay = mcrfpy.Frame(pos=(0, 0), size=(1024, 768))
            new_anim_prop = "h"
            new_anim_target = 0

        new_overlay.fill_color = mcrfpy.Color(color[0], color[1], color[2], 255)
        new_overlay.z_index = 9999
        target_scene.children.append(new_overlay)

        # Wipe out
        new_overlay.animate(new_anim_prop, float(new_anim_target), half, mcrfpy.Easing.EASE_IN_OUT)

        # Cleanup
        def cleanup(timer, runtime):
            target_scene.children.remove(new_overlay)

        mcrfpy.Timer("wipe_cleanup", cleanup, int(half * 1000) + 50, once=True)

    mcrfpy.Timer("wipe_switch", switch_and_wipe, int(half * 1000), once=True)


# Usage
game_scene = mcrfpy.Scene("game")
next_level = mcrfpy.Scene("next_level")
menu_scene = mcrfpy.Scene("menu")

mcrfpy.current_scene = game_scene
game_scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768)))

wipe_transition(game_scene, next_level, direction="right", duration=0.6)
wipe_transition(game_scene, menu_scene, direction="down", duration=0.4)
