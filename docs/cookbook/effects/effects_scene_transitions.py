"""McRogueFace - Scene Transition Effects (effects_scene_transitions)

Documentation: https://mcrogueface.github.io/cookbook/effects_scene_transitions
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/effects/effects_scene_transitions.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy

class TransitionManager:
    """Manages scene transitions with multiple effect types."""

    def __init__(self, screen_width=1024, screen_height=768):
        self.width = screen_width
        self.height = screen_height
        self.is_transitioning = False

    def go_to(self, scene_name, effect="fade", duration=0.5, **kwargs):
        """
        Transition to a scene with the specified effect.

        Args:
            scene_name: Target scene
            effect: "fade", "flash", "wipe", "instant"
            duration: Transition duration
            **kwargs: Effect-specific options (color, direction)
        """
        if self.is_transitioning:
            return

        self.is_transitioning = True

        if effect == "instant":
            mcrfpy.setScene(scene_name)
            self.is_transitioning = False

        elif effect == "fade":
            color = kwargs.get("color", (0, 0, 0))
            self._fade(scene_name, duration, color)

        elif effect == "flash":
            color = kwargs.get("color", (255, 255, 255))
            self._flash(scene_name, duration, color)

        elif effect == "wipe":
            direction = kwargs.get("direction", "right")
            color = kwargs.get("color", (0, 0, 0))
            self._wipe(scene_name, duration, direction, color)

    def _fade(self, scene, duration, color):
        half = duration / 2
        ui = mcrfpy.sceneUI(mcrfpy.currentScene())

        overlay = mcrfpy.Frame(0, 0, self.width, self.height)
        overlay.fill_color = mcrfpy.Color(color[0], color[1], color[2], 0)
        overlay.z_index = 9999
        ui.append(overlay)

        anim = mcrfpy.Animation("opacity", 1.0, half, "easeIn")
        anim.start(overlay)

        def phase2(timer_name):
            mcrfpy.setScene(scene)
            new_ui = mcrfpy.sceneUI(scene)

            new_overlay = mcrfpy.Frame(0, 0, self.width, self.height)
            new_overlay.fill_color = mcrfpy.Color(color[0], color[1], color[2], 255)
            new_overlay.z_index = 9999
            new_ui.append(new_overlay)

            anim2 = mcrfpy.Animation("opacity", 0.0, half, "easeOut")
            anim2.start(new_overlay)

            def cleanup(timer_name):
                for i, elem in enumerate(new_ui):
                    if elem is new_overlay:
                        new_ui.remove(i)
                        break
                self.is_transitioning = False

            mcrfpy.Timer("fade_done", cleanup, int(half * 1000) + 50, once=True)

        mcrfpy.Timer("fade_switch", phase2, int(half * 1000), once=True)

    def _flash(self, scene, duration, color):
        quarter = duration / 4
        ui = mcrfpy.sceneUI(mcrfpy.currentScene())

        overlay = mcrfpy.Frame(0, 0, self.width, self.height)
        overlay.fill_color = mcrfpy.Color(color[0], color[1], color[2], 0)
        overlay.z_index = 9999
        ui.append(overlay)

        anim = mcrfpy.Animation("opacity", 1.0, quarter, "easeOut")
        anim.start(overlay)

        def phase2(timer_name):
            mcrfpy.setScene(scene)
            new_ui = mcrfpy.sceneUI(scene)

            new_overlay = mcrfpy.Frame(0, 0, self.width, self.height)
            new_overlay.fill_color = mcrfpy.Color(color[0], color[1], color[2], 255)
            new_overlay.z_index = 9999
            new_ui.append(new_overlay)

            anim2 = mcrfpy.Animation("opacity", 0.0, duration / 2, "easeIn")
            anim2.start(new_overlay)

            def cleanup(timer_name):
                for i, elem in enumerate(new_ui):
                    if elem is new_overlay:
                        new_ui.remove(i)
                        break
                self.is_transitioning = False

            mcrfpy.Timer("flash_done", cleanup, int(duration * 500) + 50, once=True)

        mcrfpy.Timer("flash_switch", phase2, int(quarter * 2000), once=True)

    def _wipe(self, scene, duration, direction, color):
        # Simplified wipe - right direction only for brevity
        half = duration / 2
        ui = mcrfpy.sceneUI(mcrfpy.currentScene())

        overlay = mcrfpy.Frame(0, 0, 0, self.height)
        overlay.fill_color = mcrfpy.Color(color[0], color[1], color[2], 255)
        overlay.z_index = 9999
        ui.append(overlay)

        anim = mcrfpy.Animation("w", float(self.width), half, "easeInOut")
        anim.start(overlay)

        def phase2(timer_name):
            mcrfpy.setScene(scene)
            new_ui = mcrfpy.sceneUI(scene)

            new_overlay = mcrfpy.Frame(0, 0, self.width, self.height)
            new_overlay.fill_color = mcrfpy.Color(color[0], color[1], color[2], 255)
            new_overlay.z_index = 9999
            new_ui.append(new_overlay)

            anim2 = mcrfpy.Animation("x", float(self.width), half, "easeInOut")
            anim2.start(new_overlay)

            def cleanup(timer_name):
                for i, elem in enumerate(new_ui):
                    if elem is new_overlay:
                        new_ui.remove(i)
                        break
                self.is_transitioning = False

            mcrfpy.Timer("wipe_done", cleanup, int(half * 1000) + 50, once=True)

        mcrfpy.Timer("wipe_switch", phase2, int(half * 1000), once=True)


# Usage
transitions = TransitionManager()

# Various transition styles
transitions.go_to("game", effect="fade", duration=0.5)
transitions.go_to("menu", effect="flash", color=(255, 255, 255), duration=0.4)
transitions.go_to("next_level", effect="wipe", direction="right", duration=0.6)
transitions.go_to("options", effect="instant")