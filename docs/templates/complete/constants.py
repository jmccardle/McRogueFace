"""
constants.py - Game Constants for McRogueFace Complete Roguelike Template

All configuration values in one place for easy tweaking.
"""

# =============================================================================
# WINDOW AND DISPLAY
# =============================================================================
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

# Grid display area (where the dungeon is rendered)
GRID_X = 0
GRID_Y = 0
GRID_WIDTH = 800
GRID_HEIGHT = 600

# Tile dimensions (must match your texture)
TILE_WIDTH = 16
TILE_HEIGHT = 16

# =============================================================================
# DUNGEON GENERATION
# =============================================================================
# Size of the dungeon in tiles
DUNGEON_WIDTH = 80
DUNGEON_HEIGHT = 45

# Room size constraints
ROOM_MIN_SIZE = 6
ROOM_MAX_SIZE = 12
MAX_ROOMS = 15

# Enemy spawning per room
MAX_ENEMIES_PER_ROOM = 3
MIN_ENEMIES_PER_ROOM = 0

# =============================================================================
# SPRITE INDICES (for kenney_tinydungeon.png - 16x16 tiles)
# Adjust these if using a different tileset
# =============================================================================
# Terrain
SPRITE_FLOOR = 48          # Dungeon floor
SPRITE_WALL = 33           # Wall tile
SPRITE_STAIRS_DOWN = 50    # Stairs going down
SPRITE_DOOR = 49           # Door tile

# Player sprites
SPRITE_PLAYER = 84         # Player character (knight)

# Enemy sprites
SPRITE_GOBLIN = 111        # Goblin enemy
SPRITE_ORC = 112           # Orc enemy
SPRITE_TROLL = 116         # Troll enemy

# Items (for future expansion)
SPRITE_POTION = 89         # Health potion
SPRITE_CHEST = 91          # Treasure chest

# =============================================================================
# COLORS (R, G, B, A)
# =============================================================================
# Map colors
COLOR_DARK_WALL = (50, 50, 100, 255)
COLOR_DARK_FLOOR = (30, 30, 50, 255)
COLOR_LIGHT_WALL = (100, 100, 150, 255)
COLOR_LIGHT_FLOOR = (80, 80, 100, 255)

# FOV overlay colors
COLOR_FOG = (0, 0, 0, 200)         # Unexplored areas
COLOR_REMEMBERED = (0, 0, 0, 128)  # Seen but not visible
COLOR_VISIBLE = (0, 0, 0, 0)       # Currently visible (transparent)

# UI Colors
COLOR_UI_BG = (20, 20, 30, 230)
COLOR_UI_BORDER = (80, 80, 120, 255)
COLOR_TEXT = (255, 255, 255, 255)
COLOR_TEXT_HIGHLIGHT = (255, 255, 100, 255)

# Health bar colors
COLOR_HP_BAR_BG = (80, 0, 0, 255)
COLOR_HP_BAR_FILL = (0, 180, 0, 255)
COLOR_HP_BAR_WARNING = (180, 180, 0, 255)
COLOR_HP_BAR_CRITICAL = (180, 0, 0, 255)

# Message log colors
COLOR_MSG_DEFAULT = (255, 255, 255, 255)
COLOR_MSG_DAMAGE = (255, 100, 100, 255)
COLOR_MSG_HEAL = (100, 255, 100, 255)
COLOR_MSG_INFO = (100, 100, 255, 255)
COLOR_MSG_IMPORTANT = (255, 255, 100, 255)

# =============================================================================
# PLAYER STATS
# =============================================================================
PLAYER_START_HP = 30
PLAYER_START_ATTACK = 5
PLAYER_START_DEFENSE = 2

# =============================================================================
# ENEMY STATS
# Each enemy type: (hp, attack, defense, xp_reward, name)
# =============================================================================
ENEMY_STATS = {
    'goblin': {
        'hp': 10,
        'attack': 3,
        'defense': 0,
        'xp': 35,
        'sprite': SPRITE_GOBLIN,
        'name': 'Goblin'
    },
    'orc': {
        'hp': 16,
        'attack': 4,
        'defense': 1,
        'xp': 50,
        'sprite': SPRITE_ORC,
        'name': 'Orc'
    },
    'troll': {
        'hp': 24,
        'attack': 6,
        'defense': 2,
        'xp': 100,
        'sprite': SPRITE_TROLL,
        'name': 'Troll'
    }
}

# Enemy spawn weights per dungeon level
# Format: {level: [(enemy_type, weight), ...]}
# Higher weight = more likely to spawn
ENEMY_SPAWN_WEIGHTS = {
    1: [('goblin', 100)],
    2: [('goblin', 80), ('orc', 20)],
    3: [('goblin', 60), ('orc', 40)],
    4: [('goblin', 40), ('orc', 50), ('troll', 10)],
    5: [('goblin', 20), ('orc', 50), ('troll', 30)],
}

# Default weights for levels beyond those defined
DEFAULT_SPAWN_WEIGHTS = [('goblin', 10), ('orc', 50), ('troll', 40)]

# =============================================================================
# FOV (Field of View) SETTINGS
# =============================================================================
FOV_RADIUS = 8           # How far the player can see
FOV_LIGHT_WALLS = True   # Whether walls at FOV edge are visible

# =============================================================================
# INPUT KEYS
# Key names as returned by McRogueFace keypressScene
# =============================================================================
KEY_UP = ['Up', 'W', 'Numpad8']
KEY_DOWN = ['Down', 'S', 'Numpad2']
KEY_LEFT = ['Left', 'A', 'Numpad4']
KEY_RIGHT = ['Right', 'D', 'Numpad6']

# Diagonal movement (numpad)
KEY_UP_LEFT = ['Numpad7']
KEY_UP_RIGHT = ['Numpad9']
KEY_DOWN_LEFT = ['Numpad1']
KEY_DOWN_RIGHT = ['Numpad3']

# Actions
KEY_WAIT = ['Period', 'Numpad5']     # Skip turn
KEY_DESCEND = ['Greater', 'Space']   # Go down stairs (> key or space)

# =============================================================================
# GAME MESSAGES
# =============================================================================
MSG_WELCOME = "Welcome to the dungeon! Find the stairs to descend deeper."
MSG_DESCEND = "You descend the stairs to level %d..."
MSG_PLAYER_ATTACK = "You attack the %s for %d damage!"
MSG_PLAYER_KILL = "You have slain the %s!"
MSG_PLAYER_MISS = "You attack the %s but do no damage."
MSG_ENEMY_ATTACK = "The %s attacks you for %d damage!"
MSG_ENEMY_MISS = "The %s attacks you but does no damage."
MSG_BLOCKED = "You can't move there!"
MSG_STAIRS = "You see stairs leading down here. Press > or Space to descend."
MSG_DEATH = "You have died! Press R to restart."
MSG_NO_STAIRS = "There are no stairs here."

# =============================================================================
# UI LAYOUT
# =============================================================================
# Health bar
HP_BAR_X = 10
HP_BAR_Y = 620
HP_BAR_WIDTH = 200
HP_BAR_HEIGHT = 24

# Message log
MSG_LOG_X = 10
MSG_LOG_Y = 660
MSG_LOG_WIDTH = 780
MSG_LOG_HEIGHT = 100
MSG_LOG_MAX_LINES = 5

# Dungeon level display
LEVEL_DISPLAY_X = 700
LEVEL_DISPLAY_Y = 620

# =============================================================================
# ASSET PATHS
# =============================================================================
TEXTURE_PATH = "assets/kenney_tinydungeon.png"
FONT_PATH = "assets/JetbrainsMono.ttf"
