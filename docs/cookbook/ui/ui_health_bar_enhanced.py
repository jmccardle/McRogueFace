"""McRogueFace - Health Bar Widget (enhanced)

Documentation: https://mcrogueface.github.io/cookbook/ui_health_bar
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/ui/ui_health_bar_enhanced.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy

class EnhancedHealthBar:
    """Health bar with text display, color transitions, and animations."""

    def __init__(self, x, y, w, h, current, maximum, show_text=True):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.current = current
        self.maximum = maximum
        self.show_text = show_text

        # Color thresholds (ratio -> color)
        self.colors = {
            0.6: mcrfpy.Color(50, 205, 50),   # Green when > 60%
            0.3: mcrfpy.Color(255, 165, 0),   # Orange when > 30%
            0.0: mcrfpy.Color(220, 20, 20),   # Red when <= 30%
        }

        # Background frame with dark fill
        self.background = mcrfpy.Frame(x, y, w, h)
        self.background.fill_color = mcrfpy.Color(30, 30, 30)
        self.background.outline = 2
        self.background.outline_color = mcrfpy.Color(100, 100, 100)

        # Fill frame (nested inside background conceptually)
        padding = 2
        self.fill = mcrfpy.Frame(
            x + padding,
            y + padding,
            w - padding * 2,
            h - padding * 2
        )
        self.fill.outline = 0

        # Text label
        self.label = None
        if show_text:
            self.label = mcrfpy.Caption(
                "",
                mcrfpy.default_font,
                x + w / 2 - 20,
                y + h / 2 - 8
            )
            self.label.fill_color = mcrfpy.Color(255, 255, 255)
            self.label.outline = 1
            self.label.outline_color = mcrfpy.Color(0, 0, 0)

        self._update()

    def _get_color_for_ratio(self, ratio):
        """Get the appropriate color based on health ratio."""
        for threshold, color in sorted(self.colors.items(), reverse=True):
            if ratio > threshold:
                return color
        # Return the lowest threshold color if ratio is 0 or below
        return self.colors[0.0]

    def _update(self):
        """Update fill width, color, and text."""
        ratio = max(0, min(1, self.current / self.maximum))

        # Update fill width (accounting for padding)
        padding = 2
        self.fill.w = (self.w - padding * 2) * ratio

        # Update color based on ratio
        self.fill.fill_color = self._get_color_for_ratio(ratio)

        # Update text
        if self.label:
            self.label.text = f"{int(self.current)}/{int(self.maximum)}"
            # Center the text
            text_width = len(self.label.text) * 8  # Approximate
            self.label.x = self.x + (self.w - text_width) / 2

    def set_health(self, current, maximum=None):
        """Update health values."""
        self.current = max(0, current)
        if maximum is not None:
            self.maximum = maximum
        self._update()

    def damage(self, amount):
        """Apply damage (convenience method)."""
        self.set_health(self.current - amount)

    def heal(self, amount):
        """Apply healing (convenience method)."""
        self.set_health(min(self.maximum, self.current + amount))

    def add_to_scene(self, ui):
        """Add all components to scene UI."""
        ui.append(self.background)
        ui.append(self.fill)
        if self.label:
            ui.append(self.label)


# Usage
mcrfpy.createScene("demo")
mcrfpy.setScene("demo")
ui = mcrfpy.sceneUI("demo")

# Create enhanced health bar
hp = EnhancedHealthBar(50, 50, 250, 25, current=100, maximum=100)
hp.add_to_scene(ui)

# Simulate damage
hp.damage(30)  # Now 70/100, shows green
hp.damage(25)  # Now 45/100, shows orange
hp.damage(20)  # Now 25/100, shows red