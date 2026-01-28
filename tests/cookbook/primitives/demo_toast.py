#!/usr/bin/env python3
"""Toast Notification Demo - Auto-dismissing notification popups

Interactive controls:
    1: Show default toast
    2: Show success toast (green)
    3: Show error toast (red)
    4: Show warning toast (yellow)
    5: Show info toast (blue)
    S: Spam multiple toasts
    C: Clear all toasts
    ESC: Exit demo
"""
import mcrfpy
import sys

# Add parent to path for imports
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.toast import ToastManager


class ToastDemo:
    def __init__(self):
        self.scene = mcrfpy.Scene("toast_demo")
        self.ui = self.scene.children
        self.toast_count = 0
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
            text="Toast Notification Demo",
            pos=(512, 30),
            font_size=28,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        title.outline = 2
        title.outline_color = mcrfpy.Color(0, 0, 0)
        self.ui.append(title)

        # Create toast manager
        self.toasts = ToastManager(self.scene, position="top-right", max_toasts=5)

        # Instructions panel
        panel = mcrfpy.Frame(
            pos=(50, 100),
            size=(400, 400),
            fill_color=mcrfpy.Color(30, 30, 40),
            outline_color=mcrfpy.Color(60, 60, 80),
            outline=1
        )
        self.ui.append(panel)

        panel_title = mcrfpy.Caption(
            text="Toast Types",
            pos=(200, 15),
            font_size=18,
            fill_color=mcrfpy.Color(200, 200, 200)
        )
        panel.children.append(panel_title)

        # Type descriptions
        types = [
            ("1 - Default", "Standard notification", mcrfpy.Color(200, 200, 200)),
            ("2 - Success", "Confirmation messages", mcrfpy.Color(100, 200, 100)),
            ("3 - Error", "Error notifications", mcrfpy.Color(200, 100, 100)),
            ("4 - Warning", "Warning alerts", mcrfpy.Color(200, 180, 80)),
            ("5 - Info", "Informational messages", mcrfpy.Color(100, 150, 200)),
        ]

        for i, (key, desc, color) in enumerate(types):
            y = 50 + i * 50

            key_label = mcrfpy.Caption(
                text=key,
                pos=(20, y),
                font_size=16,
                fill_color=color
            )
            panel.children.append(key_label)

            desc_label = mcrfpy.Caption(
                text=desc,
                pos=(20, y + 20),
                font_size=12,
                fill_color=mcrfpy.Color(150, 150, 150)
            )
            panel.children.append(desc_label)

        # Additional controls
        controls = [
            ("S - Spam", "Show multiple toasts quickly"),
            ("C - Clear", "Dismiss all active toasts"),
        ]

        for i, (key, desc) in enumerate(controls):
            y = 300 + i * 40

            key_label = mcrfpy.Caption(
                text=key,
                pos=(20, y),
                font_size=14,
                fill_color=mcrfpy.Color(180, 180, 180)
            )
            panel.children.append(key_label)

            desc_label = mcrfpy.Caption(
                text=desc,
                pos=(20, y + 18),
                font_size=12,
                fill_color=mcrfpy.Color(120, 120, 120)
            )
            panel.children.append(desc_label)

        # Stats display
        self.stats_label = mcrfpy.Caption(
            text="Toasts shown: 0 | Active: 0",
            pos=(50, 520),
            font_size=14,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(self.stats_label)

        # Preview area
        preview_label = mcrfpy.Caption(
            text="Toasts appear in the top-right corner ->",
            pos=(500, 200),
            font_size=16,
            fill_color=mcrfpy.Color(100, 100, 100)
        )
        self.ui.append(preview_label)

        arrow = mcrfpy.Caption(
            text=">>>",
            pos=(750, 200),
            font_size=24,
            fill_color=mcrfpy.Color(100, 100, 100)
        )
        self.ui.append(arrow)

        # Instructions
        instr = mcrfpy.Caption(
            text="Press 1-5 to show different toast types | S: Spam | C: Clear all | ESC: Exit",
            pos=(50, 730),
            font_size=14,
            fill_color=mcrfpy.Color(120, 120, 120)
        )
        self.ui.append(instr)

    def update_stats(self):
        """Update the stats display."""
        active = len([t for t in self.toasts.toasts if not t.is_dismissed])
        self.stats_label.text = f"Toasts shown: {self.toast_count} | Active: {active}"

    def on_key(self, key, state):
        """Handle keyboard input."""
        if state != "start":
            return

        if key == "Escape":
            sys.exit(0)
        elif key == "Num1":
            self.toast_count += 1
            self.toasts.show(f"Default notification #{self.toast_count}")
            self.update_stats()
        elif key == "Num2":
            self.toast_count += 1
            self.toasts.show_success("Operation completed successfully!")
            self.update_stats()
        elif key == "Num3":
            self.toast_count += 1
            self.toasts.show_error("An error occurred!")
            self.update_stats()
        elif key == "Num4":
            self.toast_count += 1
            self.toasts.show_warning("Warning: Low health!")
            self.update_stats()
        elif key == "Num5":
            self.toast_count += 1
            self.toasts.show_info("New quest available")
            self.update_stats()
        elif key == "S":
            # Spam multiple toasts
            messages = [
                "Game saved!",
                "Achievement unlocked!",
                "New item acquired!",
                "Level up!",
                "Quest complete!",
            ]
            for msg in messages:
                self.toast_count += 1
                self.toasts.show(msg)
            self.update_stats()
        elif key == "C":
            self.toasts.dismiss_all()
            self.update_stats()

    def activate(self):
        """Activate the demo scene."""
        self.scene.on_key = self.on_key
        mcrfpy.current_scene = self.scene


def main():
    """Run the toast demo."""
    demo = ToastDemo()
    demo.activate()

    # Headless mode: show some toasts and screenshot
    try:
        if mcrfpy.headless_mode():
            from mcrfpy import automation
            # Show a few sample toasts
            demo.toasts.show("Game saved!")
            demo.toasts.show_success("Achievement unlocked!")
            demo.toasts.show_error("Connection lost!")

            mcrfpy.Timer("screenshot", lambda rt: (
                automation.screenshot("screenshots/primitives/toast_demo.png"),
                sys.exit(0)
            ), 500)
    except AttributeError:
        pass


if __name__ == "__main__":
    main()
