"""Heads-up display for Crypt of Sokoban.

Renders health bar, armor bar, inventory sidebar, and level info.
Extracted from the 7DRL's Crypt god object where HUD logic was mixed
with game state, input handling, and entity spawning.
"""

import mcrfpy
from cos import Resources
from cos.constants import (
    SPRITE_EMPTY,
    SPRITE_HEART_EMPTY, SPRITE_HEART_FULL, SPRITE_HEART_HALF,
    SPRITE_ARMOR_FULL, SPRITE_ARMOR_HALF,
    SPRITE_KEY_BASE,
    HUD_POS, HUD_SIZE,
    SIDEBAR_POS, SIDEBAR_SIZE,
    COLOR_SIDEBAR, COLOR_TEXT, COLOR_TEXT_OUTLINE,
)


class HUD:
    """Manages all HUD elements: health bar, armor, inventory, level info.

    Call update() each turn to refresh displayed values from the player.

    Attributes:
        headsup: Frame containing health/armor bars and stat text
        sidebar: Frame containing inventory sprites and level caption
    """

    def __init__(self):
        res = Resources()

        # -- Heads-up frame (health + armor bars) -------------------------
        self.headsup = mcrfpy.Frame(
            pos=HUD_POS, size=HUD_SIZE, fill_color=(0, 0, 0, 0),
        )

        self.health_sprites = []
        self.armor_sprites = []
        for i in range(10):
            hs = mcrfpy.Sprite(
                x=32 * i, y=2, texture=res.tileset,
                sprite_index=SPRITE_EMPTY, scale=2,
            )
            self.headsup.children.append(hs)
            self.health_sprites.append(hs)

            arm = mcrfpy.Sprite(
                x=32 * i, y=42, texture=res.tileset,
                sprite_index=SPRITE_EMPTY, scale=2,
            )
            self.headsup.children.append(arm)
            self.armor_sprites.append(arm)

        self.stat_caption = mcrfpy.Caption(
            text="HP:10\nDef:0(+0)", pos=(325, 0), font=res.font,
            fill_color=COLOR_TEXT,
        )
        self.stat_caption.outline = 3
        self.stat_caption.outline_color = COLOR_TEXT_OUTLINE
        self.headsup.children.append(self.stat_caption)

        # -- Sidebar frame (inventory + level) ----------------------------
        self.sidebar = mcrfpy.Frame(
            pos=SIDEBAR_POS, size=SIDEBAR_SIZE, fill_color=COLOR_SIDEBAR,
        )

        self.level_caption = mcrfpy.Caption(
            text="Level: 1", pos=(5, 5), font=res.font,
            fill_color=COLOR_TEXT,
        )
        self.level_caption.font_size = 26
        self.level_caption.outline = 3
        self.level_caption.outline_color = COLOR_TEXT_OUTLINE
        self.sidebar.children.append(self.level_caption)

        # Inventory item sprites (5 slots: 2 equipped + 3 consumable)
        self.inv_sprites = []
        for i in range(5):
            s = mcrfpy.Sprite(
                x=15, y=70 + 95 * i, texture=res.tileset,
                sprite_index=SPRITE_EMPTY, scale=6.0,
            )
            self.sidebar.children.append(s)
            self.inv_sprites.append(s)

        # Hotkey icons for consumable slots (1, 2, 3)
        self.key_sprites = []
        for i in range(3):
            s = mcrfpy.Sprite(
                x=75, y=130 + 95 * 2 + 95 * i, texture=res.tileset,
                sprite_index=SPRITE_KEY_BASE + i, scale=3.0,
            )
            self.sidebar.children.append(s)
            self.key_sprites.append(s)

        # Item name captions
        self.inv_captions = []
        for i in range(5):
            c = mcrfpy.Caption(
                text="", pos=(25, 130 + 95 * i), font=res.font,
                fill_color=COLOR_TEXT,
            )
            c.font_size = 16
            self.sidebar.children.append(c)
            self.inv_captions.append(c)

    def update(self, player, depth):
        """Refresh all HUD elements from current game state.

        Args:
            player: PlayerEntity with hp, max_hp, equipped, inventory
            depth: current dungeon depth
        """
        self._update_health_bar(player)
        self._update_armor_bar(player)
        self._update_stat_text(player)
        self._update_inventory(player)
        self.level_caption.text = f"Level: {depth}"

    def _update_health_bar(self, player):
        for i, sprite in enumerate(self.health_sprites):
            full = player.hp - (i * 2)
            capacity = player.max_hp - (i * 2)
            sprite.sprite_number = SPRITE_EMPTY
            if capacity >= 2:
                sprite.sprite_number = SPRITE_HEART_EMPTY
            if full >= 2:
                sprite.sprite_number = SPRITE_HEART_FULL
            elif full == 1:
                sprite.sprite_number = SPRITE_HEART_HALF

    def _update_armor_bar(self, player):
        defense = player.calc_defense()
        for i, sprite in enumerate(self.armor_sprites):
            full = defense - (i * 2)
            sprite.sprite_number = SPRITE_EMPTY
            if full >= 2:
                sprite.sprite_number = SPRITE_ARMOR_FULL
            elif full == 1:
                sprite.sprite_number = SPRITE_ARMOR_HALF

    def _update_stat_text(self, player):
        defense = player.calc_defense()
        bonus = defense - player.base_defense
        self.stat_caption.text = f"HP:{player.hp}\nDef:{defense}(+{bonus})"

    def _update_inventory(self, player):
        """Update inventory display: 2 equipment slots + 3 consumable slots."""
        for i in range(5):
            if i < 2:
                item = player.equipped[i] if i < len(player.equipped) else None
            else:
                slot = i - 2
                item = (player.inventory[slot]
                        if slot < len(player.inventory) else None)

            if item is None:
                self.inv_sprites[i].sprite_number = SPRITE_EMPTY
                self.inv_captions[i].text = ""
                if i >= 2:
                    self.key_sprites[i - 2].sprite_number = SPRITE_EMPTY
                continue

            self.inv_sprites[i].sprite_number = item.sprite
            if i >= 2:
                self.key_sprites[i - 2].sprite_number = SPRITE_KEY_BASE + (i - 2)

            if item.zap_cooldown_remaining:
                self.inv_captions[i].text = f"[{item.zap_cooldown_remaining}] {item.text}"
            else:
                self.inv_captions[i].text = item.text
            self.inv_captions[i].fill_color = item.text_color
