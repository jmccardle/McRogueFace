"""McRogueFace - Health Bar Widget (multi)

Documentation: https://mcrogueface.github.io/cookbook/ui_health_bar
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/ui/ui_health_bar_multi.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy

class ResourceBar:
    """Generic resource bar that can represent any stat."""

    def __init__(self, x, y, w, h, current, maximum,
                 fill_color, bg_color=None, label=""):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.current = current
        self.maximum = maximum
        self.label_text = label

        if bg_color is None:
            bg_color = mcrfpy.Color(30, 30, 30)

        # Background
        self.background = mcrfpy.Frame(x, y, w, h)
        self.background.fill_color = bg_color
        self.background.outline = 1
        self.background.outline_color = mcrfpy.Color(60, 60, 60)

        # Fill
        self.fill = mcrfpy.Frame(x + 1, y + 1, w - 2, h - 2)
        self.fill.fill_color = fill_color
        self.fill.outline = 0

        # Label (left side)
        self.label = mcrfpy.Caption(label, mcrfpy.default_font, x - 30, y + 2)
        self.label.fill_color = mcrfpy.Color(200, 200, 200)

        self._update()

    def _update(self):
        ratio = max(0, min(1, self.current / self.maximum))
        self.fill.w = (self.w - 2) * ratio

    def set_value(self, current, maximum=None):
        self.current = max(0, current)
        if maximum:
            self.maximum = maximum
        self._update()

    def add_to_scene(self, ui):
        if self.label_text:
            ui.append(self.label)
        ui.append(self.background)
        ui.append(self.fill)


class PlayerStats:
    """Collection of resource bars for a player."""

    def __init__(self, x, y):
        bar_width = 200
        bar_height = 18
        spacing = 25

        self.hp = ResourceBar(
            x, y, bar_width, bar_height,
            current=100, maximum=100,
            fill_color=mcrfpy.Color(220, 50, 50),
            label="HP"
        )

        self.mp = ResourceBar(
            x, y + spacing, bar_width, bar_height,
            current=50, maximum=50,
            fill_color=mcrfpy.Color(50, 100, 220),
            label="MP"
        )

        self.stamina = ResourceBar(
            x, y + spacing * 2, bar_width, bar_height,
            current=80, maximum=80,
            fill_color=mcrfpy.Color(50, 180, 50),
            label="SP"
        )

    def add_to_scene(self, ui):
        self.hp.add_to_scene(ui)
        self.mp.add_to_scene(ui)
        self.stamina.add_to_scene(ui)


# Usage
mcrfpy.createScene("stats_demo")
mcrfpy.setScene("stats_demo")
ui = mcrfpy.sceneUI("stats_demo")

stats = PlayerStats(80, 20)
stats.add_to_scene(ui)

# Update individual stats
stats.hp.set_value(75)
stats.mp.set_value(30)
stats.stamina.set_value(60)