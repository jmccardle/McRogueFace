#!/usr/bin/env python3
"""Responsive Design Cookbook - Layouts that survive aspect ratio changes

Interactive controls:
    1: Landscape 16:9  (1280x720)
    2: Desktop 4:3     (1024x768)
    3: Ultrawide 21:9  (1260x540)
    4: Portrait 9:16   (720x1280)
    S: Cycle scaling modes (Fit / Stretch / Center)
    ESC: Exit demo

This demo shows three approaches to resolution-independent layout:

    APPROACH 1 - "Fit and forget" (scaling_mode="fit")
        Design for one resolution. The engine scales and letterboxes.
        Simplest. Works great when aspect ratio won't change.

    APPROACH 2 - Alignment anchoring (align=TOP_RIGHT, margin=10)
        Attach elements to edges/corners. The engine repositions them
        when game_resolution changes. Good for HUD elements.

    APPROACH 3 - Layout function (compute positions from resolution)
        Write a function that takes (width, height) and places everything.
        Most flexible. Required when layout structure must change
        (e.g. sidebar becomes bottom bar in portrait mode).

The demo uses Approach 3 to build a game-like HUD that restructures
itself for landscape vs portrait orientations.
"""
import mcrfpy
import sys


# -- Color palette --
BG_COLOR = mcrfpy.Color(18, 18, 24)
PANEL_COLOR = mcrfpy.Color(28, 32, 42)
PANEL_BORDER = mcrfpy.Color(55, 65, 85)
ACCENT = mcrfpy.Color(90, 140, 220)
HEALTH_COLOR = mcrfpy.Color(180, 50, 60)
MANA_COLOR = mcrfpy.Color(50, 100, 200)
XP_COLOR = mcrfpy.Color(180, 160, 40)
TEXT_COLOR = mcrfpy.Color(210, 210, 210)
DIM_TEXT = mcrfpy.Color(120, 120, 130)
GAME_AREA_COLOR = mcrfpy.Color(12, 14, 18)


# -- Resolution presets --
PRESETS = [
    ("Landscape 16:9",  (1280, 720)),
    ("Desktop 4:3",     (1024, 768)),
    ("Ultrawide 21:9",  (1260, 540)),
    ("Portrait 9:16",   (720, 1280)),
]

SCALING_MODES = ["fit", "stretch", "center"]


class ResponsiveDemo:
    def __init__(self):
        self.preset_index = 0
        self.scaling_index = 0
        self.apply_resolution(0)

    # -- Resolution switching --

    def apply_resolution(self, preset_index):
        """Change game_resolution and rebuild the entire layout."""
        self.preset_index = preset_index
        name, (w, h) = PRESETS[preset_index]

        win = mcrfpy.Window.get()
        win.game_resolution = (w, h)
        win.scaling_mode = SCALING_MODES[self.scaling_index]

        # Create a fresh scene each time (UICollection has no clear())
        self.scene = mcrfpy.Scene("responsive_demo")
        self.scene.on_key = self.on_key
        self.ui = self.scene.children
        self.build_layout(w, h)
        mcrfpy.current_scene = self.scene

    # -- Layout --

    def build_layout(self, w, h):
        """Build the full HUD layout for the given resolution.

        This is the core of Approach 3: a single function that reads
        the resolution and decides where everything goes. The layout
        structure changes based on orientation.
        """
        is_portrait = h > w
        name, _ = PRESETS[self.preset_index]

        # Full-screen background
        self.ui.append(mcrfpy.Frame(
            pos=(0, 0), size=(w, h), fill_color=BG_COLOR
        ))

        if is_portrait:
            self._layout_portrait(w, h)
        else:
            self._layout_landscape(w, h)

        # Resolution label (always top-center)
        self._add_resolution_label(w, h, name)

        # Instructions (always bottom)
        self._add_instructions(w, h)

    def _layout_landscape(self, w, h):
        """Landscape/desktop: sidebar on right, game area fills the rest."""
        sidebar_w = 200
        margin = 8
        bar_h = 40

        # Game area - fills left side
        game_w = w - sidebar_w - margin * 3
        game_h = h - bar_h - margin * 3 - 30  # room for top bar + label
        game_y = margin + 30  # below resolution label

        self.ui.append(mcrfpy.Frame(
            pos=(margin, game_y),
            size=(game_w, game_h),
            fill_color=GAME_AREA_COLOR,
            outline_color=PANEL_BORDER,
            outline=1
        ))
        self._add_game_placeholder(margin, game_y, game_w, game_h)

        # Sidebar - right edge
        sidebar_x = w - sidebar_w - margin
        sidebar_h = h - margin * 2 - 30
        sidebar = mcrfpy.Frame(
            pos=(sidebar_x, game_y),
            size=(sidebar_w, sidebar_h),
            fill_color=PANEL_COLOR,
            outline_color=PANEL_BORDER,
            outline=1
        )
        self.ui.append(sidebar)
        self._populate_sidebar(sidebar, sidebar_w, sidebar_h)

        # Bottom bar - below game area
        bar_y = h - bar_h - margin
        bar_w = game_w
        bar = mcrfpy.Frame(
            pos=(margin, bar_y),
            size=(bar_w, bar_h),
            fill_color=PANEL_COLOR,
            outline_color=PANEL_BORDER,
            outline=1
        )
        self.ui.append(bar)
        self._populate_action_bar(bar, bar_w, bar_h)

    def _layout_portrait(self, w, h):
        """Portrait: game area on top, panels stacked below."""
        margin = 8
        panel_h = 160
        bar_h = 50

        # Game area - top portion
        game_y = margin + 30
        game_h = h - panel_h - bar_h - margin * 4 - 30
        game_w = w - margin * 2

        self.ui.append(mcrfpy.Frame(
            pos=(margin, game_y),
            size=(game_w, game_h),
            fill_color=GAME_AREA_COLOR,
            outline_color=PANEL_BORDER,
            outline=1
        ))
        self._add_game_placeholder(margin, game_y, game_w, game_h)

        # Info panel - below game area, full width
        panel_y = game_y + game_h + margin
        panel_w = w - margin * 2
        panel = mcrfpy.Frame(
            pos=(margin, panel_y),
            size=(panel_w, panel_h),
            fill_color=PANEL_COLOR,
            outline_color=PANEL_BORDER,
            outline=1
        )
        self.ui.append(panel)
        self._populate_info_panel_wide(panel, panel_w, panel_h)

        # Action bar - bottom, full width
        bar_y = h - bar_h - margin
        bar_w = w - margin * 2
        bar = mcrfpy.Frame(
            pos=(margin, bar_y),
            size=(bar_w, bar_h),
            fill_color=PANEL_COLOR,
            outline_color=PANEL_BORDER,
            outline=1
        )
        self.ui.append(bar)
        self._populate_action_bar(bar, bar_w, bar_h)

    # -- Panel content builders --

    def _populate_sidebar(self, parent, w, h):
        """Fill sidebar with character stats and inventory."""
        pad = 10
        y = pad

        # Character name
        parent.children.append(mcrfpy.Caption(
            text="Adventurer", pos=(w // 2, y),
            font_size=16, fill_color=ACCENT
        ))
        y += 28

        # Stat bars
        for label, value, max_val, color in [
            ("HP",   73, 100, HEALTH_COLOR),
            ("MP",   45,  80, MANA_COLOR),
            ("XP", 1200, 2000, XP_COLOR),
        ]:
            parent.children.append(mcrfpy.Caption(
                text=f"{label}: {value}/{max_val}",
                pos=(pad, y), font_size=12, fill_color=TEXT_COLOR
            ))
            y += 18

            # Bar background
            bar_w = w - pad * 2
            parent.children.append(mcrfpy.Frame(
                pos=(pad, y), size=(bar_w, 8),
                fill_color=mcrfpy.Color(40, 40, 50)
            ))
            # Bar fill
            fill_w = int(bar_w * value / max_val)
            parent.children.append(mcrfpy.Frame(
                pos=(pad, y), size=(fill_w, 8),
                fill_color=color
            ))
            y += 16

        # Divider
        y += 4
        parent.children.append(mcrfpy.Frame(
            pos=(pad, y), size=(w - pad * 2, 1),
            fill_color=PANEL_BORDER
        ))
        y += 12

        # Inventory header
        parent.children.append(mcrfpy.Caption(
            text="Inventory", pos=(w // 2, y),
            font_size=14, fill_color=ACCENT
        ))
        y += 24

        # Inventory slots (grid of small frames)
        slot_size = 28
        slots_per_row = (w - pad * 2 + 4) // (slot_size + 4)
        for i in range(12):
            row = i // slots_per_row
            col = i % slots_per_row
            sx = pad + col * (slot_size + 4)
            sy = y + row * (slot_size + 4)
            parent.children.append(mcrfpy.Frame(
                pos=(sx, sy), size=(slot_size, slot_size),
                fill_color=mcrfpy.Color(22, 24, 32),
                outline_color=PANEL_BORDER, outline=1
            ))

        # Minimap at bottom of sidebar
        minimap_size = min(w - pad * 2, 120)
        minimap_y = h - minimap_size - pad
        parent.children.append(mcrfpy.Caption(
            text="Map", pos=(w // 2, minimap_y - 16),
            font_size=12, fill_color=DIM_TEXT
        ))
        parent.children.append(mcrfpy.Frame(
            pos=((w - minimap_size) // 2, minimap_y),
            size=(minimap_size, minimap_size),
            fill_color=mcrfpy.Color(15, 20, 15),
            outline_color=PANEL_BORDER, outline=1
        ))

    def _populate_info_panel_wide(self, parent, w, h):
        """Fill a wide info panel (portrait mode) with stats side by side."""
        pad = 10
        col_w = (w - pad * 3) // 2

        # Left column: stats
        y = pad
        parent.children.append(mcrfpy.Caption(
            text="Adventurer", pos=(col_w // 2 + pad, y),
            font_size=16, fill_color=ACCENT
        ))
        y += 26

        for label, value, max_val, color in [
            ("HP",   73, 100, HEALTH_COLOR),
            ("MP",   45,  80, MANA_COLOR),
            ("XP", 1200, 2000, XP_COLOR),
        ]:
            parent.children.append(mcrfpy.Caption(
                text=f"{label}: {value}/{max_val}",
                pos=(pad, y), font_size=12, fill_color=TEXT_COLOR
            ))
            y += 16
            bar_w = col_w - pad
            parent.children.append(mcrfpy.Frame(
                pos=(pad, y), size=(bar_w, 6),
                fill_color=mcrfpy.Color(40, 40, 50)
            ))
            fill_w = int(bar_w * value / max_val)
            parent.children.append(mcrfpy.Frame(
                pos=(pad, y), size=(fill_w, 6),
                fill_color=color
            ))
            y += 12

        # Right column: inventory + minimap
        right_x = col_w + pad * 2
        parent.children.append(mcrfpy.Caption(
            text="Inventory", pos=(right_x + col_w // 2, pad),
            font_size=14, fill_color=ACCENT
        ))

        slot_size = 24
        slots_per_row = (col_w - pad) // (slot_size + 4)
        iy = pad + 22
        for i in range(8):
            row = i // slots_per_row
            col = i % slots_per_row
            sx = right_x + col * (slot_size + 4)
            sy = iy + row * (slot_size + 4)
            parent.children.append(mcrfpy.Frame(
                pos=(sx, sy), size=(slot_size, slot_size),
                fill_color=mcrfpy.Color(22, 24, 32),
                outline_color=PANEL_BORDER, outline=1
            ))

        # Small minimap in portrait
        mm_size = min(60, h - pad * 2)
        mm_x = right_x + col_w - mm_size - pad
        mm_y = h - mm_size - pad
        parent.children.append(mcrfpy.Frame(
            pos=(mm_x, mm_y), size=(mm_size, mm_size),
            fill_color=mcrfpy.Color(15, 20, 15),
            outline_color=PANEL_BORDER, outline=1
        ))

    def _populate_action_bar(self, parent, w, h):
        """Fill the action bar with ability slots."""
        pad = 6
        num_slots = 6
        slot_h = h - pad * 2
        slot_w = slot_h  # square
        total_w = num_slots * slot_w + (num_slots - 1) * pad
        start_x = (w - total_w) // 2

        for i in range(num_slots):
            sx = start_x + i * (slot_w + pad)
            slot = mcrfpy.Frame(
                pos=(sx, pad), size=(slot_w, slot_h),
                fill_color=mcrfpy.Color(35, 38, 50),
                outline_color=ACCENT if i == 0 else PANEL_BORDER,
                outline=2 if i == 0 else 1
            )
            parent.children.append(slot)

            # Keybind label
            slot.children.append(mcrfpy.Caption(
                text=str(i + 1), pos=(slot_w // 2, 2),
                font_size=10, fill_color=DIM_TEXT
            ))

    def _add_game_placeholder(self, x, y, w, h):
        """Add placeholder text in the game area."""
        self.ui.append(mcrfpy.Caption(
            text="[ Game Area ]",
            pos=(x + w // 2, y + h // 2 - 10),
            font_size=20, fill_color=mcrfpy.Color(40, 45, 55)
        ))

    # -- HUD overlays --

    def _add_resolution_label(self, w, h, preset_name):
        """Show current resolution and scaling mode at top."""
        mode = SCALING_MODES[self.scaling_index]
        label = mcrfpy.Caption(
            text=f"{preset_name}  ({w}x{h})  scaling: {mode}",
            pos=(w // 2, 6),
            font_size=13, fill_color=ACCENT
        )
        self.ui.append(label)

    def _add_instructions(self, w, h):
        """Add key instructions at the bottom edge."""
        is_portrait = h > w
        text = "1-4: Resolutions | S: Scaling mode | ESC: Exit"
        self.ui.append(mcrfpy.Caption(
            text=text,
            pos=(w // 2, h - 6),
            font_size=11, fill_color=DIM_TEXT
        ))

    # -- Input --

    def on_key(self, key, state):
        if state != mcrfpy.InputState.PRESSED:
            return

        if key == mcrfpy.Key.ESCAPE:
            sys.exit(0)
        elif key == mcrfpy.Key.NUM1:
            self.apply_resolution(0)
        elif key == mcrfpy.Key.NUM2:
            self.apply_resolution(1)
        elif key == mcrfpy.Key.NUM3:
            self.apply_resolution(2)
        elif key == mcrfpy.Key.NUM4:
            self.apply_resolution(3)
        elif key == mcrfpy.Key.S:
            self.scaling_index = (self.scaling_index + 1) % len(SCALING_MODES)
            self.apply_resolution(self.preset_index)

    # -- Activation --

    def activate(self):
        # Scene is already active from apply_resolution()
        pass


def main():
    demo = ResponsiveDemo()
    demo.activate()

    # Headless screenshot capture (set RESPONSIVE_SCREENSHOTS=1)
    import os
    if os.environ.get("RESPONSIVE_SCREENSHOTS"):
        from mcrfpy import automation
        os.makedirs("screenshots/features", exist_ok=True)
        for i, (name, (w, h)) in enumerate(PRESETS):
            demo.apply_resolution(i)
            mcrfpy.step(0.05)
            tag = name.lower().replace(" ", "_").replace("/", "")
            automation.screenshot(
                f"screenshots/features/responsive_{tag}.png"
            )
            print(f"  saved responsive_{tag}.png ({w}x{h})")
        sys.exit(0)


if __name__ == "__main__":
    main()
