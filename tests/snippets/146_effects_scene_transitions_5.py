# mcrf: objects=[Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy


class TransitionManager:
    """Manages scene transitions with multiple effect types."""

    def __init__(self, screen_width=1024, screen_height=768):
        self.width = screen_width
        self.height = screen_height
        self.is_transitioning = False
        self.current_scene = None  # Track active scene

    def go_to(self, target_scene, effect="fade", duration=0.5, **kwargs):
        """
        Transition to a scene with the specified effect.

        Args:
            target_scene: The mcrfpy.Scene object to transition to
            effect: "fade", "flash", "wipe", "instant"
            duration: Transition duration
            **kwargs: Effect-specific options (color, direction)
        """
        if self.is_transitioning:
            return

        if self.current_scene is None:
            # No current scene tracked, just activate target
            target_scene.activate()
            self.current_scene = target_scene
            return

        self.is_transitioning = True

        if effect == "instant":
            target_scene.activate()
            self.current_scene = target_scene
            self.is_transitioning = False

        elif effect == "fade":
            color = kwargs.get("color", (0, 0, 0))
            self._fade(target_scene, duration, color)

        elif effect == "flash":
            color = kwargs.get("color", (255, 255, 255))
            self._flash(target_scene, duration, color)

        elif effect == "wipe":
            direction = kwargs.get("direction", "right")
            color = kwargs.get("color", (0, 0, 0))
            self._wipe(target_scene, duration, direction, color)

    def _fade(self, target_scene, duration, color):
        half = duration / 2

        overlay = mcrfpy.Frame(pos=(0, 0), size=(self.width, self.height))
        overlay.fill_color = mcrfpy.Color(color[0], color[1], color[2], 0)
        overlay.z_index = 9999
        self.current_scene.children.append(overlay)

        overlay.animate("opacity", 1.0, half, mcrfpy.Easing.EASE_IN)

        def phase2(timer, runtime):
            target_scene.activate()

            new_overlay = mcrfpy.Frame(pos=(0, 0), size=(self.width, self.height))
            new_overlay.fill_color = mcrfpy.Color(color[0], color[1], color[2], 255)
            new_overlay.z_index = 9999
            target_scene.children.append(new_overlay)

            new_overlay.animate("opacity", 0.0, half, mcrfpy.Easing.EASE_OUT)

            def cleanup(timer, runtime):
                target_scene.children.remove(new_overlay)
                self.current_scene = target_scene
                self.is_transitioning = False

            mcrfpy.Timer("fade_done", cleanup, int(half * 1000) + 50, once=True)

        mcrfpy.Timer("fade_switch", phase2, int(half * 1000), once=True)

    def _flash(self, target_scene, duration, color):
        quarter = duration / 4

        overlay = mcrfpy.Frame(pos=(0, 0), size=(self.width, self.height))
        overlay.fill_color = mcrfpy.Color(color[0], color[1], color[2], 0)
        overlay.z_index = 9999
        self.current_scene.children.append(overlay)

        overlay.animate("opacity", 1.0, quarter, mcrfpy.Easing.EASE_OUT)

        def phase2(timer, runtime):
            target_scene.activate()

            new_overlay = mcrfpy.Frame(pos=(0, 0), size=(self.width, self.height))
            new_overlay.fill_color = mcrfpy.Color(color[0], color[1], color[2], 255)
            new_overlay.z_index = 9999
            target_scene.children.append(new_overlay)

            new_overlay.animate("opacity", 0.0, duration / 2, mcrfpy.Easing.EASE_IN)

            def cleanup(timer, runtime):
                target_scene.children.remove(new_overlay)
                self.current_scene = target_scene
                self.is_transitioning = False

            mcrfpy.Timer("flash_done", cleanup, int(duration * 500) + 50, once=True)

        mcrfpy.Timer("flash_switch", phase2, int(quarter * 2000), once=True)

    def _wipe(self, target_scene, duration, direction, color):
        # Simplified wipe - right direction only for brevity
        half = duration / 2

        overlay = mcrfpy.Frame(pos=(0, 0), size=(0, self.height))
        overlay.fill_color = mcrfpy.Color(color[0], color[1], color[2], 255)
        overlay.z_index = 9999
        self.current_scene.children.append(overlay)

        overlay.animate("w", float(self.width), half, mcrfpy.Easing.EASE_IN_OUT)

        def phase2(timer, runtime):
            target_scene.activate()

            new_overlay = mcrfpy.Frame(pos=(0, 0), size=(self.width, self.height))
            new_overlay.fill_color = mcrfpy.Color(color[0], color[1], color[2], 255)
            new_overlay.z_index = 9999
            target_scene.children.append(new_overlay)

            new_overlay.animate("x", float(self.width), half, mcrfpy.Easing.EASE_IN_OUT)

            def cleanup(timer, runtime):
                target_scene.children.remove(new_overlay)
                self.current_scene = target_scene
                self.is_transitioning = False

            mcrfpy.Timer("wipe_done", cleanup, int(half * 1000) + 50, once=True)

        mcrfpy.Timer("wipe_switch", phase2, int(half * 1000), once=True)


# Usage
# Create scenes
menu_scene = mcrfpy.Scene("menu")
game_scene = mcrfpy.Scene("game")
options_scene = mcrfpy.Scene("options")
next_level_scene = mcrfpy.Scene("next_level")

# Create transition manager and set initial scene
transitions = TransitionManager()
transitions.current_scene = menu_scene
menu_scene.activate()
menu_scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768)))

# Various transition styles
transitions.go_to(game_scene, effect="fade", duration=0.5)
transitions.go_to(menu_scene, effect="flash", color=(255, 255, 255), duration=0.4)
transitions.go_to(next_level_scene, effect="wipe", direction="right", duration=0.6)
transitions.go_to(options_scene, effect="instant")
