"""Interactive Procedural Generation Demo Launcher

Run with: ./mcrogueface ../tests/procgen_interactive/main.py
"""

import mcrfpy
import sys

# Demo classes
from .demos.cave_demo import CaveDemo
from .demos.dungeon_demo import DungeonDemo
from .demos.terrain_demo import TerrainDemo
from .demos.town_demo import TownDemo


class DemoLauncher:
    """Main menu for selecting demos."""

    DEMOS = [
        ("Cave (Cellular Automata)", CaveDemo,
         "Cellular automata cave generation with noise, smoothing, and region detection"),
        ("Dungeon (BSP)", DungeonDemo,
         "Binary Space Partitioning with room extraction and corridor connections"),
        ("Terrain (Multi-layer)", TerrainDemo,
         "FBM noise elevation with water level, mountains, erosion, and biomes"),
        ("Town (Voronoi)", TownDemo,
         "Voronoi districts with Bezier roads and building placement"),
    ]

    def __init__(self):
        """Build the menu scene."""
        self.scene = mcrfpy.Scene("procgen_menu")
        self.current_demo = None
        self._build_menu()

    def _build_menu(self):
        """Create the menu UI."""
        ui = self.scene.children

        # Background
        bg = mcrfpy.Frame(
            pos=(0, 0),
            size=(1024, 768),
            fill_color=mcrfpy.Color(25, 28, 35)
        )
        ui.append(bg)

        # Title
        title = mcrfpy.Caption(
            text="Interactive Procedural Generation",
            pos=(512, 60),
            font_size=32,
            fill_color=mcrfpy.Color(220, 220, 230)
        )
        ui.append(title)

        subtitle = mcrfpy.Caption(
            text="Educational demos for exploring generation techniques",
            pos=(512, 100),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 160)
        )
        ui.append(subtitle)

        # Demo buttons
        button_y = 180
        button_width = 400
        button_height = 80

        for i, (name, demo_class, description) in enumerate(self.DEMOS):
            # Button frame
            btn = mcrfpy.Frame(
                pos=(312, button_y),
                size=(button_width, button_height),
                fill_color=mcrfpy.Color(45, 48, 55),
                outline=2,
                outline_color=mcrfpy.Color(80, 85, 100)
            )

            # Demo name
            name_caption = mcrfpy.Caption(
                text=name,
                pos=(20, 15),
                font_size=20,
                fill_color=mcrfpy.Color(200, 200, 210)
            )
            btn.children.append(name_caption)

            # Description (wrap manually for now)
            desc_text = description[:55] + "..." if len(description) > 55 else description
            desc_caption = mcrfpy.Caption(
                text=desc_text,
                pos=(20, 45),
                font_size=12,
                fill_color=mcrfpy.Color(120, 120, 130)
            )
            btn.children.append(desc_caption)

            # Click handler
            demo_idx = i
            btn.on_click = lambda p, b, a, idx=demo_idx: self._on_demo_click(idx, b, a)
            btn.on_enter = lambda p, btn=btn: self._on_btn_enter(btn)
            btn.on_exit = lambda p, btn=btn: self._on_btn_exit(btn)

            ui.append(btn)
            button_y += button_height + 20

        # Instructions
        instructions = [
            "Click a demo to start exploring procedural generation",
            "Each demo shows step-by-step visualization of the algorithm",
            "",
            "Controls (in demos):",
            "  Left/Right arrows: Navigate steps",
            "  Middle-drag: Pan viewport",
            "  Scroll wheel: Zoom in/out",
            "  Number keys: Toggle layer visibility",
            "  R: Reset view",
            "  Escape: Return to this menu",
        ]

        instr_y = 580
        for line in instructions:
            cap = mcrfpy.Caption(
                text=line,
                pos=(312, instr_y),
                font_size=12,
                fill_color=mcrfpy.Color(100, 100, 110)
            )
            ui.append(cap)
            instr_y += 18

        # Keyboard handler
        self.scene.on_key = self._on_key

    def _on_btn_enter(self, btn):
        """Handle button hover enter."""
        btn.fill_color = mcrfpy.Color(55, 60, 70)
        btn.outline_color = mcrfpy.Color(100, 120, 180)

    def _on_btn_exit(self, btn):
        """Handle button hover exit."""
        btn.fill_color = mcrfpy.Color(45, 48, 55)
        btn.outline_color = mcrfpy.Color(80, 85, 100)

    def _on_demo_click(self, idx, button, action):
        """Handle demo button click."""
        if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.RELEASED:
            self._launch_demo(idx)

    def _launch_demo(self, idx):
        """Launch a demo by index."""
        _, demo_class, _ = self.DEMOS[idx]
        self.current_demo = demo_class()
        self.current_demo.activate()

    def _on_key(self, key, action):
        """Handle keyboard input."""
        # Only process on key press
        if action != mcrfpy.InputState.PRESSED:
            return

        # Convert key to string for easier comparison
        key_str = str(key) if not isinstance(key, str) else key

        # Number keys to launch demos directly
        if key_str.startswith("Key.NUM") or (len(key_str) == 1 and key_str.isdigit()):
            try:
                num = int(key_str[-1])
                if 1 <= num <= len(self.DEMOS):
                    self._launch_demo(num - 1)
            except (ValueError, IndexError):
                pass
        elif key == mcrfpy.Key.ESCAPE:
            sys.exit(0)

    def show(self):
        """Show the menu."""
        mcrfpy.current_scene = self.scene


# Global launcher instance
_launcher = None


def show_menu():
    """Show the demo menu (called from demos to return)."""
    global _launcher
    if _launcher is None:
        _launcher = DemoLauncher()
    _launcher.show()


def main():
    """Entry point for the demo system."""
    show_menu()


if __name__ == "__main__":
    main()
