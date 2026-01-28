#!/usr/bin/env python3
"""Capture all cookbook screenshots.

This script captures screenshots for all demos in the cookbook.
Run with:
    cd build && ./mcrogueface --headless --exec ../tests/cookbook/run_screenshots.py

Output goes to:
    tests/cookbook/screenshots/
        primitives/
        features/
        apps/
        compound/
"""
import mcrfpy
from mcrfpy import automation
import sys
import os

# Add cookbook to path
COOKBOOK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, COOKBOOK_DIR)

# Output directories
SCREENSHOT_BASE = os.path.join(COOKBOOK_DIR, "screenshots")


def ensure_dirs():
    """Create screenshot directories."""
    dirs = ["primitives", "features", "apps", "compound"]
    for d in dirs:
        os.makedirs(os.path.join(SCREENSHOT_BASE, d), exist_ok=True)


def capture_demo(module_path, output_name, category):
    """Capture a single demo screenshot.

    Args:
        module_path: Dotted module path (e.g., "primitives.demo_button")
        output_name: Output filename without extension
        category: Subdirectory (e.g., "primitives")

    Returns:
        True if successful, False otherwise
    """
    try:
        # Import the module
        parts = module_path.rsplit('.', 1)
        if len(parts) == 2:
            parent, name = parts
            module = __import__(module_path, fromlist=[name])
        else:
            module = __import__(module_path)

        # Find the Demo class
        demo_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and 'Demo' in attr_name:
                demo_class = attr
                break

        if not demo_class:
            print(f"  No Demo class in {module_path}")
            return False

        # Create and activate demo
        demo = demo_class()
        demo.activate()

        # Take screenshot
        output_path = os.path.join(SCREENSHOT_BASE, category, f"{output_name}.png")
        automation.screenshot(output_path)
        print(f"  OK: {output_path}")
        return True

    except Exception as e:
        print(f"  FAIL: {module_path} - {e}")
        return False


def main():
    """Main screenshot capture routine."""
    print("=" * 60)
    print("McRogueFace Cookbook - Screenshot Capture")
    print("=" * 60)

    ensure_dirs()

    # Define all demos to capture
    demos = [
        # Primitives
        ("primitives.demo_button", "button", "primitives"),
        ("primitives.demo_stat_bar", "stat_bar", "primitives"),
        ("primitives.demo_choice_list", "choice_list", "primitives"),
        ("primitives.demo_text_box", "text_box", "primitives"),
        ("primitives.demo_toast", "toast", "primitives"),
        ("primitives.demo_drag_drop_frame", "drag_drop_frame", "primitives"),
        ("primitives.demo_drag_drop_grid", "drag_drop_grid", "primitives"),
        ("primitives.demo_click_pickup", "click_pickup", "primitives"),

        # Features
        ("features.demo_animation_chain", "animation_chain", "features"),
        ("features.demo_shaders", "shaders", "features"),
        ("features.demo_rotation", "rotation", "features"),

        # Apps
        ("apps.calculator", "calculator", "apps"),
        ("apps.dialogue_system", "dialogue_system", "apps"),

        # Compound
        ("compound.shop_demo", "shop_demo", "compound"),
    ]

    success = 0
    failed = 0

    for module_path, output_name, category in demos:
        print(f"\nCapturing: {output_name}")
        if capture_demo(module_path, output_name, category):
            success += 1
        else:
            failed += 1

    print("\n" + "=" * 60)
    print(f"Complete! Success: {success}, Failed: {failed}")
    print(f"Screenshots saved to: {SCREENSHOT_BASE}")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    # Use a timer to ensure the scene system is ready
    mcrfpy.Timer("run_capture", lambda rt: main(), 50)
