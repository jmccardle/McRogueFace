#!/usr/bin/env python3
"""Calculator App - Boss-key calculator with scene switching

Interactive controls:
    0-9: Number input
    +, -, *, /: Operations
    Enter/=: Calculate result
    C: Clear
    ESC: Toggle between game and calculator scenes
    Backspace: Delete last digit

This demonstrates:
    - Scene switching (boss key pattern)
    - Button grid layout
    - State management
    - Click handlers
"""
import mcrfpy
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.button import Button


class Calculator:
    """A simple calculator with GUI."""

    def __init__(self):
        self.scene = mcrfpy.Scene("calculator")
        self.ui = self.scene.children
        self.expression = ""
        self.result = ""
        self.setup()

    def setup(self):
        """Build the calculator UI."""
        # Background
        bg = mcrfpy.Frame(
            pos=(0, 0),
            size=(1024, 768),
            fill_color=mcrfpy.Color(30, 30, 35)
        )
        self.ui.append(bg)

        # Calculator frame
        calc_frame = mcrfpy.Frame(
            pos=(312, 100),
            size=(400, 550),
            fill_color=mcrfpy.Color(40, 40, 50),
            outline_color=mcrfpy.Color(80, 80, 100),
            outline=2
        )
        self.ui.append(calc_frame)

        # Title
        title = mcrfpy.Caption(
            text="Calculator",
            pos=(512, 130),
            font_size=24,
            fill_color=mcrfpy.Color(200, 200, 200)
        )
        self.ui.append(title)

        # Display frame
        display_bg = mcrfpy.Frame(
            pos=(332, 170),
            size=(360, 80),
            fill_color=mcrfpy.Color(20, 25, 30),
            outline_color=mcrfpy.Color(60, 60, 80),
            outline=1
        )
        self.ui.append(display_bg)

        # Expression display
        self.expr_display = mcrfpy.Caption(
            text="",
            pos=(682, 180),  # Right-aligned
            font_size=18,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(self.expr_display)

        # Result display
        self.result_display = mcrfpy.Caption(
            text="0",
            pos=(682, 210),  # Right-aligned
            font_size=32,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        self.ui.append(self.result_display)

        # Button layout
        button_layout = [
            ["C", "(", ")", "/"],
            ["7", "8", "9", "*"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "+"],
            ["0", ".", "DEL", "="],
        ]

        start_x = 342
        start_y = 270
        btn_width = 80
        btn_height = 50
        spacing = 8

        for row_idx, row in enumerate(button_layout):
            for col_idx, label in enumerate(row):
                x = start_x + col_idx * (btn_width + spacing)
                y = start_y + row_idx * (btn_height + spacing)

                # Different colors for different button types
                if label in "0123456789.":
                    fill = mcrfpy.Color(60, 60, 70)
                    hover = mcrfpy.Color(80, 80, 95)
                elif label == "=":
                    fill = mcrfpy.Color(80, 120, 80)
                    hover = mcrfpy.Color(100, 150, 100)
                elif label == "C":
                    fill = mcrfpy.Color(120, 60, 60)
                    hover = mcrfpy.Color(150, 80, 80)
                else:
                    fill = mcrfpy.Color(70, 70, 90)
                    hover = mcrfpy.Color(90, 90, 115)

                btn = Button(
                    label,
                    pos=(x, y),
                    size=(btn_width, btn_height),
                    fill_color=fill,
                    hover_color=hover,
                    callback=lambda l=label: self.on_button(l),
                    font_size=20
                )
                self.ui.append(btn.frame)

        # Instructions
        instr = mcrfpy.Caption(
            text="Press ESC to switch to game | Click buttons or use keyboard",
            pos=(512, 580),
            font_size=14,
            fill_color=mcrfpy.Color(100, 100, 100)
        )
        self.ui.append(instr)

    def on_button(self, label):
        """Handle button press."""
        if label == "C":
            self.expression = ""
            self.result = "0"
        elif label == "DEL":
            self.expression = self.expression[:-1]
        elif label == "=":
            self.calculate()
        else:
            self.expression += label

        self._update_display()

    def calculate(self):
        """Evaluate the expression."""
        if not self.expression:
            return

        try:
            # Safe evaluation (only math operations)
            allowed = set("0123456789+-*/.()")
            if all(c in allowed for c in self.expression):
                self.result = str(eval(self.expression))
                if self.result.endswith('.0'):
                    self.result = self.result[:-2]
            else:
                self.result = "Error"
        except Exception:
            self.result = "Error"

    def _update_display(self):
        """Update the display captions."""
        self.expr_display.text = self.expression or ""
        self.result_display.text = self.result or "0"

    def on_key(self, key, state):
        """Handle keyboard input."""
        if state != "start":
            return

        if key == "Escape":
            # Switch to game scene
            mcrfpy.current_scene = game_scene
            return

        # Map keys to buttons
        key_map = {
            "Num0": "0", "Num1": "1", "Num2": "2", "Num3": "3",
            "Num4": "4", "Num5": "5", "Num6": "6", "Num7": "7",
            "Num8": "8", "Num9": "9",
            "Period": ".", "Add": "+", "Subtract": "-",
            "Multiply": "*", "Divide": "/",
            "Enter": "=", "Return": "=",
            "C": "C", "Backspace": "DEL",
            "LParen": "(", "RParen": ")",
        }

        if key in key_map:
            self.on_button(key_map[key])

    def activate(self):
        """Activate the calculator scene."""
        self.scene.on_key = self.on_key
        mcrfpy.current_scene = self.scene


class GamePlaceholder:
    """Placeholder game scene to switch to/from."""

    def __init__(self):
        self.scene = mcrfpy.Scene("game_placeholder")
        self.ui = self.scene.children
        self.setup()

    def setup(self):
        """Build the game placeholder UI."""
        # Background
        bg = mcrfpy.Frame(
            pos=(0, 0),
            size=(1024, 768),
            fill_color=mcrfpy.Color(20, 40, 20)
        )
        self.ui.append(bg)

        # Title
        title = mcrfpy.Caption(
            text="GAME SCENE",
            pos=(512, 350),
            font_size=48,
            fill_color=mcrfpy.Color(100, 200, 100)
        )
        title.outline = 3
        title.outline_color = mcrfpy.Color(0, 0, 0)
        self.ui.append(title)

        # Subtitle
        subtitle = mcrfpy.Caption(
            text="Press ESC for Calculator (Boss Key!)",
            pos=(512, 420),
            font_size=20,
            fill_color=mcrfpy.Color(150, 200, 150)
        )
        self.ui.append(subtitle)

        # Fake game elements
        for i in range(5):
            fake_element = mcrfpy.Frame(
                pos=(100 + i * 180, 550),
                size=(150, 100),
                fill_color=mcrfpy.Color(40 + i * 10, 60 + i * 5, 40),
                outline_color=mcrfpy.Color(80, 120, 80),
                outline=1
            )
            self.ui.append(fake_element)

            label = mcrfpy.Caption(
                text=f"Game Element {i+1}",
                pos=(175 + i * 180, 590),
                font_size=12,
                fill_color=mcrfpy.Color(200, 200, 200)
            )
            self.ui.append(label)

    def on_key(self, key, state):
        """Handle keyboard input."""
        if state != "start":
            return

        if key == "Escape":
            # Switch to calculator
            calculator.activate()

    def activate(self):
        """Activate the game scene."""
        self.scene.on_key = self.on_key
        mcrfpy.current_scene = self.scene


# Global instances
calculator = None
game_scene = None


def main():
    """Run the calculator app."""
    global calculator, game_scene

    calculator = Calculator()
    game_scene = GamePlaceholder()

    # Start with the game scene
    game_scene.activate()

    # Headless mode: capture screenshot and exit
    try:
        if mcrfpy.headless_mode():
            from mcrfpy import automation
            # Show calculator for screenshot
            calculator.activate()
            calculator.expression = "7+8"
            calculator._update_display()

            mcrfpy.Timer("screenshot", lambda rt: (
                automation.screenshot("screenshots/apps/calculator.png"),
                sys.exit(0)
            ), 100)
    except AttributeError:
        pass


if __name__ == "__main__":
    main()
