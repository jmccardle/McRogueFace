# mcrf: objects=[Color,Frame,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy

class AnimatedHealthBar:
    """Health bar with smooth fill animation."""

    def __init__(self, x, y, w, h, current, maximum):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.current = current
        self.display_current = current  # What's visually shown
        self.maximum = maximum
        self.timer_name = f"hp_anim_{id(self)}"

        # Background
        self.background = mcrfpy.Frame(pos=(x, y), size=(w, h))
        self.background.fill_color = mcrfpy.Color(40, 40, 40)
        self.background.outline = 2
        self.background.outline_color = mcrfpy.Color(60, 60, 60)

        # Damage preview (shows recent damage in different color)
        self.damage_fill = mcrfpy.Frame(pos=(x + 2, y + 2), size=(w - 4, h - 4))
        self.damage_fill.fill_color = mcrfpy.Color(180, 50, 50)
        self.damage_fill.outline = 0

        # Main fill
        self.fill = mcrfpy.Frame(pos=(x + 2, y + 2), size=(w - 4, h - 4))
        self.fill.fill_color = mcrfpy.Color(50, 200, 50)
        self.fill.outline = 0

        self._update_display()

    def _update_display(self):
        """Update the visual fill based on display_current."""
        ratio = max(0, min(1, self.display_current / self.maximum))
        self.fill.w = (self.w - 4) * ratio

        # Color based on ratio
        if ratio > 0.6:
            self.fill.fill_color = mcrfpy.Color(50, 200, 50)
        elif ratio > 0.3:
            self.fill.fill_color = mcrfpy.Color(230, 180, 30)
        else:
            self.fill.fill_color = mcrfpy.Color(200, 50, 50)

    def set_health(self, new_current, animate=True):
        """
        Set health with optional animation.

        Args:
            new_current: New health value
            animate: Whether to animate the transition
        """
        old_current = self.current
        self.current = max(0, min(self.maximum, new_current))

        if not animate:
            self.display_current = self.current
            self._update_display()
            return

        # Show damage preview immediately
        if self.current < old_current:
            damage_ratio = self.current / self.maximum
            self.damage_fill.w = (self.w - 4) * (old_current / self.maximum)

        # Animate the fill
        self._start_animation()

    def _start_animation(self):
        """Start animating toward target health."""
        self._animating = True

        def animate_step(timer, runtime):
            if not self._animating:
                return
            # Lerp toward target
            diff = self.current - self.display_current
            if abs(diff) < 0.5:
                self.display_current = self.current
                self._animating = False
                # Also update damage preview
                self.damage_fill.w = self.fill.w
            else:
                # Move 10% of the way each frame
                self.display_current += diff * 0.1
                # Continue animation
                mcrfpy.Timer(self.timer_name, animate_step, 16)

            self._update_display()

        mcrfpy.Timer(self.timer_name, animate_step, 16)

    def damage(self, amount):
        """Apply damage with animation."""
        self.set_health(self.current - amount, animate=True)

    def heal(self, amount):
        """Apply healing with animation."""
        self.set_health(self.current + amount, animate=True)

    def add_to_scene(self, ui):
        """Add all frames to scene."""
        ui.append(self.background)
        ui.append(self.damage_fill)
        ui.append(self.fill)


# Usage
scene = mcrfpy.Scene("animated_demo")

hp_bar = AnimatedHealthBar(50, 50, 300, 30, current=100, maximum=100)
hp_bar.add_to_scene(scene.children)

# Damage will animate smoothly
hp_bar.damage(40)

scene.activate()
