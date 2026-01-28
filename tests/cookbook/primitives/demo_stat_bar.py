#!/usr/bin/env python3
"""Stat Bar Widget Demo - Progress bars for health, mana, XP, etc.

Interactive controls:
    1-4: Decrease stat bars
    Shift+1-4: Increase stat bars
    F: Flash the health bar
    R: Reset all bars
    ESC: Exit demo
"""
import mcrfpy
import sys

# Add parent to path for imports
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.stat_bar import StatBar, create_stat_bar_group


class StatBarDemo:
    def __init__(self):
        self.scene = mcrfpy.Scene("stat_bar_demo")
        self.ui = self.scene.children
        self.bars = {}
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
            text="Stat Bar Widget Demo",
            pos=(512, 30),
            font_size=28,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        title.outline = 2
        title.outline_color = mcrfpy.Color(0, 0, 0)
        self.ui.append(title)

        # Section 1: Basic stat bars with labels
        section1_label = mcrfpy.Caption(
            text="Character Stats (press 1-4 to decrease, Shift+1-4 to increase)",
            pos=(50, 90),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section1_label)

        # Health bar
        self.bars['hp'] = StatBar(
            pos=(50, 120),
            size=(250, 25),
            current=75,
            maximum=100,
            fill_color=StatBar.HEALTH_COLOR,
            label="HP"
        )
        self.ui.append(self.bars['hp'].frame)

        # Mana bar
        self.bars['mp'] = StatBar(
            pos=(50, 155),
            size=(250, 25),
            current=50,
            maximum=80,
            fill_color=StatBar.MANA_COLOR,
            label="MP"
        )
        self.ui.append(self.bars['mp'].frame)

        # Stamina bar
        self.bars['stamina'] = StatBar(
            pos=(50, 190),
            size=(250, 25),
            current=90,
            maximum=100,
            fill_color=StatBar.STAMINA_COLOR,
            label="Stamina"
        )
        self.ui.append(self.bars['stamina'].frame)

        # XP bar
        self.bars['xp'] = StatBar(
            pos=(50, 225),
            size=(250, 25),
            current=250,
            maximum=1000,
            fill_color=StatBar.XP_COLOR,
            label="XP"
        )
        self.ui.append(self.bars['xp'].frame)

        # Section 2: Different sizes
        section2_label = mcrfpy.Caption(
            text="Different Sizes",
            pos=(50, 290),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section2_label)

        # Thin bar
        thin_bar = StatBar(
            pos=(50, 320),
            size=(200, 10),
            current=60,
            maximum=100,
            fill_color=mcrfpy.Color(100, 150, 200),
            show_text=False
        )
        self.ui.append(thin_bar.frame)

        thin_label = mcrfpy.Caption(
            text="Thin (no text)",
            pos=(260, 315),
            font_size=12,
            fill_color=mcrfpy.Color(120, 120, 120)
        )
        self.ui.append(thin_label)

        # Wide bar
        wide_bar = StatBar(
            pos=(50, 345),
            size=(400, 35),
            current=450,
            maximum=500,
            fill_color=StatBar.SHIELD_COLOR,
            label="Shield",
            font_size=16
        )
        self.ui.append(wide_bar.frame)

        # Section 3: Stat bar group
        section3_label = mcrfpy.Caption(
            text="Stat Bar Group (auto-layout)",
            pos=(500, 90),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section3_label)

        group = create_stat_bar_group([
            {"name": "Strength", "current": 15, "max": 20, "color": mcrfpy.Color(200, 80, 80)},
            {"name": "Dexterity", "current": 18, "max": 20, "color": mcrfpy.Color(80, 200, 80)},
            {"name": "Intelligence", "current": 12, "max": 20, "color": mcrfpy.Color(80, 80, 200)},
            {"name": "Wisdom", "current": 14, "max": 20, "color": mcrfpy.Color(200, 200, 80)},
            {"name": "Charisma", "current": 10, "max": 20, "color": mcrfpy.Color(200, 80, 200)},
        ], start_pos=(500, 120), spacing=10, size=(220, 22))

        for bar in group.values():
            self.ui.append(bar.frame)

        # Section 4: Edge cases
        section4_label = mcrfpy.Caption(
            text="Edge Cases",
            pos=(50, 420),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section4_label)

        # Empty bar
        empty_bar = StatBar(
            pos=(50, 450),
            size=(200, 20),
            current=0,
            maximum=100,
            fill_color=StatBar.HEALTH_COLOR,
            label="Empty"
        )
        self.ui.append(empty_bar.frame)

        # Full bar
        full_bar = StatBar(
            pos=(50, 480),
            size=(200, 20),
            current=100,
            maximum=100,
            fill_color=StatBar.STAMINA_COLOR,
            label="Full"
        )
        self.ui.append(full_bar.frame)

        # Overfill attempt (should clamp)
        overfill_bar = StatBar(
            pos=(50, 510),
            size=(200, 20),
            current=150,  # Will be clamped to 100
            maximum=100,
            fill_color=StatBar.XP_COLOR,
            label="Overfill"
        )
        self.ui.append(overfill_bar.frame)

        # Section 5: Animation demo
        section5_label = mcrfpy.Caption(
            text="Animation Demo (watch the bars change)",
            pos=(500, 290),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section5_label)

        self.anim_bar = StatBar(
            pos=(500, 320),
            size=(250, 30),
            current=50,
            maximum=100,
            fill_color=mcrfpy.Color(150, 100, 200),
            label="Animated"
        )
        self.ui.append(self.anim_bar.frame)

        # Start animation loop
        self._anim_direction = 1
        mcrfpy.Timer("anim_bar", self._animate_bar, 2000)

        # Section 6: Flash effect
        section6_label = mcrfpy.Caption(
            text="Flash Effect (press F)",
            pos=(500, 400),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section6_label)

        self.flash_bar = StatBar(
            pos=(500, 430),
            size=(250, 30),
            current=80,
            maximum=100,
            fill_color=StatBar.HEALTH_COLOR,
            label="Flash Me"
        )
        self.ui.append(self.flash_bar.frame)

        # Instructions
        instr = mcrfpy.Caption(
            text="1-4: Decrease bars | Shift+1-4: Increase bars | F: Flash | R: Reset | ESC: Exit",
            pos=(50, 730),
            font_size=14,
            fill_color=mcrfpy.Color(120, 120, 120)
        )
        self.ui.append(instr)

        # Status display
        self.status = mcrfpy.Caption(
            text="Status: Ready",
            pos=(50, 600),
            font_size=16,
            fill_color=mcrfpy.Color(100, 200, 100)
        )
        self.ui.append(self.status)

    def _animate_bar(self, runtime):
        """Animate the demo bar back and forth."""
        current = self.anim_bar.current
        if self._anim_direction > 0:
            new_val = min(100, current + 30)
            if new_val >= 100:
                self._anim_direction = -1
        else:
            new_val = max(10, current - 30)
            if new_val <= 10:
                self._anim_direction = 1

        self.anim_bar.set_value(new_val, animate=True)

    def on_key(self, key, state):
        """Handle keyboard input."""
        if state != "start":
            return

        if key == "Escape":
            sys.exit(0)

        # Number keys to modify bars
        bar_keys = ['hp', 'mp', 'stamina', 'xp']
        key_map = {"Num1": 0, "Num2": 1, "Num3": 2, "Num4": 3}

        if key in key_map:
            idx = key_map[key]
            if idx < len(bar_keys):
                bar = self.bars[bar_keys[idx]]
                # Decrease by 10
                bar.set_value(bar.current - 10, animate=True)
                self.status.text = f"Status: Decreased {bar_keys[idx].upper()}"

        elif key == "F":
            self.flash_bar.flash()
            self.status.text = "Status: Flash effect triggered!"

        elif key == "R":
            # Reset all bars
            self.bars['hp'].set_value(75, 100, animate=True)
            self.bars['mp'].set_value(50, 80, animate=True)
            self.bars['stamina'].set_value(90, 100, animate=True)
            self.bars['xp'].set_value(250, 1000, animate=True)
            self.status.text = "Status: All bars reset"

    def activate(self):
        """Activate the demo scene."""
        self.scene.on_key = self.on_key
        mcrfpy.current_scene = self.scene


def main():
    """Run the stat bar demo."""
    demo = StatBarDemo()
    demo.activate()

    # Headless mode: capture screenshot and exit
    try:
        if mcrfpy.headless_mode():
            from mcrfpy import automation
            mcrfpy.Timer("screenshot", lambda rt: (
                automation.screenshot("screenshots/primitives/stat_bar_demo.png"),
                sys.exit(0)
            ), 100)
    except AttributeError:
        pass


if __name__ == "__main__":
    main()
