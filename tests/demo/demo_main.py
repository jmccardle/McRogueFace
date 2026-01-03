#!/usr/bin/env python3
"""
McRogueFace Feature Demo System

Usage:
    Headless (screenshots): ./mcrogueface --headless --exec tests/demo/demo_main.py
    Interactive: ./mcrogueface tests/demo/demo_main.py

In headless mode, generates screenshots for each feature screen.
In interactive mode, provides a menu to navigate between screens.
"""
import mcrfpy
from mcrfpy import automation
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import screen modules
from demo.screens.caption_demo import CaptionDemo
from demo.screens.frame_demo import FrameDemo
from demo.screens.primitives_demo import PrimitivesDemo
from demo.screens.grid_demo import GridDemo
from demo.screens.animation_demo import AnimationDemo
from demo.screens.color_demo import ColorDemo

# All demo screens in order
DEMO_SCREENS = [
    CaptionDemo,
    FrameDemo,
    PrimitivesDemo,
    GridDemo,
    AnimationDemo,
    ColorDemo,
]

class DemoRunner:
    """Manages the demo system."""

    def __init__(self):
        self.screens = []
        self.current_index = 0
        self.headless = self._detect_headless()
        self.screenshot_dir = os.path.join(os.path.dirname(__file__), "screenshots")

    def _detect_headless(self):
        """Detect if running in headless mode."""
        # Check window resolution - headless mode has a default resolution
        try:
            win = mcrfpy.Window.get()
            # In headless mode, Window.get() still returns an object
            # Check if we're in headless by looking for the indicator
            return str(win).find("headless") >= 0
        except:
            return True

    def setup_all_screens(self):
        """Initialize all demo screens."""
        for i, ScreenClass in enumerate(DEMO_SCREENS):
            scene_name = f"demo_{i:02d}_{ScreenClass.name.lower().replace(' ', '_')}"
            screen = ScreenClass(scene_name)
            screen.setup()
            self.screens.append(screen)

    def create_menu(self):
        """Create the main menu screen."""
        menu = mcrfpy.Scene("menu")
        ui = menu.children

        # Title
        title = mcrfpy.Caption(text="McRogueFace Demo", pos=(400, 30))
        title.fill_color = mcrfpy.Color(255, 255, 255)
        title.outline = 2
        title.outline_color = mcrfpy.Color(0, 0, 0)
        ui.append(title)

        subtitle = mcrfpy.Caption(text="Feature Showcase", pos=(400, 70))
        subtitle.fill_color = mcrfpy.Color(180, 180, 180)
        ui.append(subtitle)

        # Menu items
        for i, screen in enumerate(self.screens):
            y = 130 + i * 50

            # Button frame
            btn = mcrfpy.Frame(pos=(250, y), size=(300, 40))
            btn.fill_color = mcrfpy.Color(50, 50, 70)
            btn.outline = 1
            btn.outline_color = mcrfpy.Color(100, 100, 150)
            ui.append(btn)

            # Button text
            label = mcrfpy.Caption(text=f"{i+1}. {screen.name}", pos=(20, 8))
            label.fill_color = mcrfpy.Color(200, 200, 255)
            btn.children.append(label)

            # Store index for click handler
            btn.name = f"menu_{i}"

        # Instructions
        instr = mcrfpy.Caption(text="Press 1-6 to view demos, ESC to return to menu", pos=(200, 500))
        instr.fill_color = mcrfpy.Color(150, 150, 150)
        ui.append(instr)

    def run_headless(self):
        """Run in headless mode - generate all screenshots."""
        print(f"Generating {len(self.screens)} demo screenshots...")

        # Ensure screenshot directory exists
        os.makedirs(self.screenshot_dir, exist_ok=True)

        # Use timer to take screenshots after game loop renders each scene
        self.current_index = 0
        self.render_wait = 0

        def screenshot_cycle(runtime):
            if self.render_wait == 0:
                # Set scene and wait for render
                if self.current_index >= len(self.screens):
                    print("Done!")
                    sys.exit(0)
                    return
                screen = self.screens[self.current_index]
                mcrfpy.current_scene = screen
                self.render_wait = 1
            elif self.render_wait < 2:
                # Wait additional frame
                self.render_wait += 1
            else:
                # Take screenshot
                screen = self.screens[self.current_index]
                filename = os.path.join(self.screenshot_dir, screen.get_screenshot_name())
                automation.screenshot(filename)
                print(f"  [{self.current_index+1}/{len(self.screens)}] {filename}")
                self.current_index += 1
                self.render_wait = 0
                if self.current_index >= len(self.screens):
                    print("Done!")
                    sys.exit(0)

        mcrfpy.setTimer("screenshot", screenshot_cycle, 50)

    def run_interactive(self):
        """Run in interactive mode with menu."""
        self.create_menu()

        def handle_key(key, state):
            if state != "start":
                return

            # Number keys 1-9 for direct screen access
            if key in [f"Num{n}" for n in "123456789"]:
                idx = int(key[-1]) - 1
                if idx < len(self.screens):
                    mcrfpy.setScene(self.screens[idx].scene_name)

            # ESC returns to menu
            elif key == "Escape":
                menu.activate()

            # Q quits
            elif key == "Q":
                sys.exit(0)

        # Register keyboard handler on menu scene
        menu.activate()
        menu.on_key = handle_key

        # Also register keyboard handler on all demo scenes
        for screen in self.screens:
            mcrfpy.current_scene = screen
            menu.on_key = handle_key

        # Start on menu
        menu.activate()

def main():
    """Main entry point."""
    runner = DemoRunner()
    runner.setup_all_screens()

    if runner.headless:
        runner.run_headless()
    else:
        runner.run_interactive()

# Run when executed
main()
