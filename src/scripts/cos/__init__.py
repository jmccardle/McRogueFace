"""Crypt of Sokoban - A roguelike Sokoban puzzle game.

Remastered from the 7DRL 2025 entry to showcase McRogueFace engine capabilities.
"""

import mcrfpy
from cos.constants import (
    TILESET_PATH, TILESET_TILE_SIZE,
    BUTTON_TEXTURE_PATH, BUTTON_TEXTURE_SIZE,
    FONT_PATH, SFX_DIR, SFX_SPLAT_COUNT,
)


class Resources:
    """Centralized resource manager. Loaded once, shared everywhere.

    Original 7DRL loaded the same texture 3 times across different modules.
    This class provides a single point of access for all shared assets.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Shared assets
        self.tileset = mcrfpy.Texture(TILESET_PATH, TILESET_TILE_SIZE, TILESET_TILE_SIZE)
        self.button_texture = mcrfpy.Texture(BUTTON_TEXTURE_PATH, BUTTON_TEXTURE_SIZE, BUTTON_TEXTURE_SIZE)
        self.font = mcrfpy.Font(FONT_PATH)

        # Audio
        self.music_enabled = True
        self.music_volume = 40
        self.sfx_enabled = True
        self.sfx_volume = 100
        self.master_volume = 100

        self.splats = []
        for i in range(1, SFX_SPLAT_COUNT + 1):
            try:
                self.splats.append(mcrfpy.Sound(f"{SFX_DIR}/splat{i}.ogg"))
            except RuntimeError:
                pass  # sound file not found in WASM or missing asset

        self.music = None

    def play_sfx(self, sfx_id):
        if not (self.sfx_enabled and self.sfx_volume and self.master_volume):
            return
        if sfx_id < len(self.splats):
            sound = self.splats[sfx_id]
            sound.volume = self.master_volume / 100 * self.sfx_volume
            sound.play()

    def play_music(self, track_path):
        if not (self.music_enabled and self.music_volume and self.master_volume):
            return
        try:
            self.music = mcrfpy.Music(track_path)
            self.music.volume = self.master_volume / 100 * self.music_volume
            self.music.play()
        except RuntimeError:
            pass  # music file not found

    def set_music_volume(self, volume):
        self.music_volume = volume
        if self.music:
            self.music.volume = self.master_volume / 100 * self.music_volume

    def set_sfx_volume(self, volume):
        self.sfx_volume = volume


def run():
    """Entry point: launch the game from the main menu."""
    from cos.scenes.menu import MenuScene
    menu = MenuScene()
    menu.activate()
