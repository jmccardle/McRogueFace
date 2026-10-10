"""Named constants for Crypt of Sokoban.

Eliminates magic numbers scattered throughout the original 7DRL code.
Sprite indices reference the kenney_TD_MR_IP.png tileset (16x16 grid).
"""

# -- Asset paths ----------------------------------------------------------
TILESET_PATH = "assets/kenney_TD_MR_IP.png"
TILESET_TILE_SIZE = 16
BUTTON_TEXTURE_PATH = "assets/48px_ui_icons-KenneyNL.png"
BUTTON_TEXTURE_SIZE = 48
FONT_PATH = "assets/JetbrainsMono.ttf"

# -- Sprite indices: entities ---------------------------------------------
SPRITE_PLAYER = 84
SPRITE_BOULDER = 66
SPRITE_BUTTON = 250
SPRITE_EXIT_LOCKED = 45
SPRITE_EXIT_UNLOCKED = 21
SPRITE_TREASURE_CLOSED = 89
SPRITE_TREASURE_OPEN = 91
SPRITE_ENEMY_RAT = 123
SPRITE_ENEMY_BIG_RAT = 130
SPRITE_ENEMY_CYCLOPS = 109
SPRITE_EMPTY = 659  # transparent/blank tile

# Dead enemy sprite = base_sprite + this offset
SPRITE_DEAD_OFFSET = 246

# -- Sprite indices: HUD -------------------------------------------------
SPRITE_HEART_EMPTY = 208
SPRITE_HEART_FULL = 210
SPRITE_HEART_HALF = 209
SPRITE_ARMOR_FULL = 211
SPRITE_ARMOR_HALF = 212

# -- Sprite indices: inventory hotkeys ------------------------------------
SPRITE_KEY_BASE = 384  # hotkey icons: 384, 385, 386 for slots 1-3

# -- Tile painting --------------------------------------------------------
# TODO: Replace with Wang tile terrain IDs when tileset is designed in Tiled
TILE_FALLBACK = 431  # "tile of last resort" when no WFC rule matches

# -- Entity draw order (lower = rendered first / behind) ------------------
DRAW_ORDER_BUTTON = 1
DRAW_ORDER_DEAD_ENEMY = 1
DRAW_ORDER_EXIT = 2
DRAW_ORDER_TREASURE = 6
DRAW_ORDER_ENEMY = 7
DRAW_ORDER_BOULDER = 8
DRAW_ORDER_PLAYER = 10

# -- UI layout (pixel coordinates) ----------------------------------------
# Grid display area
GRID_POS = (10, 5)
GRID_SIZE = (1014, 700)
GRID_ZOOM = 2.0

# Sidebar
SIDEBAR_POS = (860, 4)
SIDEBAR_SIZE = (160, 600)

# Heads-up display (health/armor bars)
HUD_POS = (10, 684)
HUD_SIZE = (320, 64)

# UI colors
COLOR_FRAME = (64, 64, 128)
COLOR_SIDEBAR = (96, 96, 160)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_OUTLINE = (0, 0, 0)

# -- Enemy stat presets ---------------------------------------------------
ENEMY_PRESETS = {
    "rat": {
        "hp": 2, "base_damage": 1, "base_defense": 0,
        "sprite": SPRITE_ENEMY_RAT, "can_push": False,
        "move_cooldown": 1,
    },
    "big rat": {
        "hp": 4, "base_damage": 2, "base_defense": 0,
        "sprite": SPRITE_ENEMY_BIG_RAT, "can_push": False,
        "move_cooldown": 1,
    },
    "cyclops": {
        "hp": 8, "base_damage": 3, "base_defense": 2,
        "sprite": SPRITE_ENEMY_CYCLOPS, "can_push": True,
        "move_cooldown": 0,
    },
}

# -- Level plan data ------------------------------------------------------
# Each entry maps depth -> list of room contents.
# Room contents are tuples of entity type names.
# A set means "pick one arrangement at random".
LEVEL_PLANS = {
    1: [("spawn", "button", "boulder"), ("exit",)],
    2: [("spawn", "button", "treasure", "treasure", "treasure",
         "rat", "rat", "boulder"), ("exit",)],
    3: [("spawn", "button", "boulder"), ("rat",), ("exit",)],
    4: [("spawn", "button", "rat"), ("boulder", "rat", "treasure"), ("exit",)],
    5: [("spawn", "button", "rat"), ("boulder", "rat"), ("exit",)],
    6: {(("spawn", "button"), ("boulder", "treasure", "exit")),
        (("spawn", "boulder"), ("button", "treasure", "exit"))},
    7: {(("spawn", "button"), ("boulder", "treasure", "exit")),
        (("spawn", "boulder"), ("button", "treasure", "exit"))},
    8: {(("spawn", "treasure", "button"), ("boulder", "treasure", "exit")),
        (("spawn", "treasure", "boulder"), ("button", "treasure", "exit"))},
}

# -- Audio ----------------------------------------------------------------
SFX_DIR = "assets/sfx"
SFX_SPLAT_COUNT = 9  # splat1.ogg through splat9.ogg
