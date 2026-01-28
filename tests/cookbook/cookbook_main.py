#!/usr/bin/env python3
"""McRogueFace Cookbook - Interactive Demo Launcher

A comprehensive collection of reusable UI widgets and interactive demos
showcasing McRogueFace capabilities.

Controls:
    Up/Down: Navigate menu
    Enter: Run selected demo
    ESC: Exit (or go back from demo)
"""
import mcrfpy
import sys
import os

# Ensure lib is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class CookbookLauncher:
    """Main launcher for the cookbook demos."""

    DEMOS = {
        "Primitives": [
            ("Button Widget", "primitives.demo_button"),
            ("Stat Bar Widget", "primitives.demo_stat_bar"),
            ("Choice List Widget", "primitives.demo_choice_list"),
            ("Text Box Widget", "primitives.demo_text_box"),
            ("Toast Notifications", "primitives.demo_toast"),
            ("Drag & Drop (Frame)", "primitives.demo_drag_drop_frame"),
            ("Drag & Drop (Grid)", "primitives.demo_drag_drop_grid"),
            ("Click to Pick Up", "primitives.demo_click_pickup"),
        ],
        "Features": [
            ("Animation Chain/Group", "features.demo_animation_chain"),
            ("Shader Effects", "features.demo_shaders"),
            ("Rotation & Origin", "features.demo_rotation"),
            ("Alignment (TODO)", None),
        ],
        "Mini-Apps": [
            ("Calculator", "apps.calculator"),
            ("Dialogue System", "apps.dialogue_system"),
            ("Day/Night Shadows (TODO)", None),
        ],
        "Compound": [
            ("Shop Demo", "compound.shop_demo"),
            ("Inventory UI (TODO)", None),
            ("Character Sheet (TODO)", None),
        ],
    }

    def __init__(self):
        self.scene = mcrfpy.Scene("cookbook_main")
        self.ui = self.scene.children
        self.selected_category = 0
        self.selected_item = 0
        self.categories = list(self.DEMOS.keys())
        self.setup()

    def setup(self):
        """Build the launcher UI."""
        # Background
        bg = mcrfpy.Frame(
            pos=(0, 0),
            size=(1024, 768),
            fill_color=mcrfpy.Color(15, 15, 20)
        )
        self.ui.append(bg)

        # Title
        title = mcrfpy.Caption(
            text="McRogueFace Cookbook",
            pos=(512, 40),
            font_size=36,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        title.outline = 3
        title.outline_color = mcrfpy.Color(0, 0, 0)
        self.ui.append(title)

        # Subtitle
        subtitle = mcrfpy.Caption(
            text="Widget Library & Interactive Demos",
            pos=(512, 85),
            font_size=18,
            fill_color=mcrfpy.Color(150, 150, 180)
        )
        self.ui.append(subtitle)

        # Create category panels
        self.category_frames = []
        self.item_labels = {}

        panel_width = 220
        panel_spacing = 30
        start_x = (1024 - (len(self.categories) * panel_width + (len(self.categories) - 1) * panel_spacing)) // 2

        for i, category in enumerate(self.categories):
            x = start_x + i * (panel_width + panel_spacing)
            self._create_category_panel(category, x, 130, panel_width)

        # Instructions
        instr = mcrfpy.Caption(
            text="Arrow Keys: Navigate | Enter: Run Demo | ESC: Exit",
            pos=(512, 720),
            font_size=14,
            fill_color=mcrfpy.Color(100, 100, 100)
        )
        self.ui.append(instr)

        # Update display
        self._update_selection()

    def _create_category_panel(self, category, x, y, width):
        """Create a category panel with demo items."""
        items = self.DEMOS[category]

        # Calculate panel height
        header_height = 40
        item_height = 35
        padding = 10
        panel_height = header_height + len(items) * item_height + padding * 2

        # Panel background
        panel = mcrfpy.Frame(
            pos=(x, y),
            size=(width, panel_height),
            fill_color=mcrfpy.Color(30, 30, 40),
            outline_color=mcrfpy.Color(60, 60, 80),
            outline=2
        )
        self.ui.append(panel)
        self.category_frames.append(panel)

        # Category title
        cat_title = mcrfpy.Caption(
            text=category,
            pos=(width // 2, 12),
            font_size=16,
            fill_color=mcrfpy.Color(200, 200, 220)
        )
        panel.children.append(cat_title)

        # Separator line
        sep = mcrfpy.Frame(
            pos=(10, 35),
            size=(width - 20, 2),
            fill_color=mcrfpy.Color(60, 60, 80)
        )
        panel.children.append(sep)

        # Item list
        self.item_labels[category] = []
        for j, (item_name, module) in enumerate(items):
            item_y = header_height + j * item_height + 5
            item_label = mcrfpy.Caption(
                text=item_name,
                pos=(15, item_y),
                font_size=13,
                fill_color=mcrfpy.Color(150, 150, 150) if module else mcrfpy.Color(80, 80, 80)
            )
            panel.children.append(item_label)
            self.item_labels[category].append((item_label, module is not None))

    def _update_selection(self):
        """Update the visual selection state."""
        # Update all items
        for cat_idx, category in enumerate(self.categories):
            # Update panel outline
            panel = self.category_frames[cat_idx]
            if cat_idx == self.selected_category:
                panel.outline_color = mcrfpy.Color(100, 150, 255)
                panel.outline = 3
            else:
                panel.outline_color = mcrfpy.Color(60, 60, 80)
                panel.outline = 2

            # Update item colors
            for item_idx, (label, available) in enumerate(self.item_labels[category]):
                if cat_idx == self.selected_category and item_idx == self.selected_item:
                    if available:
                        label.fill_color = mcrfpy.Color(100, 200, 255)
                    else:
                        label.fill_color = mcrfpy.Color(100, 100, 120)
                else:
                    if available:
                        label.fill_color = mcrfpy.Color(180, 180, 180)
                    else:
                        label.fill_color = mcrfpy.Color(80, 80, 80)

    def _run_selected_demo(self):
        """Run the currently selected demo."""
        category = self.categories[self.selected_category]
        items = self.DEMOS[category]

        if self.selected_item < len(items):
            name, module = items[self.selected_item]
            if module:
                try:
                    # Import and run the demo module
                    exec(f"from {module} import main; main()")
                except Exception as e:
                    print(f"Error running demo: {e}")
                    import traceback
                    traceback.print_exc()

    def on_key(self, key, state):
        """Handle keyboard input."""
        if state != "start":
            return

        category = self.categories[self.selected_category]
        items = self.DEMOS[category]

        if key == "Escape":
            sys.exit(0)
        elif key == "Left":
            self.selected_category = (self.selected_category - 1) % len(self.categories)
            # Clamp item selection to new category
            new_category = self.categories[self.selected_category]
            self.selected_item = min(self.selected_item, len(self.DEMOS[new_category]) - 1)
            self._update_selection()
        elif key == "Right":
            self.selected_category = (self.selected_category + 1) % len(self.categories)
            new_category = self.categories[self.selected_category]
            self.selected_item = min(self.selected_item, len(self.DEMOS[new_category]) - 1)
            self._update_selection()
        elif key == "Up":
            self.selected_item = (self.selected_item - 1) % len(items)
            self._update_selection()
        elif key == "Down":
            self.selected_item = (self.selected_item + 1) % len(items)
            self._update_selection()
        elif key == "Enter":
            self._run_selected_demo()

    def activate(self):
        """Activate the launcher scene."""
        self.scene.on_key = self.on_key
        mcrfpy.current_scene = self.scene


def main():
    """Launch the cookbook."""
    launcher = CookbookLauncher()
    launcher.activate()


if __name__ == "__main__":
    main()
