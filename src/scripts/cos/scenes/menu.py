"""Main menu scene for Crypt of Sokoban.

Displays a title screen with a live demo grid, play button,
and settings buttons. Replaces the 7DRL's MainMenu class
that duplicated entity spawning code from the Crypt class.
"""

import random
import mcrfpy
from cos import Resources
from cos.constants import (
    GRID_ZOOM, ENEMY_PRESETS, COLOR_TEXT,
)
from cos.level.generator import Level
from cos.entities.player import PlayerEntity
from cos.entities.enemies import EnemyEntity
from cos.entities.objects import BoulderEntity, ExitEntity
from cos.ui.widgets import SweetButton


class MenuScene:
    """Main menu with animated demo and navigation buttons.

    The demo grid shows a small generated level with entities
    that wander randomly, giving the menu visual interest.
    """

    def __init__(self):
        self.scene = mcrfpy.Scene("menu")
        self.ui = self.scene.children
        self.play_scene = None

        res = Resources()

        # -- Demo grid (background) ---------------------------------------
        self.entities = []  # entity registry for demo animation
        self._demo_level = Level(20, 20)
        self.grid = self._demo_level.grid
        self.grid.zoom = 1.75
        gw = int(self.grid.grid_size.x)
        gh = int(self.grid.grid_size.y)
        self.grid.center_camera((gw / 2.0, gh / 2.0))

        demo_plan = [
            ("boulder", "boulder", "rat", "cyclops", "boulder"),
            ("spawn",),
            ("rat", "big rat"),
            ("button", "boulder", "exit"),
        ]
        coords = self._demo_level.generate(demo_plan)
        self._spawn_demo_entities(coords)

        # Wire up engine entities for rendering
        for entity in self.entities:
            entity.entity.grid = self.grid

        self.demo_timer = mcrfpy.Timer("demo_motion", self._demo_tick, 100)

        # -- Title text ---------------------------------------------------
        drop_shadow = mcrfpy.Caption(
            text="Crypt Of Sokoban", pos=(150, 10), font=res.font,
            fill_color=(96, 96, 96), outline_color=(192, 0, 0),
        )
        drop_shadow.outline = 3
        drop_shadow.font_size = 64

        title = mcrfpy.Caption(
            text="Crypt Of Sokoban", pos=(158, 18), font=res.font,
            fill_color=COLOR_TEXT,
        )
        title.font_size = 64

        # -- Toast notification -------------------------------------------
        self.toast = mcrfpy.Caption(
            text="", pos=(150, 400), font=res.font,
            fill_color=(0, 0, 0),
        )
        self.toast.font_size = 28
        self.toast.outline = 2
        self.toast.outline_color = (255, 255, 255)
        self._toast_remaining = None
        self._toast_timer = None

        # -- Buttons ------------------------------------------------------
        play_btn = SweetButton(
            (20, 248), "PLAY",
            box_width=200, box_height=110,
            icon=1, icon_scale=2.0, click=self._on_play,
        )

        config_btn = SweetButton(
            (10, 678), "Settings", icon=2, click=self._on_config,
        )

        scale_btn = SweetButton(
            (266, 678), "Scale up\nto 1080p", icon=15, click=self._on_scale,
        )
        self._scaled = False

        music_btn = SweetButton(
            (522, 678), "Music\nON", icon=12, click=self._on_music_toggle,
        )

        sfx_btn = SweetButton(
            (778, 678), "SFX\nON", icon=0, click=self._on_sfx_toggle,
        )

        # -- Assemble scene -----------------------------------------------
        for element in (
            self.grid, drop_shadow, title, self.toast,
            play_btn.base_frame, config_btn.base_frame,
            scale_btn.base_frame, music_btn.base_frame,
            sfx_btn.base_frame,
        ):
            self.ui.append(element)

    # -- Entity registry (minimal, for demo only) -------------------------

    def register_entity(self, entity):
        self.entities.append(entity)

    def unregister_entity(self, entity):
        if entity in self.entities:
            self.entities.remove(entity)

    # -- Demo animation ---------------------------------------------------

    def _spawn_demo_entities(self, coords):
        """Spawn entities for the demo grid. Reuses the same entity
        creation as PlayScene to avoid the 7DRL's duplicated spawning."""
        buttons = []
        for name, pos in sorted(coords, key=lambda c: c[0]):
            if name == "spawn":
                self.player = PlayerEntity(game=self)
                self.player.draw_pos = pos
            elif name == "boulder":
                BoulderEntity(pos[0], pos[1], game=self)
            elif name == "button":
                buttons.append(pos)
            elif name == "exit":
                btn = buttons.pop(0)
                ExitEntity(pos[0], pos[1], btn[0], btn[1], game=self)
            elif name in ENEMY_PRESETS:
                EnemyEntity.from_preset(name, pos[0], pos[1], game=self)

    def _demo_tick(self, timer, runtime):
        """Timer callback: animate demo entities randomly."""
        try:
            dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
            self.player.try_move(*random.choice(dirs))
            for entity in self.entities:
                entity.act()
        except Exception:
            pass  # demo animation is cosmetic; don't crash the menu

    # -- Navigation -------------------------------------------------------

    def activate(self):
        self.scene.activate()

    def _on_play(self, btn, args):
        if args[3] == mcrfpy.InputState.RELEASED:
            return
        self.demo_timer.stop()
        from cos.scenes.play import PlayScene
        self.play_scene = PlayScene()
        self.play_scene.activate()

    # -- Settings buttons -------------------------------------------------

    def _on_config(self, btn, args):
        if args[3] == mcrfpy.InputState.RELEASED:
            return
        self._show_toast("Settings will go here.")

    def _on_scale(self, btn, args):
        if args[3] == mcrfpy.InputState.RELEASED:
            return
        self._scaled = not self._scaled
        btn.unpress()
        if self._scaled:
            self._show_toast("Windowed mode only.\nCheck Settings for fine-tuned controls.")
            mcrfpy.set_scale(1.3)
            btn.text = "Scale down\nto 1.0x"
        else:
            mcrfpy.set_scale(1.0)
            btn.text = "Scale up\nto 1080p"

    def _on_music_toggle(self, btn, args):
        if args[3] == mcrfpy.InputState.RELEASED:
            return
        res = Resources()
        res.music_enabled = not res.music_enabled
        if res.music_enabled:
            res.set_music_volume(res.music_volume)
            btn.text = "Music\nON"
            btn.sprite_number = 12
        else:
            self._show_toast("Use your volume keys or\nlook in Settings for a volume meter.")
            res.set_music_volume(0)
            btn.text = "Music\nOFF"
            btn.sprite_number = 17

    def _on_sfx_toggle(self, btn, args):
        if args[3] == mcrfpy.InputState.RELEASED:
            return
        res = Resources()
        res.sfx_enabled = not res.sfx_enabled
        if res.sfx_enabled:
            res.set_sfx_volume(res.sfx_volume)
            btn.text = "SFX\nON"
            btn.sprite_number = 0
        else:
            self._show_toast("Use your volume keys or\nlook in Settings for a volume meter.")
            res.set_sfx_volume(0)
            btn.text = "SFX\nOFF"
            btn.sprite_number = 17

    # -- Toast notification -----------------------------------------------

    def _show_toast(self, text):
        self.toast.text = text
        self._toast_remaining = 350
        self.toast.fill_color = (255, 255, 255, 255)
        self.toast.outline_color = (0, 0, 0, 255)
        if self._toast_timer:
            self._toast_timer.stop()
        self._toast_timer = mcrfpy.Timer("toast_timer", self._toast_tick, 100)

    def _toast_tick(self, timer, runtime):
        self._toast_remaining -= 5
        if self._toast_remaining < 0:
            self._toast_timer.stop()
            self._toast_timer = None
            self.toast.text = ""
            return
        alpha = min(self._toast_remaining, 255)
        self.toast.fill_color = (255, 255, 255, alpha)
        self.toast.outline_color = (0, 0, 0, alpha)
