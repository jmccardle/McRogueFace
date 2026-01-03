"""McRogueFace - Part 12: Experience and Leveling

Documentation: https://mcrogueface.github.io/tutorial/part_12_experience
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/tutorials/part_12_experience/part_12_experience.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy
import random
import json
import os
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

# =============================================================================
# Constants
# =============================================================================

# Sprite indices for CP437 tileset
SPRITE_WALL = 35    # '#' - wall
SPRITE_FLOOR = 46   # '.' - floor
SPRITE_PLAYER = 64  # '@' - player
SPRITE_CORPSE = 37  # '%' - remains
SPRITE_POTION = 173 # Potion sprite
SPRITE_CURSOR = 88  # 'X' - targeting cursor
SPRITE_STAIRS_DOWN = 62  # '>' - stairs down

# Enemy sprites
SPRITE_GOBLIN = 103  # 'g'
SPRITE_ORC = 111     # 'o'
SPRITE_TROLL = 116   # 't'

# Grid dimensions
GRID_WIDTH = 50
GRID_HEIGHT = 30

# Room generation parameters
ROOM_MIN_SIZE = 6
ROOM_MAX_SIZE = 12
MAX_ROOMS = 8

# FOV and targeting settings
FOV_RADIUS = 8
RANGED_ATTACK_RANGE = 6
RANGED_ATTACK_DAMAGE = 4

# Save file location
SAVE_FILE = "savegame.json"

# XP values for enemies
ENEMY_XP_VALUES = {
    "goblin": 35,
    "orc": 50,
    "troll": 100
}

# Visibility colors
COLOR_VISIBLE = mcrfpy.Color(0, 0, 0, 0)
COLOR_DISCOVERED = mcrfpy.Color(0, 0, 40, 180)
COLOR_UNKNOWN = mcrfpy.Color(0, 0, 0, 255)

# Message colors
COLOR_PLAYER_ATTACK = mcrfpy.Color(200, 200, 200)
COLOR_ENEMY_ATTACK = mcrfpy.Color(255, 150, 150)
COLOR_PLAYER_DEATH = mcrfpy.Color(255, 50, 50)
COLOR_ENEMY_DEATH = mcrfpy.Color(100, 255, 100)
COLOR_HEAL = mcrfpy.Color(100, 255, 100)
COLOR_PICKUP = mcrfpy.Color(100, 200, 255)
COLOR_INFO = mcrfpy.Color(100, 100, 255)
COLOR_WARNING = mcrfpy.Color(255, 200, 50)
COLOR_INVALID = mcrfpy.Color(255, 100, 100)
COLOR_RANGED = mcrfpy.Color(255, 255, 100)
COLOR_SAVE = mcrfpy.Color(100, 255, 200)
COLOR_DESCEND = mcrfpy.Color(200, 200, 255)
COLOR_LEVEL_UP = mcrfpy.Color(255, 255, 100)
COLOR_XP = mcrfpy.Color(200, 200, 100)

# UI Layout constants
UI_TOP_HEIGHT = 60
UI_BOTTOM_HEIGHT = 150
GAME_AREA_Y = UI_TOP_HEIGHT
GAME_AREA_HEIGHT = 768 - UI_TOP_HEIGHT - UI_BOTTOM_HEIGHT

# =============================================================================
# Game Modes
# =============================================================================

class GameMode(Enum):
    NORMAL = "normal"
    TARGETING = "targeting"

# =============================================================================
# Fighter Component with XP
# =============================================================================

@dataclass
class Fighter:
    """Combat stats for an entity with experience system."""
    hp: int
    max_hp: int
    attack: int
    defense: int
    name: str
    is_player: bool = False
    xp: int = 0
    level: int = 1

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    @property
    def xp_to_next_level(self) -> int:
        """Calculate XP needed to reach the next level."""
        return self.level * 100

    @property
    def xp_progress(self) -> float:
        """Get XP progress as a percentage (0.0 to 1.0)."""
        return self.xp / self.xp_to_next_level if self.xp_to_next_level > 0 else 0

    def take_damage(self, amount: int) -> int:
        actual_damage = min(self.hp, amount)
        self.hp -= actual_damage
        return actual_damage

    def heal(self, amount: int) -> int:
        actual_heal = min(self.max_hp - self.hp, amount)
        self.hp += actual_heal
        return actual_heal

    def gain_xp(self, amount: int) -> bool:
        """Add XP and check for level up.

        Args:
            amount: XP to add

        Returns:
            True if leveled up, False otherwise
        """
        self.xp += amount

        if self.xp >= self.xp_to_next_level:
            self.level_up()
            return True

        return False

    def level_up(self) -> None:
        """Level up the character, increasing stats."""
        # Subtract XP cost (excess carries over)
        self.xp -= self.xp_to_next_level

        self.level += 1

        # Stat increases
        hp_increase = 5
        attack_increase = 1
        defense_increase = 1 if self.level % 3 == 0 else 0  # Every 3rd level

        self.max_hp += hp_increase
        self.hp = self.max_hp  # Full heal on level up!
        self.attack += attack_increase
        self.defense += defense_increase

    def to_dict(self) -> dict:
        return {
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "defense": self.defense,
            "name": self.name,
            "is_player": self.is_player,
            "xp": self.xp,
            "level": self.level
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Fighter":
        return cls(
            hp=data["hp"],
            max_hp=data["max_hp"],
            attack=data["attack"],
            defense=data["defense"],
            name=data["name"],
            is_player=data.get("is_player", False),
            xp=data.get("xp", 0),
            level=data.get("level", 1)
        )

# =============================================================================
# Item Component
# =============================================================================

@dataclass
class Item:
    """Data for an item that can be picked up and used."""
    name: str
    item_type: str
    heal_amount: int = 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "item_type": self.item_type,
            "heal_amount": self.heal_amount
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        return cls(
            name=data["name"],
            item_type=data["item_type"],
            heal_amount=data.get("heal_amount", 0)
        )

# =============================================================================
# Inventory System
# =============================================================================

@dataclass
class Inventory:
    """Container for items the player is carrying."""
    capacity: int = 10
    items: list = field(default_factory=list)

    def add(self, item: Item) -> bool:
        if len(self.items) >= self.capacity:
            return False
        self.items.append(item)
        return True

    def remove(self, index: int) -> Optional[Item]:
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None

    def get(self, index: int) -> Optional[Item]:
        if 0 <= index < len(self.items):
            return self.items[index]
        return None

    def is_full(self) -> bool:
        return len(self.items) >= self.capacity

    def count(self) -> int:
        return len(self.items)

    def to_dict(self) -> dict:
        return {
            "capacity": self.capacity,
            "items": [item.to_dict() for item in self.items]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Inventory":
        inv = cls(capacity=data.get("capacity", 10))
        inv.items = [Item.from_dict(item_data) for item_data in data.get("items", [])]
        return inv

# =============================================================================
# Templates
# =============================================================================

ITEM_TEMPLATES = {
    "health_potion": {
        "name": "Health Potion",
        "sprite": SPRITE_POTION,
        
        "item_type": "health_potion",
        "heal_amount": 10
    },
    "greater_health_potion": {
        "name": "Greater Health Potion",
        "sprite": SPRITE_POTION,
        
        "item_type": "health_potion",
        "heal_amount": 20
    }
}

ENEMY_TEMPLATES = {
    "goblin": {
        "sprite": SPRITE_GOBLIN,
        "hp": 6,
        "attack": 3,
        "defense": 0,
        "color": mcrfpy.Color(100, 200, 100)
    },
    "orc": {
        "sprite": SPRITE_ORC,
        "hp": 10,
        "attack": 4,
        "defense": 1,
        "color": mcrfpy.Color(100, 150, 100)
    },
    "troll": {
        "sprite": SPRITE_TROLL,
        "hp": 16,
        "attack": 6,
        "defense": 2,
        "color": mcrfpy.Color(50, 150, 50)
    }
}

# =============================================================================
# Difficulty Scaling
# =============================================================================

def get_max_enemies_per_room(level: int) -> int:
    return min(2 + level, 6)

def get_max_items_per_room(level: int) -> int:
    return min(1 + level // 2, 3)

def get_enemy_weights(level: int) -> list[tuple[str, float]]:
    if level <= 2:
        return [("goblin", 0.8), ("orc", 0.95), ("troll", 1.0)]
    elif level <= 4:
        return [("goblin", 0.5), ("orc", 0.85), ("troll", 1.0)]
    else:
        return [("goblin", 0.3), ("orc", 0.6), ("troll", 1.0)]

def get_item_weights(level: int) -> list[tuple[str, float]]:
    if level <= 2:
        return [("health_potion", 1.0)]
    else:
        return [("health_potion", 0.7), ("greater_health_potion", 1.0)]

# =============================================================================
# Message Log System
# =============================================================================

class MessageLog:
    """A message log that displays recent game messages with colors."""

    def __init__(self, x: int, y: int, width: int, height: int, max_messages: int = 6):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_messages = max_messages
        self.messages: list[tuple[str, mcrfpy.Color]] = []
        self.captions: list[mcrfpy.Caption] = []

        self.frame = mcrfpy.Frame(
            pos=(x, y),
            size=(width, height)
        )
        self.frame.fill_color = mcrfpy.Color(20, 20, 30, 200)
        self.frame.outline = 2
        self.frame.outline_color = mcrfpy.Color(80, 80, 100)

        line_height = 20
        for i in range(max_messages):
            caption = mcrfpy.Caption(
                pos=(x + 10, y + 5 + i * line_height),
                text=""
            )
            caption.font_size = 14
            caption.fill_color = mcrfpy.Color(200, 200, 200)
            self.captions.append(caption)

    def add_to_scene(self, scene: mcrfpy.Scene) -> None:
        scene.children.append(self.frame)
        for caption in self.captions:
            scene.children.append(caption)

    def add(self, text: str, color: mcrfpy.Color = None) -> None:
        if color is None:
            color = mcrfpy.Color(200, 200, 200)

        self.messages.append((text, color))

        while len(self.messages) > self.max_messages:
            self.messages.pop(0)

        self._refresh()

    def _refresh(self) -> None:
        for i, caption in enumerate(self.captions):
            if i < len(self.messages):
                text, color = self.messages[i]
                caption.text = text
                caption.fill_color = color
            else:
                caption.text = ""

    def clear(self) -> None:
        self.messages.clear()
        self._refresh()

# =============================================================================
# Health Bar System
# =============================================================================

class HealthBar:
    """A visual health bar using nested frames."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_hp = 30
        self.current_hp = 30

        self.bg_frame = mcrfpy.Frame(
            pos=(x, y),
            size=(width, height)
        )
        self.bg_frame.fill_color = mcrfpy.Color(80, 0, 0)
        self.bg_frame.outline = 2
        self.bg_frame.outline_color = mcrfpy.Color(150, 150, 150)

        self.fg_frame = mcrfpy.Frame(
            pos=(x + 2, y + 2),
            size=(width - 4, height - 4)
        )
        self.fg_frame.fill_color = mcrfpy.Color(0, 180, 0)
        self.fg_frame.outline = 0

        self.label = mcrfpy.Caption(
            pos=(x + 5, y + 2),
            text=f"HP: {self.current_hp}/{self.max_hp}"
        )
        self.label.font_size = 16
        self.label.fill_color = mcrfpy.Color(255, 255, 255)

    def add_to_scene(self, scene: mcrfpy.Scene) -> None:
        scene.children.append(self.bg_frame)
        scene.children.append(self.fg_frame)
        scene.children.append(self.label)

    def update(self, current_hp: int, max_hp: int) -> None:
        self.current_hp = current_hp
        self.max_hp = max_hp

        percent = max(0, current_hp / max_hp) if max_hp > 0 else 0

        inner_width = self.width - 4
        self.fg_frame.resize(int(inner_width * percent), self.height - 4)

        self.label.text = f"HP: {current_hp}/{max_hp}"

        if percent > 0.6:
            self.fg_frame.fill_color = mcrfpy.Color(0, 180, 0)
        elif percent > 0.3:
            self.fg_frame.fill_color = mcrfpy.Color(180, 180, 0)
        else:
            self.fg_frame.fill_color = mcrfpy.Color(180, 0, 0)

# =============================================================================
# XP Bar System
# =============================================================================

class XPBar:
    """A visual XP bar showing progress to next level."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.bg_frame = mcrfpy.Frame(
            pos=(x, y),
            size=(width, height)
        )
        self.bg_frame.fill_color = mcrfpy.Color(40, 40, 80)
        self.bg_frame.outline = 2
        self.bg_frame.outline_color = mcrfpy.Color(100, 100, 150)

        self.fg_frame = mcrfpy.Frame(
            pos=(x + 2, y + 2),
            size=(0, height - 4)
        )
        self.fg_frame.fill_color = mcrfpy.Color(200, 200, 50)
        self.fg_frame.outline = 0

        self.label = mcrfpy.Caption(
            pos=(x + 5, y + 1),
            text="Level 1 | XP: 0/100"
        )
        self.label.font_size = 14
        self.label.fill_color = mcrfpy.Color(255, 255, 255)

    def add_to_scene(self, scene: mcrfpy.Scene) -> None:
        scene.children.append(self.bg_frame)
        scene.children.append(self.fg_frame)
        scene.children.append(self.label)

    def update(self, level: int, xp: int, xp_to_next: int) -> None:
        """Update the XP bar display.

        Args:
            level: Current player level
            xp: Current XP
            xp_to_next: XP needed to reach next level
        """
        percent = xp / xp_to_next if xp_to_next > 0 else 0
        percent = min(1.0, max(0.0, percent))

        inner_width = self.width - 4
        self.fg_frame.resize(int(inner_width * percent), self.height - 4)

        self.label.text = f"Level {level} | XP: {xp}/{xp_to_next}"

# =============================================================================
# Inventory Panel
# =============================================================================

class InventoryPanel:
    """A panel displaying the player's inventory."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.captions: list[mcrfpy.Caption] = []

        self.frame = mcrfpy.Frame(
            pos=(x, y),
            size=(width, height)
        )
        self.frame.fill_color = mcrfpy.Color(20, 20, 30, 200)
        self.frame.outline = 2
        self.frame.outline_color = mcrfpy.Color(80, 80, 100)

        self.title = mcrfpy.Caption(
            pos=(x + 10, y + 5),
            text="Inventory (G:pickup, 1-5:use)"
        )
        self.title.font_size = 14
        self.title.fill_color = mcrfpy.Color(200, 200, 255)

        for i in range(5):
            caption = mcrfpy.Caption(
                pos=(x + 10, y + 25 + i * 18),
                text=""
            )
            caption.font_size = 13
            caption.fill_color = mcrfpy.Color(180, 180, 180)
            self.captions.append(caption)

    def add_to_scene(self, scene: mcrfpy.Scene) -> None:
        scene.children.append(self.frame)
        scene.children.append(self.title)
        for caption in self.captions:
            scene.children.append(caption)

    def update(self, inventory: Inventory) -> None:
        for i, caption in enumerate(self.captions):
            if i < len(inventory.items):
                item = inventory.items[i]
                caption.text = f"{i+1}. {item.name}"
                caption.fill_color = mcrfpy.Color(180, 180, 180)
            else:
                caption.text = f"{i+1}. ---"
                caption.fill_color = mcrfpy.Color(80, 80, 80)

# =============================================================================
# Stats Panel
# =============================================================================

class StatsPanel:
    """A panel displaying player stats."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.frame = mcrfpy.Frame(
            pos=(x, y),
            size=(width, height)
        )
        self.frame.fill_color = mcrfpy.Color(20, 20, 30, 200)
        self.frame.outline = 2
        self.frame.outline_color = mcrfpy.Color(80, 80, 100)

        self.title = mcrfpy.Caption(
            pos=(x + 10, y + 5),
            text="Stats"
        )
        self.title.font_size = 14
        self.title.fill_color = mcrfpy.Color(200, 200, 255)

        self.attack_label = mcrfpy.Caption(
            pos=(x + 10, y + 25),
            text="Attack: 5"
        )
        self.attack_label.font_size = 13
        self.attack_label.fill_color = mcrfpy.Color(255, 150, 150)

        self.defense_label = mcrfpy.Caption(
            pos=(x + 10, y + 43),
            text="Defense: 2"
        )
        self.defense_label.font_size = 13
        self.defense_label.fill_color = mcrfpy.Color(150, 150, 255)

    def add_to_scene(self, scene: mcrfpy.Scene) -> None:
        scene.children.append(self.frame)
        scene.children.append(self.title)
        scene.children.append(self.attack_label)
        scene.children.append(self.defense_label)

    def update(self, attack: int, defense: int) -> None:
        self.attack_label.text = f"Attack: {attack}"
        self.defense_label.text = f"Defense: {defense}"

# =============================================================================
# Level Display
# =============================================================================

class LevelDisplay:
    """Displays current dungeon level."""

    def __init__(self, x: int, y: int):
        self.caption = mcrfpy.Caption(
            pos=(x, y),
            text="Dungeon Level: 1"
        )
        self.caption.font_size = 16
        self.caption.fill_color = mcrfpy.Color(200, 200, 255)

    def add_to_scene(self, scene: mcrfpy.Scene) -> None:
        scene.children.append(self.caption)

    def update(self, level: int) -> None:
        self.caption.text = f"Dungeon: {level}"

# =============================================================================
# Mode Display
# =============================================================================

class ModeDisplay:
    """Displays the current game mode."""

    def __init__(self, x: int, y: int):
        self.caption = mcrfpy.Caption(
            pos=(x, y),
            text="[NORMAL MODE]"
        )
        self.caption.font_size = 16
        self.caption.fill_color = mcrfpy.Color(100, 255, 100)

    def add_to_scene(self, scene: mcrfpy.Scene) -> None:
        scene.children.append(self.caption)

    def update(self, mode: GameMode) -> None:
        if mode == GameMode.NORMAL:
            self.caption.text = "[NORMAL] F:Ranged | >:Descend"
            self.caption.fill_color = mcrfpy.Color(100, 255, 100)
        elif mode == GameMode.TARGETING:
            self.caption.text = "[TARGETING] Arrows:Move, Enter:Fire, Esc:Cancel"
            self.caption.fill_color = mcrfpy.Color(255, 255, 100)

# =============================================================================
# Global State
# =============================================================================

entity_data: dict[mcrfpy.Entity, Fighter] = {}
item_data: dict[mcrfpy.Entity, Item] = {}

player: Optional[mcrfpy.Entity] = None
player_inventory: Optional[Inventory] = None
grid: Optional[mcrfpy.Grid] = None
fov_layer = None
texture: Optional[mcrfpy.Texture] = None
game_over: bool = False
dungeon_level: int = 1
stairs_position: tuple[int, int] = (0, 0)

game_mode: GameMode = GameMode.NORMAL
target_cursor: Optional[mcrfpy.Entity] = None
target_x: int = 0
target_y: int = 0

# UI components
message_log: Optional[MessageLog] = None
health_bar: Optional[HealthBar] = None
xp_bar: Optional[XPBar] = None
inventory_panel: Optional[InventoryPanel] = None
stats_panel: Optional[StatsPanel] = None
mode_display: Optional[ModeDisplay] = None
level_display: Optional[LevelDisplay] = None

# =============================================================================
# Room Class
# =============================================================================

class RectangularRoom:
    """A rectangular room with its position and size."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> tuple[int, int]:
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return center_x, center_y

    @property
    def inner(self) -> tuple[slice, slice]:
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: "RectangularRoom") -> bool:
        return (
            self.x1 <= other.x2 and
            self.x2 >= other.x1 and
            self.y1 <= other.y2 and
            self.y2 >= other.y1
        )

# =============================================================================
# Exploration Tracking
# =============================================================================

explored: list[list[bool]] = []

def init_explored() -> None:
    global explored
    explored = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

def mark_explored(x: int, y: int) -> None:
    if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
        explored[y][x] = True

def is_explored(x: int, y: int) -> bool:
    if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
        return explored[y][x]
    return False

# =============================================================================
# Dungeon Generation
# =============================================================================

def fill_with_walls(target_grid: mcrfpy.Grid) -> None:
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            cell = target_grid.at(x, y)
            cell.tilesprite = SPRITE_WALL
            cell.walkable = False
            cell.transparent = False

def carve_room(target_grid: mcrfpy.Grid, room: RectangularRoom) -> None:
    inner_x, inner_y = room.inner
    for y in range(inner_y.start, inner_y.stop):
        for x in range(inner_x.start, inner_x.stop):
            if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                cell = target_grid.at(x, y)
                cell.tilesprite = SPRITE_FLOOR
                cell.walkable = True
                cell.transparent = True

def carve_tunnel_horizontal(target_grid: mcrfpy.Grid, x1: int, x2: int, y: int) -> None:
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
            cell = target_grid.at(x, y)
            cell.tilesprite = SPRITE_FLOOR
            cell.walkable = True
            cell.transparent = True

def carve_tunnel_vertical(target_grid: mcrfpy.Grid, y1: int, y2: int, x: int) -> None:
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
            cell = target_grid.at(x, y)
            cell.tilesprite = SPRITE_FLOOR
            cell.walkable = True
            cell.transparent = True

def carve_l_tunnel(
    target_grid: mcrfpy.Grid,
    start: tuple[int, int],
    end: tuple[int, int]
) -> None:
    x1, y1 = start
    x2, y2 = end

    if random.random() < 0.5:
        carve_tunnel_horizontal(target_grid, x1, x2, y1)
        carve_tunnel_vertical(target_grid, y1, y2, x2)
    else:
        carve_tunnel_vertical(target_grid, y1, y2, x1)
        carve_tunnel_horizontal(target_grid, x1, x2, y2)

def place_stairs(target_grid: mcrfpy.Grid, x: int, y: int) -> None:
    global stairs_position
    cell = target_grid.at(x, y)
    cell.tilesprite = SPRITE_STAIRS_DOWN
    cell.walkable = True
    cell.transparent = True
    stairs_position = (x, y)

def generate_dungeon(target_grid: mcrfpy.Grid, level: int) -> tuple[int, int]:
    global stairs_position
    fill_with_walls(target_grid)

    rooms: list[RectangularRoom] = []

    for _ in range(MAX_ROOMS):
        room_width = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        room_height = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x = random.randint(1, GRID_WIDTH - room_width - 2)
        y = random.randint(1, GRID_HEIGHT - room_height - 2)

        new_room = RectangularRoom(x, y, room_width, room_height)

        overlaps = False
        for other_room in rooms:
            if new_room.intersects(other_room):
                overlaps = True
                break

        if overlaps:
            continue

        carve_room(target_grid, new_room)

        if rooms:
            carve_l_tunnel(target_grid, new_room.center, rooms[-1].center)

        rooms.append(new_room)

    if rooms:
        stairs_x, stairs_y = rooms[-1].center
        place_stairs(target_grid, stairs_x, stairs_y)

    if rooms:
        return rooms[0].center
    else:
        return GRID_WIDTH // 2, GRID_HEIGHT // 2

# =============================================================================
# Entity Management
# =============================================================================

def spawn_enemy(target_grid: mcrfpy.Grid, x: int, y: int, enemy_type: str, tex: mcrfpy.Texture) -> mcrfpy.Entity:
    template = ENEMY_TEMPLATES[enemy_type]

    enemy = mcrfpy.Entity(
        grid_pos=(x, y),
        texture=tex,
        sprite_index=template["sprite"]
    )

    enemy.visible = False

    target_grid.entities.append(enemy)

    entity_data[enemy] = Fighter(
        hp=template["hp"],
        max_hp=template["hp"],
        attack=template["attack"],
        defense=template["defense"],
        name=enemy_type.capitalize(),
        is_player=False
    )

    return enemy

def spawn_item(target_grid: mcrfpy.Grid, x: int, y: int, item_type: str, tex: mcrfpy.Texture) -> mcrfpy.Entity:
    template = ITEM_TEMPLATES[item_type]

    item_entity = mcrfpy.Entity(
        grid_pos=(x, y),
        texture=tex,
        sprite_index=template["sprite"]
    )

    item_entity.visible = False

    target_grid.entities.append(item_entity)

    item_data[item_entity] = Item(
        name=template["name"],
        item_type=template["item_type"],
        heal_amount=template.get("heal_amount", 0)
    )

    return item_entity

def spawn_entities_for_level(target_grid: mcrfpy.Grid, tex: mcrfpy.Texture, level: int) -> None:
    floor_tiles = []
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            cell = target_grid.at(x, y)
            if cell.walkable and cell.tilesprite == SPRITE_FLOOR:
                floor_tiles.append((x, y))

    max_enemies = get_max_enemies_per_room(level) * 3
    enemy_weights = get_enemy_weights(level)

    for _ in range(max_enemies):
        if not floor_tiles:
            break

        x, y = random.choice(floor_tiles)

        if (x, y) == (int(player.x), int(player.y)):
            continue
        if (x, y) == stairs_position:
            continue
        if is_position_occupied(target_grid, x, y):
            continue

        roll = random.random()
        enemy_type = "goblin"
        for etype, threshold in enemy_weights:
            if roll < threshold:
                enemy_type = etype
                break

        spawn_enemy(target_grid, x, y, enemy_type, tex)

    max_items = get_max_items_per_room(level) * 2
    item_weights = get_item_weights(level)

    for _ in range(max_items):
        if not floor_tiles:
            break

        x, y = random.choice(floor_tiles)

        if (x, y) == (int(player.x), int(player.y)):
            continue
        if (x, y) == stairs_position:
            continue
        if is_position_occupied(target_grid, x, y):
            continue

        roll = random.random()
        item_type = "health_potion"
        for itype, threshold in item_weights:
            if roll < threshold:
                item_type = itype
                break

        spawn_item(target_grid, x, y, item_type, tex)

def is_position_occupied(target_grid: mcrfpy.Grid, x: int, y: int) -> bool:
    for entity in target_grid.entities:
        if int(entity.x) == x and int(entity.y) == y:
            return True
    return False

def get_item_at(target_grid: mcrfpy.Grid, x: int, y: int) -> Optional[mcrfpy.Entity]:
    for entity in target_grid.entities:
        if entity in item_data:
            if int(entity.x) == x and int(entity.y) == y:
                return entity
    return None

def get_blocking_entity_at(target_grid: mcrfpy.Grid, x: int, y: int, exclude: mcrfpy.Entity = None) -> Optional[mcrfpy.Entity]:
    for entity in target_grid.entities:
        if entity == exclude:
            continue
        if int(entity.x) == x and int(entity.y) == y:
            if entity in entity_data and entity_data[entity].is_alive:
                return entity
    return None

def remove_entity(target_grid: mcrfpy.Grid, entity: mcrfpy.Entity) -> None:
    for i, e in enumerate(target_grid.entities):
        if e == entity:
            target_grid.entities.remove(i)
            break
    if entity in entity_data:
        del entity_data[entity]

def remove_item_entity(target_grid: mcrfpy.Grid, entity: mcrfpy.Entity) -> None:
    for i, e in enumerate(target_grid.entities):
        if e == entity:
            target_grid.entities.remove(i)
            break
    if entity in item_data:
        del item_data[entity]

def clear_entities_except_player(target_grid: mcrfpy.Grid) -> None:
    global entity_data, item_data

    entities_to_remove = []
    for entity in target_grid.entities:
        if entity in entity_data and entity_data[entity].is_player:
            continue
        entities_to_remove.append(entity)

    for entity in entities_to_remove:
        if entity in entity_data:
            del entity_data[entity]
        if entity in item_data:
            del item_data[entity]

        for i, e in enumerate(target_grid.entities):
            if e == entity:
                target_grid.entities.remove(i)
                break

# =============================================================================
# XP and Level Up
# =============================================================================

def award_xp(enemy_name: str) -> None:
    """Award XP for killing an enemy.

    Args:
        enemy_name: Name of the defeated enemy
    """
    global player

    fighter = entity_data.get(player)
    if fighter is None:
        return

    enemy_type = enemy_name.lower()
    xp_amount = ENEMY_XP_VALUES.get(enemy_type, 35)

    leveled_up = fighter.gain_xp(xp_amount)

    if leveled_up:
        message_log.add(
            f"You gained {xp_amount} XP and reached level {fighter.level}!",
            COLOR_LEVEL_UP
        )
        message_log.add(
            f"HP +5, Attack +1{', Defense +1' if fighter.level % 3 == 0 else ''}!",
            COLOR_LEVEL_UP
        )
    else:
        message_log.add(f"You gain {xp_amount} XP.", COLOR_XP)

    update_ui()

# =============================================================================
# Level Transition
# =============================================================================

def descend_stairs() -> bool:
    global player, dungeon_level, grid, fov_layer, stairs_position

    px, py = int(player.x), int(player.y)

    if (px, py) != stairs_position:
        message_log.add("There are no stairs here.", COLOR_INVALID)
        return False

    dungeon_level += 1

    clear_entities_except_player(grid)

    init_explored()
    player_start = generate_dungeon(grid, dungeon_level)

    player.x = player_start[0]
    player.y = player_start[1]

    spawn_entities_for_level(grid, texture, dungeon_level)

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            fov_layer.set(x, y, COLOR_UNKNOWN)

    update_fov(grid, fov_layer, player_start[0], player_start[1])

    message_log.add(f"You descend to level {dungeon_level}...", COLOR_DESCEND)
    level_display.update(dungeon_level)
    update_ui()

    return True

# =============================================================================
# Save/Load System
# =============================================================================

def save_game() -> bool:
    global player, player_inventory, grid, explored, dungeon_level, stairs_position

    try:
        tiles = []
        for y in range(GRID_HEIGHT):
            row = []
            for x in range(GRID_WIDTH):
                cell = grid.at(x, y)
                row.append({
                    "tilesprite": cell.tilesprite,
                    "walkable": cell.walkable,
                    "transparent": cell.transparent
                })
            tiles.append(row)

        enemies = []
        for entity in grid.entities:
            if entity == player:
                continue
            if entity in entity_data:
                fighter = entity_data[entity]
                enemies.append({
                    "x": int(entity.x),
                    "y": int(entity.y),
                    "type": fighter.name.lower(),
                    "fighter": fighter.to_dict()
                })

        items_on_ground = []
        for entity in grid.entities:
            if entity in item_data:
                item = item_data[entity]
                items_on_ground.append({
                    "x": int(entity.x),
                    "y": int(entity.y),
                    "item": item.to_dict()
                })

        save_data = {
            "version": 3,
            "dungeon_level": dungeon_level,
            "stairs_position": list(stairs_position),
            "player": {
                "x": int(player.x),
                "y": int(player.y),
                "fighter": entity_data[player].to_dict(),
                "inventory": player_inventory.to_dict()
            },
            "tiles": tiles,
            "explored": [[explored[y][x] for x in range(GRID_WIDTH)] for y in range(GRID_HEIGHT)],
            "enemies": enemies,
            "items": items_on_ground
        }

        with open(SAVE_FILE, "w") as f:
            json.dump(save_data, f, indent=2)

        message_log.add("Game saved successfully!", COLOR_SAVE)
        return True

    except Exception as e:
        message_log.add(f"Failed to save: {str(e)}", COLOR_INVALID)
        return False

def load_game() -> bool:
    global player, player_inventory, grid, explored, dungeon_level
    global entity_data, item_data, fov_layer, game_over, stairs_position

    if not os.path.exists(SAVE_FILE):
        return False

    try:
        with open(SAVE_FILE, "r") as f:
            save_data = json.load(f)

        entity_data.clear()
        item_data.clear()

        while len(grid.entities) > 0:
            grid.entities.remove(0)

        dungeon_level = save_data.get("dungeon_level", 1)
        stairs_position = tuple(save_data.get("stairs_position", [0, 0]))

        tiles = save_data["tiles"]
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                cell = grid.at(x, y)
                tile_data = tiles[y][x]
                cell.tilesprite = tile_data["tilesprite"]
                cell.walkable = tile_data["walkable"]
                cell.transparent = tile_data["transparent"]

        global explored
        explored_data = save_data["explored"]
        explored = [[explored_data[y][x] for x in range(GRID_WIDTH)] for y in range(GRID_HEIGHT)]

        player_data = save_data["player"]
        player = mcrfpy.Entity(
            grid_pos=(player_data["x"], player_data["y"]),
            texture=texture,
            sprite_index=SPRITE_PLAYER
        )
        grid.entities.append(player)

        entity_data[player] = Fighter.from_dict(player_data["fighter"])
        player_inventory = Inventory.from_dict(player_data["inventory"])

        for enemy_data in save_data.get("enemies", []):
            enemy_type = enemy_data["type"]
            template = ENEMY_TEMPLATES.get(enemy_type, ENEMY_TEMPLATES["goblin"])

            enemy = mcrfpy.Entity(
                grid_pos=(enemy_data["x"], enemy_data["y"]),
                texture=texture,
                sprite_index=template["sprite"]
            )
            enemy.visible = False

            grid.entities.append(enemy)
            entity_data[enemy] = Fighter.from_dict(enemy_data["fighter"])

        for item_entry in save_data.get("items", []):
            item_type = item_entry["item"]["item_type"]
            template = ITEM_TEMPLATES.get(item_type, ITEM_TEMPLATES["health_potion"])

            item_entity = mcrfpy.Entity(
                grid_pos=(item_entry["x"], item_entry["y"]),
                texture=texture,
                sprite_index=template["sprite"]
            )
            item_entity.visible = False

            grid.entities.append(item_entity)
            item_data[item_entity] = Item.from_dict(item_entry["item"])

        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                fov_layer.set(x, y, COLOR_UNKNOWN)

        update_fov(grid, fov_layer, int(player.x), int(player.y))

        game_over = False

        message_log.add("Game loaded successfully!", COLOR_SAVE)
        level_display.update(dungeon_level)
        update_ui()
        return True

    except Exception as e:
        message_log.add(f"Failed to load: {str(e)}", COLOR_INVALID)
        return False

def delete_save() -> bool:
    try:
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)
        return True
    except Exception:
        return False

def has_save_file() -> bool:
    return os.path.exists(SAVE_FILE)

# =============================================================================
# Targeting System
# =============================================================================

def enter_targeting_mode() -> None:
    global game_mode, target_cursor, target_x, target_y, player, grid, texture

    target_x = int(player.x)
    target_y = int(player.y)

    target_cursor = mcrfpy.Entity(
        grid_pos=(target_x, target_y),
        texture=texture,
        sprite_index=SPRITE_CURSOR
    )
    grid.entities.append(target_cursor)

    game_mode = GameMode.TARGETING

    message_log.add("Targeting mode: Arrows to aim, Enter to fire, Esc to cancel.", COLOR_INFO)
    mode_display.update(game_mode)

def exit_targeting_mode() -> None:
    global game_mode, target_cursor, grid

    if target_cursor is not None:
        for i, e in enumerate(grid.entities):
            if e == target_cursor:
                grid.entities.remove(i)
                break
        target_cursor = None

    game_mode = GameMode.NORMAL
    mode_display.update(game_mode)

def move_cursor(dx: int, dy: int) -> None:
    global target_x, target_y, target_cursor, grid, player

    new_x = target_x + dx
    new_y = target_y + dy

    if new_x < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y >= GRID_HEIGHT:
        return

    if not grid.is_in_fov(new_x, new_y):
        message_log.add("You cannot see that location.", COLOR_INVALID)
        return

    player_x, player_y = int(player.x), int(player.y)
    distance = abs(new_x - player_x) + abs(new_y - player_y)
    if distance > RANGED_ATTACK_RANGE:
        message_log.add(f"Target is out of range (max {RANGED_ATTACK_RANGE}).", COLOR_WARNING)
        return

    target_x = new_x
    target_y = new_y
    target_cursor.x = target_x
    target_cursor.y = target_y

    enemy = get_blocking_entity_at(grid, target_x, target_y, exclude=player)
    if enemy and enemy in entity_data:
        fighter = entity_data[enemy]
        message_log.add(f"Target: {fighter.name} (HP: {fighter.hp}/{fighter.max_hp})", COLOR_RANGED)

def confirm_target() -> None:
    global game_mode, target_x, target_y, player, grid

    if target_x == int(player.x) and target_y == int(player.y):
        message_log.add("You cannot target yourself!", COLOR_INVALID)
        return

    target_enemy = get_blocking_entity_at(grid, target_x, target_y, exclude=player)

    if target_enemy is None or target_enemy not in entity_data:
        message_log.add("No valid target at that location.", COLOR_INVALID)
        return

    perform_ranged_attack(target_enemy)
    exit_targeting_mode()
    enemy_turn()
    update_ui()

def perform_ranged_attack(target_entity: mcrfpy.Entity) -> None:
    global player, game_over

    defender = entity_data.get(target_entity)
    attacker = entity_data.get(player)

    if defender is None or attacker is None:
        return

    damage = max(1, RANGED_ATTACK_DAMAGE - defender.defense // 2)

    defender.take_damage(damage)

    message_log.add(
        f"Your ranged attack hits the {defender.name} for {damage} damage!",
        COLOR_RANGED
    )

    if not defender.is_alive:
        handle_death(target_entity, defender)

# =============================================================================
# Combat System
# =============================================================================

def calculate_damage(attacker: Fighter, defender: Fighter) -> int:
    return max(0, attacker.attack - defender.defense)

def perform_attack(attacker_entity: mcrfpy.Entity, defender_entity: mcrfpy.Entity) -> None:
    global game_over

    attacker = entity_data.get(attacker_entity)
    defender = entity_data.get(defender_entity)

    if attacker is None or defender is None:
        return

    damage = calculate_damage(attacker, defender)
    defender.take_damage(damage)

    if damage > 0:
        if attacker.is_player:
            message_log.add(
                f"You hit the {defender.name} for {damage} damage!",
                COLOR_PLAYER_ATTACK
            )
        else:
            message_log.add(
                f"The {attacker.name} hits you for {damage} damage!",
                COLOR_ENEMY_ATTACK
            )
    else:
        if attacker.is_player:
            message_log.add(
                f"You hit the {defender.name} but deal no damage.",
                mcrfpy.Color(150, 150, 150)
            )
        else:
            message_log.add(
                f"The {attacker.name} hits but deals no damage.",
                mcrfpy.Color(150, 150, 200)
            )

    if not defender.is_alive:
        handle_death(defender_entity, defender)

    update_ui()

def handle_death(entity: mcrfpy.Entity, fighter: Fighter) -> None:
    global game_over, grid

    if fighter.is_player:
        message_log.add("You have died!", COLOR_PLAYER_DEATH)
        message_log.add("Press R to restart or Escape to quit.", COLOR_INFO)
        game_over = True
        entity.sprite_index = SPRITE_CORPSE
        delete_save()
    else:
        message_log.add(f"The {fighter.name} dies!", COLOR_ENEMY_DEATH)
        # Award XP before removing the entity
        award_xp(fighter.name)
        remove_entity(grid, entity)

# =============================================================================
# Item Actions
# =============================================================================

def pickup_item() -> bool:
    global player, player_inventory, grid

    px, py = int(player.x), int(player.y)
    item_entity = get_item_at(grid, px, py)

    if item_entity is None:
        message_log.add("There is nothing to pick up here.", COLOR_INVALID)
        return False

    if player_inventory.is_full():
        message_log.add("Your inventory is full!", COLOR_WARNING)
        return False

    item = item_data.get(item_entity)
    if item is None:
        return False

    player_inventory.add(item)
    remove_item_entity(grid, item_entity)

    message_log.add(f"You pick up the {item.name}.", COLOR_PICKUP)

    update_ui()
    return True

def use_item(index: int) -> bool:
    global player, player_inventory

    item = player_inventory.get(index)
    if item is None:
        message_log.add("Invalid item selection.", COLOR_INVALID)
        return False

    if item.item_type == "health_potion":
        fighter = entity_data.get(player)
        if fighter is None:
            return False

        if fighter.hp >= fighter.max_hp:
            message_log.add("You are already at full health!", COLOR_WARNING)
            return False

        actual_heal = fighter.heal(item.heal_amount)
        player_inventory.remove(index)

        message_log.add(f"You drink the {item.name} and recover {actual_heal} HP!", COLOR_HEAL)

        update_ui()
        return True

    message_log.add(f"You cannot use the {item.name}.", COLOR_INVALID)
    return False

# =============================================================================
# Field of View
# =============================================================================

def update_entity_visibility(target_grid: mcrfpy.Grid) -> None:
    global player, target_cursor

    for entity in target_grid.entities:
        if entity == player:
            entity.visible = True
            continue

        if entity == target_cursor:
            entity.visible = True
            continue

        ex, ey = int(entity.x), int(entity.y)
        entity.visible = target_grid.is_in_fov(ex, ey)

def update_fov(target_grid: mcrfpy.Grid, target_fov_layer, player_x: int, player_y: int) -> None:
    target_grid.compute_fov(player_x, player_y, FOV_RADIUS, mcrfpy.FOV.SHADOW)

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if target_grid.is_in_fov(x, y):
                mark_explored(x, y)
                target_fov_layer.set(x, y, COLOR_VISIBLE)
            elif is_explored(x, y):
                target_fov_layer.set(x, y, COLOR_DISCOVERED)
            else:
                target_fov_layer.set(x, y, COLOR_UNKNOWN)

    update_entity_visibility(target_grid)

# =============================================================================
# Movement and Actions
# =============================================================================

def can_move_to(target_grid: mcrfpy.Grid, x: int, y: int, mover: mcrfpy.Entity = None) -> bool:
    if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
        return False

    if not target_grid.at(x, y).walkable:
        return False

    blocker = get_blocking_entity_at(target_grid, x, y, exclude=mover)
    if blocker is not None:
        return False

    return True

def try_move_or_attack(dx: int, dy: int) -> None:
    global player, grid, fov_layer, game_over

    if game_over:
        return

    px, py = int(player.x), int(player.y)
    new_target_x = px + dx
    new_target_y = py + dy

    if new_target_x < 0 or new_target_x >= GRID_WIDTH or new_target_y < 0 or new_target_y >= GRID_HEIGHT:
        return

    blocker = get_blocking_entity_at(grid, new_target_x, new_target_y, exclude=player)

    if blocker is not None:
        perform_attack(player, blocker)
        enemy_turn()
    elif grid.at(new_target_x, new_target_y).walkable:
        player.x = new_target_x
        player.y = new_target_y
        update_fov(grid, fov_layer, new_target_x, new_target_y)
        enemy_turn()

    update_ui()

# =============================================================================
# Enemy AI
# =============================================================================

def enemy_turn() -> None:
    global player, grid, game_over

    if game_over:
        return

    player_x, player_y = int(player.x), int(player.y)

    enemies = []
    for entity in grid.entities:
        if entity == player:
            continue
        if entity in entity_data and entity_data[entity].is_alive:
            enemies.append(entity)

    for enemy in enemies:
        fighter = entity_data.get(enemy)
        if fighter is None or not fighter.is_alive:
            continue

        ex, ey = int(enemy.x), int(enemy.y)

        if not grid.is_in_fov(ex, ey):
            continue

        dx = player_x - ex
        dy = player_y - ey

        if abs(dx) <= 1 and abs(dy) <= 1 and (dx != 0 or dy != 0):
            perform_attack(enemy, player)
        else:
            move_toward_player(enemy, ex, ey, player_x, player_y)

def move_toward_player(enemy: mcrfpy.Entity, ex: int, ey: int, px: int, py: int) -> None:
    global grid

    dx = 0
    dy = 0

    if px < ex:
        dx = -1
    elif px > ex:
        dx = 1

    if py < ey:
        dy = -1
    elif py > ey:
        dy = 1

    new_x = ex + dx
    new_y = ey + dy

    if can_move_to(grid, new_x, new_y, enemy):
        enemy.x = new_x
        enemy.y = new_y
    elif dx != 0 and can_move_to(grid, ex + dx, ey, enemy):
        enemy.x = ex + dx
    elif dy != 0 and can_move_to(grid, ex, ey + dy, enemy):
        enemy.y = ey + dy

# =============================================================================
# UI Updates
# =============================================================================

def update_ui() -> None:
    global player, health_bar, xp_bar, inventory_panel, stats_panel, player_inventory

    if player in entity_data:
        fighter = entity_data[player]
        health_bar.update(fighter.hp, fighter.max_hp)
        xp_bar.update(fighter.level, fighter.xp, fighter.xp_to_next_level)
        stats_panel.update(fighter.attack, fighter.defense)

    if player_inventory:
        inventory_panel.update(player_inventory)

# =============================================================================
# New Game Generation
# =============================================================================

def generate_new_game() -> None:
    global player, player_inventory, grid, fov_layer, game_over
    global entity_data, item_data, dungeon_level, game_mode

    game_over = False
    game_mode = GameMode.NORMAL
    dungeon_level = 1

    entity_data.clear()
    item_data.clear()

    while len(grid.entities) > 0:
        grid.entities.remove(0)

    init_explored()
    message_log.clear()

    player_start = generate_dungeon(grid, dungeon_level)

    player = mcrfpy.Entity(
        grid_pos=(player_start[0], player_start[1]),
        texture=texture,
        sprite_index=SPRITE_PLAYER
    )
    grid.entities.append(player)

    entity_data[player] = Fighter(
        hp=30,
        max_hp=30,
        attack=5,
        defense=2,
        name="Player",
        is_player=True,
        xp=0,
        level=1
    )

    player_inventory = Inventory(capacity=10)

    spawn_entities_for_level(grid, texture, dungeon_level)

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            fov_layer.set(x, y, COLOR_UNKNOWN)

    update_fov(grid, fov_layer, player_start[0], player_start[1])

    mode_display.update(game_mode)
    level_display.update(dungeon_level)
    update_ui()

# =============================================================================
# Game Setup
# =============================================================================

scene = mcrfpy.Scene("game")
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

grid = mcrfpy.Grid(
    pos=(20, GAME_AREA_Y),
    size=(700, GAME_AREA_HEIGHT - 20),
    grid_size=(GRID_WIDTH, GRID_HEIGHT),
    texture=texture,
    zoom=1.0
)

fov_layer = grid.add_layer("color", z_index=-1)
for y in range(GRID_HEIGHT):
    for x in range(GRID_WIDTH):
        fov_layer.set(x, y, COLOR_UNKNOWN)

scene.children.append(grid)

# =============================================================================
# Create UI Elements
# =============================================================================

title = mcrfpy.Caption(
    pos=(20, 10),
    text="Part 12: Experience System"
)
title.fill_color = mcrfpy.Color(255, 255, 255)
title.font_size = 24
scene.children.append(title)

instructions = mcrfpy.Caption(
    pos=(300, 15),
    text="WASD:Move | >:Descend | F:Ranged | G:Pickup"
)
instructions.fill_color = mcrfpy.Color(180, 180, 180)
instructions.font_size = 14
scene.children.append(instructions)

health_bar = HealthBar(x=730, y=10, width=280, height=25)
health_bar.add_to_scene(scene)

xp_bar = XPBar(x=730, y=40, width=280, height=20)
xp_bar.add_to_scene(scene)

level_display = LevelDisplay(x=860, y=65)
level_display.add_to_scene(scene)

mode_display = ModeDisplay(x=20, y=40)
mode_display.add_to_scene(scene)

stats_panel = StatsPanel(x=730, y=GAME_AREA_Y, width=140, height=70)
stats_panel.add_to_scene(scene)

inventory_panel = InventoryPanel(x=730, y=GAME_AREA_Y + 75, width=280, height=120)
inventory_panel.add_to_scene(scene)

message_log = MessageLog(
    x=20,
    y=768 - UI_BOTTOM_HEIGHT + 10,
    width=990,
    height=UI_BOTTOM_HEIGHT - 20,
    max_messages=6
)
message_log.add_to_scene(scene)

# =============================================================================
# Initialize Game
# =============================================================================

init_explored()

if has_save_file():
    message_log.add("Found saved game. Loading...", COLOR_INFO)
    if not load_game():
        message_log.add("Failed to load. Starting new game.", COLOR_WARNING)
        generate_new_game()
        message_log.add("Welcome to the dungeon!", COLOR_INFO)
else:
    generate_new_game()
    message_log.add("Welcome to the dungeon!", COLOR_INFO)
    message_log.add("Kill enemies to gain XP and level up!", COLOR_INFO)

# =============================================================================
# Input Handling
# =============================================================================

def handle_keys(key: str, action: str) -> None:
    global game_over, game_mode

    if action != "start":
        return

    if key == "R":
        delete_save()
        generate_new_game()
        message_log.add("A new adventure begins!", COLOR_INFO)
        return

    if key == "Escape":
        if game_mode == GameMode.TARGETING:
            exit_targeting_mode()
            message_log.add("Targeting cancelled.", COLOR_INFO)
            return
        else:
            if not game_over:
                save_game()
            mcrfpy.exit()
            return

    if key == "Period" and game_mode == GameMode.NORMAL and not game_over:
        # Check for shift to descend
        descend_stairs()
        return

    if game_over:
        return

    if game_mode == GameMode.TARGETING:
        handle_targeting_input(key)
    else:
        handle_normal_input(key)

def handle_normal_input(key: str) -> None:
    if key == "W" or key == "Up":
        try_move_or_attack(0, -1)
    elif key == "S" or key == "Down":
        try_move_or_attack(0, 1)
    elif key == "A" or key == "Left":
        try_move_or_attack(-1, 0)
    elif key == "D" or key == "Right":
        try_move_or_attack(1, 0)
    elif key == "F":
        enter_targeting_mode()
    elif key == "G" or key == ",":
        pickup_item()
    elif key in ["1", "2", "3", "4", "5"]:
        index = int(key) - 1
        if use_item(index):
            enemy_turn()
            update_ui()

def handle_targeting_input(key: str) -> None:
    if key == "Up" or key == "W":
        move_cursor(0, -1)
    elif key == "Down" or key == "S":
        move_cursor(0, 1)
    elif key == "Left" or key == "A":
        move_cursor(-1, 0)
    elif key == "Right" or key == "D":
        move_cursor(1, 0)
    elif key == "Return" or key == "Space":
        confirm_target()

scene.on_key = handle_keys

# =============================================================================
# Start the Game
# =============================================================================

scene.activate()
print("Part 12 loaded! Kill enemies to gain XP and level up!")