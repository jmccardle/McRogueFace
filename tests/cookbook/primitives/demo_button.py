#!/usr/bin/env python3
"""Button Widget Demo - Clickable buttons with hover/press states

Interactive controls:
    Click: Interact with buttons
    1-4: Trigger button actions via keyboard
    D: Toggle button 4 enabled/disabled
    ESC: Exit demo
"""
import mcrfpy
import sys

# Add parent to path for imports
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.button import Button, create_button_row, create_button_column


class ButtonDemo:
    def __init__(self):
        self.scene = mcrfpy.Scene("button_demo")
        self.ui = self.scene.children
        self.click_count = 0
        self.buttons = []
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
            text="Button Widget Demo",
            pos=(512, 30),
            font_size=28,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        title.outline = 2
        title.outline_color = mcrfpy.Color(0, 0, 0)
        self.ui.append(title)

        # Click counter display
        self.counter_caption = mcrfpy.Caption(
            text="Clicks: 0",
            pos=(512, 70),
            font_size=18,
            fill_color=mcrfpy.Color(200, 200, 100)
        )
        self.ui.append(self.counter_caption)

        # Section 1: Basic buttons with different styles
        section1_label = mcrfpy.Caption(
            text="Basic Buttons (click or press 1-4)",
            pos=(100, 130),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section1_label)

        # Default button
        btn1 = Button(
            "Default",
            pos=(100, 160),
            callback=lambda: self.on_button_click("Default")
        )
        self.buttons.append(btn1)
        self.ui.append(btn1.frame)

        # Custom color button
        btn2 = Button(
            "Custom",
            pos=(240, 160),
            fill_color=mcrfpy.Color(80, 50, 100),
            hover_color=mcrfpy.Color(100, 70, 130),
            press_color=mcrfpy.Color(120, 90, 150),
            callback=lambda: self.on_button_click("Custom")
        )
        self.buttons.append(btn2)
        self.ui.append(btn2.frame)

        # Success-style button
        btn3 = Button(
            "Success",
            pos=(380, 160),
            fill_color=mcrfpy.Color(40, 120, 60),
            hover_color=mcrfpy.Color(50, 150, 75),
            press_color=mcrfpy.Color(60, 180, 90),
            outline_color=mcrfpy.Color(100, 200, 120),
            callback=lambda: self.on_button_click("Success")
        )
        self.buttons.append(btn3)
        self.ui.append(btn3.frame)

        # Danger-style button (toggleable)
        self.btn4 = Button(
            "Danger",
            pos=(520, 160),
            fill_color=mcrfpy.Color(150, 50, 50),
            hover_color=mcrfpy.Color(180, 70, 70),
            press_color=mcrfpy.Color(200, 90, 90),
            outline_color=mcrfpy.Color(200, 100, 100),
            callback=lambda: self.on_button_click("Danger")
        )
        self.buttons.append(self.btn4)
        self.ui.append(self.btn4.frame)

        # Section 2: Different sizes
        section2_label = mcrfpy.Caption(
            text="Button Sizes",
            pos=(100, 240),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section2_label)

        # Small button
        small = Button(
            "Small",
            pos=(100, 270),
            size=(80, 30),
            font_size=12,
            callback=lambda: self.on_button_click("Small")
        )
        self.ui.append(small.frame)

        # Medium button (default size)
        medium = Button(
            "Medium",
            pos=(200, 270),
            callback=lambda: self.on_button_click("Medium")
        )
        self.ui.append(medium.frame)

        # Large button
        large = Button(
            "Large Button",
            pos=(340, 270),
            size=(180, 50),
            font_size=20,
            callback=lambda: self.on_button_click("Large")
        )
        self.ui.append(large.frame)

        # Section 3: Button row
        section3_label = mcrfpy.Caption(
            text="Button Row (auto-layout)",
            pos=(100, 360),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section3_label)

        row_buttons = create_button_row(
            labels=["File", "Edit", "View", "Help"],
            start_pos=(100, 390),
            spacing=5,
            size=(80, 35),
            callbacks=[
                lambda: self.on_button_click("File"),
                lambda: self.on_button_click("Edit"),
                lambda: self.on_button_click("View"),
                lambda: self.on_button_click("Help"),
            ]
        )
        for btn in row_buttons:
            self.ui.append(btn.frame)

        # Section 4: Button column
        section4_label = mcrfpy.Caption(
            text="Button Column",
            pos=(600, 240),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section4_label)

        col_buttons = create_button_column(
            labels=["New Game", "Load Game", "Options", "Quit"],
            start_pos=(600, 270),
            spacing=5,
            size=(150, 35),
            callbacks=[
                lambda: self.on_button_click("New Game"),
                lambda: self.on_button_click("Load Game"),
                lambda: self.on_button_click("Options"),
                lambda: self.on_button_click("Quit"),
            ]
        )
        for btn in col_buttons:
            self.ui.append(btn.frame)

        # Section 5: Disabled state
        section5_label = mcrfpy.Caption(
            text="Disabled State (press D to toggle)",
            pos=(100, 470),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section5_label)

        self.disabled_btn = Button(
            "Disabled",
            pos=(100, 500),
            enabled=False,
            callback=lambda: self.on_button_click("This shouldn't fire!")
        )
        self.ui.append(self.disabled_btn.frame)

        self.toggle_info = mcrfpy.Caption(
            text="Currently: Disabled",
            pos=(240, 510),
            font_size=14,
            fill_color=mcrfpy.Color(180, 100, 100)
        )
        self.ui.append(self.toggle_info)

        # Instructions
        instr = mcrfpy.Caption(
            text="Click buttons or press 1-4 | D: Toggle disabled | ESC: Exit",
            pos=(50, 730),
            font_size=14,
            fill_color=mcrfpy.Color(120, 120, 120)
        )
        self.ui.append(instr)

        # Last action display
        self.action_caption = mcrfpy.Caption(
            text="Last action: None",
            pos=(50, 600),
            font_size=16,
            fill_color=mcrfpy.Color(100, 200, 100)
        )
        self.ui.append(self.action_caption)

    def on_button_click(self, button_name):
        """Handle button click."""
        self.click_count += 1
        self.counter_caption.text = f"Clicks: {self.click_count}"
        self.action_caption.text = f"Last action: Clicked '{button_name}'"

    def on_key(self, key, state):
        """Handle keyboard input."""
        if state != "start":
            return

        if key == "Escape":
            sys.exit(0)
        elif key == "Num1" and len(self.buttons) > 0:
            self.buttons[0].callback()
        elif key == "Num2" and len(self.buttons) > 1:
            self.buttons[1].callback()
        elif key == "Num3" and len(self.buttons) > 2:
            self.buttons[2].callback()
        elif key == "Num4" and len(self.buttons) > 3:
            self.buttons[3].callback()
        elif key == "D":
            # Toggle disabled button
            self.disabled_btn.enabled = not self.disabled_btn.enabled
            if self.disabled_btn.enabled:
                self.toggle_info.text = "Currently: Enabled"
                self.toggle_info.fill_color = mcrfpy.Color(100, 180, 100)
            else:
                self.toggle_info.text = "Currently: Disabled"
                self.toggle_info.fill_color = mcrfpy.Color(180, 100, 100)

    def activate(self):
        """Activate the demo scene."""
        self.scene.on_key = self.on_key
        mcrfpy.current_scene = self.scene


def main():
    """Run the button demo."""
    demo = ButtonDemo()
    demo.activate()

    # Headless mode: capture screenshot and exit
    try:
        if mcrfpy.headless_mode():
            from mcrfpy import automation
            mcrfpy.Timer("screenshot", lambda rt: (
                automation.screenshot("screenshots/primitives/button_demo.png"),
                sys.exit(0)
            ), 100)
    except AttributeError:
        # headless_mode() may not exist in all versions
        pass


if __name__ == "__main__":
    main()
