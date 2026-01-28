#!/usr/bin/env python3
"""Choice List Widget Demo - Vertical selectable list with keyboard/mouse navigation

Interactive controls:
    Up/Down: Navigate choices
    Enter: Confirm selection
    Click: Select item
    A: Add a new choice
    R: Remove selected choice
    ESC: Exit demo
"""
import mcrfpy
import sys

# Add parent to path for imports
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.choice_list import ChoiceList, create_menu


class ChoiceListDemo:
    def __init__(self):
        self.scene = mcrfpy.Scene("choice_list_demo")
        self.ui = self.scene.children
        self.lists = []
        self.active_list_idx = 0
        self.add_counter = 0
        self.setup()

    def setup(self):
        """Build the demo scene."""
        # Background
        bg = mcrfpy.Frame(
            pos=(0, 0),
            size=(1024, 768),
            fill_color=mcrfpy.Color(20, 20, 25)
        )
        self.ui.append(bg)

        # Title
        title = mcrfpy.Caption(
            text="Choice List Widget Demo",
            pos=(512, 30),
            font_size=28,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        title.outline = 2
        title.outline_color = mcrfpy.Color(0, 0, 0)
        self.ui.append(title)

        # Section 1: Basic choice list
        section1_label = mcrfpy.Caption(
            text="Main Menu (keyboard or click)",
            pos=(50, 90),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section1_label)

        self.main_list = ChoiceList(
            pos=(50, 120),
            size=(200, 150),
            choices=["New Game", "Continue", "Options", "Credits", "Quit"],
            on_select=self.on_main_select
        )
        self.lists.append(self.main_list)
        self.ui.append(self.main_list.frame)

        # Selection indicator
        self.main_selection = mcrfpy.Caption(
            text="Selected: New Game",
            pos=(50, 280),
            font_size=14,
            fill_color=mcrfpy.Color(100, 200, 100)
        )
        self.ui.append(self.main_selection)

        # Section 2: Custom styled list
        section2_label = mcrfpy.Caption(
            text="Difficulty Selection",
            pos=(300, 90),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section2_label)

        self.diff_list = ChoiceList(
            pos=(300, 120),
            size=(180, 120),
            choices=["Easy", "Normal", "Hard", "Nightmare"],
            on_select=self.on_diff_select,
            selected_color=mcrfpy.Color(120, 60, 60),
            hover_color=mcrfpy.Color(80, 40, 40),
            normal_color=mcrfpy.Color(50, 30, 30)
        )
        self.lists.append(self.diff_list)
        self.ui.append(self.diff_list.frame)

        self.diff_selection = mcrfpy.Caption(
            text="Difficulty: Easy",
            pos=(300, 250),
            font_size=14,
            fill_color=mcrfpy.Color(200, 100, 100)
        )
        self.ui.append(self.diff_selection)

        # Section 3: Dynamic list (add/remove items)
        section3_label = mcrfpy.Caption(
            text="Dynamic List (A: Add, R: Remove)",
            pos=(530, 90),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section3_label)

        self.dynamic_list = ChoiceList(
            pos=(530, 120),
            size=(200, 180),
            choices=["Item 1", "Item 2", "Item 3"],
            on_select=self.on_dynamic_select
        )
        self.lists.append(self.dynamic_list)
        self.ui.append(self.dynamic_list.frame)

        self.dynamic_info = mcrfpy.Caption(
            text="Items: 3",
            pos=(530, 310),
            font_size=14,
            fill_color=mcrfpy.Color(100, 150, 200)
        )
        self.ui.append(self.dynamic_info)

        # Section 4: Menu with title (using helper)
        section4_label = mcrfpy.Caption(
            text="Menu with Title (helper function)",
            pos=(780, 90),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section4_label)

        menu_container, self.titled_list = create_menu(
            pos=(780, 120),
            choices=["Attack", "Defend", "Magic", "Item", "Flee"],
            on_select=self.on_combat_select,
            title="Combat",
            width=180
        )
        self.lists.append(self.titled_list)
        self.ui.append(menu_container)

        self.combat_selection = mcrfpy.Caption(
            text="Action: Attack",
            pos=(780, 340),
            font_size=14,
            fill_color=mcrfpy.Color(200, 200, 100)
        )
        self.ui.append(self.combat_selection)

        # Section 5: Long list (scrolling needed in future)
        section5_label = mcrfpy.Caption(
            text="Long List",
            pos=(50, 350),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section5_label)

        long_choices = [f"Option {i+1}" for i in range(10)]
        self.long_list = ChoiceList(
            pos=(50, 380),
            size=(200, 300),
            choices=long_choices,
            on_select=self.on_long_select,
            item_height=28
        )
        self.lists.append(self.long_list)
        self.ui.append(self.long_list.frame)

        self.long_selection = mcrfpy.Caption(
            text="Long list: Option 1",
            pos=(50, 690),
            font_size=14,
            fill_color=mcrfpy.Color(150, 150, 200)
        )
        self.ui.append(self.long_selection)

        # Active list indicator
        self.active_indicator = mcrfpy.Caption(
            text="Active list: Main Menu (Tab to switch)",
            pos=(300, 400),
            font_size=14,
            fill_color=mcrfpy.Color(200, 200, 200)
        )
        self.ui.append(self.active_indicator)

        # Instructions
        instr = mcrfpy.Caption(
            text="Up/Down: Navigate | Enter: Confirm | Tab: Switch list | A: Add | R: Remove | ESC: Exit",
            pos=(50, 730),
            font_size=14,
            fill_color=mcrfpy.Color(120, 120, 120)
        )
        self.ui.append(instr)

    def on_main_select(self, index, value):
        """Handle main menu selection."""
        self.main_selection.text = f"Selected: {value}"

    def on_diff_select(self, index, value):
        """Handle difficulty selection."""
        self.diff_selection.text = f"Difficulty: {value}"

    def on_dynamic_select(self, index, value):
        """Handle dynamic list selection."""
        self.dynamic_info.text = f"Selected: {value} (Items: {len(self.dynamic_list.choices)})"

    def on_combat_select(self, index, value):
        """Handle combat menu selection."""
        self.combat_selection.text = f"Action: {value}"

    def on_long_select(self, index, value):
        """Handle long list selection."""
        self.long_selection.text = f"Long list: {value}"

    def _update_active_indicator(self):
        """Update the active list indicator."""
        names = ["Main Menu", "Difficulty", "Dynamic", "Combat", "Long List"]
        if self.active_list_idx < len(names):
            self.active_indicator.text = f"Active list: {names[self.active_list_idx]} (Tab to switch)"

    def on_key(self, key, state):
        """Handle keyboard input."""
        if state != "start":
            return

        if key == "Escape":
            sys.exit(0)

        # Get active list
        active = self.lists[self.active_list_idx] if self.lists else None

        if key == "Up" and active:
            active.navigate(-1)
        elif key == "Down" and active:
            active.navigate(1)
        elif key == "Enter" and active:
            active.confirm()
        elif key == "Tab":
            # Switch active list
            self.active_list_idx = (self.active_list_idx + 1) % len(self.lists)
            self._update_active_indicator()
        elif key == "A":
            # Add item to dynamic list
            self.add_counter += 1
            self.dynamic_list.add_choice(f"New Item {self.add_counter}")
            self.dynamic_info.text = f"Items: {len(self.dynamic_list.choices)}"
        elif key == "R":
            # Remove selected from dynamic list
            if len(self.dynamic_list.choices) > 1:
                self.dynamic_list.remove_choice(self.dynamic_list.selected_index)
                self.dynamic_info.text = f"Items: {len(self.dynamic_list.choices)}"

    def activate(self):
        """Activate the demo scene."""
        self.scene.on_key = self.on_key
        mcrfpy.current_scene = self.scene


def main():
    """Run the choice list demo."""
    demo = ChoiceListDemo()
    demo.activate()

    # Headless mode: capture screenshot and exit
    try:
        if mcrfpy.headless_mode():
            from mcrfpy import automation
            mcrfpy.Timer("screenshot", lambda rt: (
                automation.screenshot("screenshots/primitives/choice_list_demo.png"),
                sys.exit(0)
            ), 100)
    except AttributeError:
        pass


if __name__ == "__main__":
    main()
