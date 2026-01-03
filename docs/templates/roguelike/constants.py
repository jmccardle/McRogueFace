"""
constants.py - Roguelike Template Constants

This module defines all the constants used throughout the roguelike template,
including sprite indices for CP437 tileset, colors for FOV system, and
game configuration values.

CP437 is the classic IBM PC character set commonly used in traditional roguelikes.
The sprite indices correspond to ASCII character codes in a CP437 tileset.
"""

import mcrfpy

# =============================================================================
# SPRITE INDICES (CP437 Character Codes)
# =============================================================================
# These indices correspond to characters in a CP437-style tileset.
# The default McRogueFace tileset uses 16x16 sprites arranged in a grid.

# Terrain sprites
SPRITE_FLOOR = 46       # '.' - Standard floor tile
SPRITE_WALL = 35        # '#' - Wall/obstacle tile
SPRITE_DOOR_CLOSED = 43 # '+' - Closed door
SPRITE_DOOR_OPEN = 47   # '/' - Open door
SPRITE_STAIRS_DOWN = 62 # '>' - Stairs going down
SPRITE_STAIRS_UP = 60   # '<' - Stairs going up

# Player sprite
SPRITE_PLAYER = 64      # '@' - The classic roguelike player symbol

# Enemy sprites
SPRITE_ORC = 111        # 'o' - Orc enemy
SPRITE_TROLL = 84       # 'T' - Troll enemy
SPRITE_GOBLIN = 103     # 'g' - Goblin enemy
SPRITE_RAT = 114        # 'r' - Giant rat
SPRITE_SNAKE = 115      # 's' - Snake
SPRITE_ZOMBIE = 90      # 'Z' - Zombie

# Item sprites
SPRITE_POTION = 33      # '!' - Potion
SPRITE_SCROLL = 63      # '?' - Scroll
SPRITE_GOLD = 36        # '$' - Gold/treasure
SPRITE_WEAPON = 41      # ')' - Weapon
SPRITE_ARMOR = 91       # '[' - Armor
SPRITE_RING = 61        # '=' - Ring

# =============================================================================
# FOV/VISIBILITY COLORS
# =============================================================================
# These colors are applied as overlays to grid tiles to create the fog of war
# effect. The alpha channel determines how much of the original tile shows through.

# Fully visible - no overlay (alpha = 0 means completely transparent overlay)
COLOR_VISIBLE = mcrfpy.Color(0, 0, 0, 0)

# Previously explored but not currently visible - dim blue-gray overlay
# This creates the "memory" effect where you can see the map layout
# but not current enemy positions
COLOR_EXPLORED = mcrfpy.Color(50, 50, 80, 180)

# Never seen - completely black (alpha = 255 means fully opaque)
COLOR_UNKNOWN = mcrfpy.Color(0, 0, 0, 255)

# =============================================================================
# TILE COLORS
# =============================================================================
# Base colors for different tile types (applied to the tile's color property)

COLOR_FLOOR = mcrfpy.Color(50, 50, 50)      # Dark gray floor
COLOR_WALL = mcrfpy.Color(100, 100, 100)    # Lighter gray walls
COLOR_FLOOR_LIT = mcrfpy.Color(100, 90, 70) # Warm lit floor
COLOR_WALL_LIT = mcrfpy.Color(130, 110, 80) # Warm lit walls

# =============================================================================
# ENTITY COLORS
# =============================================================================
# Colors applied to entity sprites

COLOR_PLAYER = mcrfpy.Color(255, 255, 255)  # White player
COLOR_ORC = mcrfpy.Color(63, 127, 63)       # Green orc
COLOR_TROLL = mcrfpy.Color(0, 127, 0)       # Darker green troll
COLOR_GOBLIN = mcrfpy.Color(127, 127, 0)    # Yellow-green goblin

# =============================================================================
# GAME CONFIGURATION
# =============================================================================

# Map dimensions (in tiles)
MAP_WIDTH = 80
MAP_HEIGHT = 45

# Room generation parameters
ROOM_MIN_SIZE = 6       # Minimum room dimension
ROOM_MAX_SIZE = 12      # Maximum room dimension
MAX_ROOMS = 30          # Maximum number of rooms to generate

# FOV settings
FOV_RADIUS = 8          # How far the player can see

# Display settings
GRID_PIXEL_WIDTH = 1024   # Grid display width in pixels
GRID_PIXEL_HEIGHT = 768   # Grid display height in pixels

# Sprite size (should match your tileset)
SPRITE_WIDTH = 16
SPRITE_HEIGHT = 16

# =============================================================================
# ENEMY DEFINITIONS
# =============================================================================
# Dictionary of enemy types with their properties for easy spawning

ENEMY_TYPES = {
    "orc": {
        "sprite": SPRITE_ORC,
        "color": COLOR_ORC,
        "name": "Orc",
        "hp": 10,
        "power": 3,
        "defense": 0,
    },
    "troll": {
        "sprite": SPRITE_TROLL,
        "color": COLOR_TROLL,
        "name": "Troll",
        "hp": 16,
        "power": 4,
        "defense": 1,
    },
    "goblin": {
        "sprite": SPRITE_GOBLIN,
        "color": COLOR_GOBLIN,
        "name": "Goblin",
        "hp": 6,
        "power": 2,
        "defense": 0,
    },
}
