# mcrf: objects=[Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy


class FadeTransition:
    """Custom fade transition with callback support."""

    def __init__(self, current_scene, target_scene):
        """
        Args:
            current_scene: The mcrfpy.Scene object to transition from
            target_scene: The mcrfpy.Scene object to transition to
        """
        self.current_scene = current_scene
        self.target_scene = target_scene
        self.overlay = None

    def _create_overlay(self, scene):
        """Create a full-screen black overlay in the given scene."""
        self.overlay = mcrfpy.Frame(pos=(0, 0), size=(1024, 768))
        self.overlay.fill_color = mcrfpy.Color(0, 0, 0, 0)
        self.overlay.z_index = 9999  # On top of everything
        scene.children.append(self.overlay)

    def fade_out_in(self, duration=0.5, on_complete=None):
        """
        Fade to black, switch scene, fade in.

        Args:
            duration: Total transition time (half for out, half for in)
            on_complete: Callback when transition finishes
        """
        half_duration = duration / 2

        # Create overlay in current scene
        self._create_overlay(self.current_scene)

        # Fade to black
        self.overlay.animate("opacity", 1.0, half_duration, mcrfpy.Easing.EASE_IN)

        # Switch scene and fade in
        def switch_and_fade_in(timer, runtime):
            # Switch to new scene
            self.target_scene.activate()

            # Create overlay in new scene
            self._create_overlay(self.target_scene)
            self.overlay.opacity = 1.0  # Start fully opaque

            # Fade in
            self.overlay.animate("opacity", 0.0, half_duration, mcrfpy.Easing.EASE_OUT)

            # Cleanup and callback
            def cleanup(timer, runtime):
                self.target_scene.children.remove(self.overlay)
                if on_complete:
                    on_complete()

            mcrfpy.Timer("fade_cleanup", cleanup, int(half_duration * 1000) + 50, once=True)

        mcrfpy.Timer("fade_switch", switch_and_fade_in, int(half_duration * 1000), once=True)


# Usage
menu_scene = mcrfpy.Scene("menu")
game_scene = mcrfpy.Scene("game")


def on_transition_complete():
    print("Transition complete, game starting!")


# Start on menu, then transition to game
menu_scene.activate()

transition = FadeTransition(menu_scene, game_scene)
transition.fade_out_in(duration=0.8, on_complete=on_transition_complete)
