#!/usr/bin/env python3
"""Capture screenshots for all primitive widget demos.

Run with:
    cd build && ./mcrogueface --headless --exec ../tests/cookbook/automation/capture_primitives.py
"""
import mcrfpy
from mcrfpy import automation
import sys
import os

# Add cookbook to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# List of demos to capture with their setup functions
DEMOS = [
    ("button", "demo_button"),
    ("stat_bar", "demo_stat_bar"),
    ("choice_list", "demo_choice_list"),
    ("text_box", "demo_text_box"),
    ("toast", "demo_toast"),
]

# Screenshot output directory (relative to build/)
OUTPUT_DIR = "../tests/cookbook/screenshots/primitives"


class ScreenshotCapture:
    """Captures screenshots for all primitive demos."""

    def __init__(self):
        self.current_demo = 0
        self.demos = []

    def load_demos(self):
        """Load all demo modules."""
        for name, module_name in DEMOS:
            try:
                module = __import__(f"primitives.{module_name}", fromlist=[module_name])
                self.demos.append((name, module))
                print(f"Loaded: {name}")
            except Exception as e:
                print(f"Failed to load {name}: {e}")

    def capture_next(self, runtime=None):
        """Capture the next demo screenshot."""
        if self.current_demo >= len(self.demos):
            print(f"\nDone! Captured {self.current_demo} screenshots.")
            sys.exit(0)
            return

        name, module = self.demos[self.current_demo]
        print(f"Capturing: {name}...")

        try:
            # Create demo instance
            demo_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and attr_name.endswith('Demo'):
                    demo_class = attr
                    break

            if demo_class:
                demo = demo_class()
                demo.activate()

                # Schedule screenshot after render
                def take_screenshot(rt):
                    filename = f"{OUTPUT_DIR}/{name}.png"
                    try:
                        automation.screenshot(filename)
                        print(f"  Saved: {filename}")
                    except Exception as e:
                        print(f"  Error saving: {e}")

                    self.current_demo += 1
                    self.capture_next()

                mcrfpy.Timer(f"capture_{name}", take_screenshot, 100)
            else:
                print(f"  No Demo class found in {name}")
                self.current_demo += 1
                self.capture_next()

        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            self.current_demo += 1
            self.capture_next()

    def start(self):
        """Start the capture process."""
        print("=" * 50)
        print("Cookbook Primitive Screenshot Capture")
        print("=" * 50)

        # Ensure output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        self.load_demos()
        print(f"\nCapturing {len(self.demos)} demos...")
        print("-" * 50)

        # Start capture process
        self.capture_next()


def main():
    capture = ScreenshotCapture()
    capture.start()


if __name__ == "__main__":
    main()
