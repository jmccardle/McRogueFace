#!/usr/bin/env python3
"""
Geometry Module Demo System

Demonstrates the geometry module for Pinships orbital mechanics:
- Bresenham algorithms for grid-aligned circles and lines
- Angle calculations for pathfinding
- Static pathfinding through planetary orbits
- Animated solar system with discrete time steps
- Ship navigation anticipating planetary motion

Usage:
    Headless (screenshots): ./mcrogueface --headless --exec tests/geometry_demo/geometry_main.py
    Interactive: ./mcrogueface tests/geometry_demo/geometry_main.py
"""
import mcrfpy
from mcrfpy import automation
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'scripts'))

# Import screen modules
from geometry_demo.screens.bresenham_demo import BresenhamDemo
from geometry_demo.screens.angle_lines_demo import AngleLinesDemo
from geometry_demo.screens.pathfinding_static_demo import PathfindingStaticDemo
from geometry_demo.screens.solar_system_demo import SolarSystemDemo
from geometry_demo.screens.pathfinding_animated_demo import PathfindingAnimatedDemo

# All demo screens in order
DEMO_SCREENS = [
    BresenhamDemo,
    AngleLinesDemo,
    PathfindingStaticDemo,
    SolarSystemDemo,
    PathfindingAnimatedDemo,
]


class GeometryDemoRunner:
    """Manages the geometry demo system."""

    def __init__(self):
        self.screens = []
        self.current_index = 0
        self.headless = self._detect_headless()
        self.screenshot_dir = os.path.join(os.path.dirname(__file__), "screenshots")

    def _detect_headless(self):
        """Detect if running in headless mode."""
        try:
            win = mcrfpy.Window.get()
            return str(win).find("headless") >= 0
        except:
            return True

    def setup_all_screens(self):
        """Initialize all demo screens."""
        for i, ScreenClass in enumerate(DEMO_SCREENS):
            scene_name = f"geo_{i:02d}_{ScreenClass.name.lower().replace(' ', '_')}"
            screen = ScreenClass(scene_name)
            screen.setup()
            self.screens.append(screen)

    def create_menu(self):
        """Create the main menu screen."""
        geo_menu = mcrfpy.Scene("geo_menu")
        ui = geo_menu.children

        # Screen dimensions
        SCREEN_WIDTH = 1024
        SCREEN_HEIGHT = 768

        # Background
        bg = mcrfpy.Frame(pos=(0, 0), size=(SCREEN_WIDTH, SCREEN_HEIGHT))
        bg.fill_color = mcrfpy.Color(15, 15, 25)
        ui.append(bg)

        # Title
        title = mcrfpy.Caption(text="Geometry Module Demo", pos=(SCREEN_WIDTH // 2, 40))
        title.fill_color = mcrfpy.Color(255, 255, 255)
        title.outline = 2
        title.outline_color = mcrfpy.Color(0, 0, 0)
        ui.append(title)

        subtitle = mcrfpy.Caption(text="Pinships Orbital Mechanics", pos=(SCREEN_WIDTH // 2, 80))
        subtitle.fill_color = mcrfpy.Color(180, 180, 180)
        ui.append(subtitle)

        # Menu items - wider buttons centered on 1024 width
        btn_width = 500
        btn_x = (SCREEN_WIDTH - btn_width) // 2
        for i, screen in enumerate(self.screens):
            y = 140 + i * 70

            # Button frame
            btn = mcrfpy.Frame(pos=(btn_x, y), size=(btn_width, 60))
            btn.fill_color = mcrfpy.Color(30, 40, 60)
            btn.outline = 2
            btn.outline_color = mcrfpy.Color(80, 100, 150)
            ui.append(btn)

            # Button text
            label = mcrfpy.Caption(text=f"{i+1}. {screen.name}", pos=(20, 12))
            label.fill_color = mcrfpy.Color(200, 200, 255)
            btn.children.append(label)

            # Description
            desc = mcrfpy.Caption(text=screen.description, pos=(20, 35))
            desc.fill_color = mcrfpy.Color(120, 120, 150)
            btn.children.append(desc)

        # Instructions
        instr1 = mcrfpy.Caption(text="Press 1-5 to view demos", pos=(SCREEN_WIDTH // 2 - 100, 540))
        instr1.fill_color = mcrfpy.Color(150, 150, 150)
        ui.append(instr1)

        instr2 = mcrfpy.Caption(text="ESC = return to menu  |  Q = quit", pos=(SCREEN_WIDTH // 2 - 130, 580))
        instr2.fill_color = mcrfpy.Color(100, 100, 100)
        ui.append(instr2)

        # Credits
        credits = mcrfpy.Caption(text="Geometry module: src/scripts/geometry.py", pos=(SCREEN_WIDTH // 2 - 150, 700))
        credits.fill_color = mcrfpy.Color(80, 80, 100)
        ui.append(credits)

    def run_headless(self):
        """Run in headless mode - generate all screenshots."""
        print(f"Generating {len(self.screens)} geometry demo screenshots...")

        os.makedirs(self.screenshot_dir, exist_ok=True)

        self.current_index = 0
        self.render_wait = 0

        def screenshot_cycle(timer, runtime):
            if self.render_wait == 0:
                if self.current_index >= len(self.screens):
                    print("Done!")
                    sys.exit(0)
                    return
                screen = self.screens[self.current_index]
                mcrfpy.current_scene = screen
                self.render_wait = 1
            elif self.render_wait < 3:
                # Wait for animated demos to show initial state
                self.render_wait += 1
            else:
                screen = self.screens[self.current_index]
                filename = os.path.join(self.screenshot_dir, screen.get_screenshot_name())
                automation.screenshot(filename)
                print(f"  [{self.current_index+1}/{len(self.screens)}] {filename}")

                # Clean up timers for animated demos
                screen.cleanup()

                self.current_index += 1
                self.render_wait = 0
                if self.current_index >= len(self.screens):
                    print("Done!")
                    sys.exit(0)

        self.screenshot_timer = mcrfpy.Timer("screenshot", screenshot_cycle, 100)

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
                    # Clean up ALL screen's timers first
                    for screen in self.screens:
                        screen.cleanup()
                    # Switch to selected scene
                    mcrfpy.setScene(self.screens[idx].scene_name)
                    # Restart timers for the selected screen
                    self.screens[idx].restart_timers()

            # ESC returns to menu
            elif key == "Escape":
                for screen in self.screens:
                    screen.cleanup()
                geo_menu.activate()

            # Q quits
            elif key == "Q":
                sys.exit(0)

        # Register keyboard handler on all scenes
        geo_menu.activate()
        geo_menu.on_key = handle_key

        for screen in self.screens:
            mcrfpy.current_scene = screen
            geo_menu.on_key = handle_key

        geo_menu.activate()


def main():
    """Main entry point."""
    runner = GeometryDemoRunner()
    runner.setup_all_screens()

    if runner.headless:
        runner.run_headless()
    else:
        runner.run_interactive()


# Run when executed
main()
