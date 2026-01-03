"""McRogueFace - Selection Menu Widget (enhanced)

Documentation: https://mcrogueface.github.io/cookbook/ui_menu
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/ui/ui_menu_enhanced.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy

class MenuBar:
    """Horizontal menu bar with dropdown submenus."""

    def __init__(self, y=0, items=None):
        """
        Create a menu bar.

        Args:
            y: Y position (usually 0 for top)
            items: List of dicts with 'label' and 'options' keys
        """
        self.y = y
        self.items = items or []
        self.selected_item = 0
        self.dropdown_open = False
        self.dropdown_selected = 0

        self.item_width = 100
        self.height = 30

        # Main bar frame
        self.bar = mcrfpy.Frame(0, y, 1024, self.height)
        self.bar.fill_color = mcrfpy.Color(50, 50, 70)
        self.bar.outline = 0

        # Item captions
        self.item_captions = []
        for i, item in enumerate(items):
            cap = mcrfpy.Caption(
                item['label'],
                mcrfpy.default_font,
                10 + i * self.item_width,
                y + 7
            )
            cap.fill_color = mcrfpy.Color(200, 200, 200)
            self.item_captions.append(cap)

        # Dropdown panel (hidden initially)
        self.dropdown = None
        self.dropdown_captions = []

    def _update_highlight(self):
        """Update visual selection on bar."""
        for i, cap in enumerate(self.item_captions):
            if i == self.selected_item and self.dropdown_open:
                cap.fill_color = mcrfpy.Color(255, 255, 100)
            else:
                cap.fill_color = mcrfpy.Color(200, 200, 200)

    def _show_dropdown(self, ui):
        """Show dropdown for selected item."""
        # Remove existing dropdown
        self._hide_dropdown(ui)

        item = self.items[self.selected_item]
        options = item.get('options', [])

        if not options:
            return

        x = 5 + self.selected_item * self.item_width
        y = self.y + self.height
        width = 150
        height = len(options) * 25 + 10

        self.dropdown = mcrfpy.Frame(x, y, width, height)
        self.dropdown.fill_color = mcrfpy.Color(40, 40, 60, 250)
        self.dropdown.outline = 1
        self.dropdown.outline_color = mcrfpy.Color(80, 80, 100)
        ui.append(self.dropdown)

        self.dropdown_captions = []
        for i, opt in enumerate(options):
            cap = mcrfpy.Caption(
                opt['label'],
                mcrfpy.default_font,
                x + 10,
                y + 5 + i * 25
            )
            cap.fill_color = mcrfpy.Color(200, 200, 200)
            self.dropdown_captions.append(cap)
            ui.append(cap)

        self.dropdown_selected = 0
        self._update_dropdown_highlight()

    def _hide_dropdown(self, ui):
        """Hide dropdown menu."""
        if self.dropdown:
            try:
                ui.remove(self.dropdown)
            except:
                pass
            self.dropdown = None

        for cap in self.dropdown_captions:
            try:
                ui.remove(cap)
            except:
                pass
        self.dropdown_captions = []

    def _update_dropdown_highlight(self):
        """Update dropdown selection highlight."""
        for i, cap in enumerate(self.dropdown_captions):
            if i == self.dropdown_selected:
                cap.fill_color = mcrfpy.Color(255, 255, 100)
            else:
                cap.fill_color = mcrfpy.Color(200, 200, 200)

    def add_to_scene(self, ui):
        ui.append(self.bar)
        for cap in self.item_captions:
            ui.append(cap)

    def handle_key(self, key, ui):
        """Handle keyboard navigation."""
        if not self.dropdown_open:
            if key == "Left":
                self.selected_item = (self.selected_item - 1) % len(self.items)
                self._update_highlight()
            elif key == "Right":
                self.selected_item = (self.selected_item + 1) % len(self.items)
                self._update_highlight()
            elif key == "Return" or key == "Down":
                self.dropdown_open = True
                self._show_dropdown(ui)
                self._update_highlight()
        else:
            if key == "Up":
                options = self.items[self.selected_item].get('options', [])
                self.dropdown_selected = (self.dropdown_selected - 1) % len(options)
                self._update_dropdown_highlight()
            elif key == "Down":
                options = self.items[self.selected_item].get('options', [])
                self.dropdown_selected = (self.dropdown_selected + 1) % len(options)
                self._update_dropdown_highlight()
            elif key == "Return":
                opt = self.items[self.selected_item]['options'][self.dropdown_selected]
                if opt.get('action'):
                    opt['action']()
                self.dropdown_open = False
                self._hide_dropdown(ui)
                self._update_highlight()
            elif key == "Escape":
                self.dropdown_open = False
                self._hide_dropdown(ui)
                self._update_highlight()