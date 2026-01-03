"""
entities.py - Player and Enemy Entity Definitions

Defines the game actors with stats, rendering, and basic behaviors.
Uses composition with McRogueFace Entity objects for rendering.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, TYPE_CHECKING
import mcrfpy

from constants import (
    PLAYER_START_HP, PLAYER_START_ATTACK, PLAYER_START_DEFENSE,
    SPRITE_PLAYER, ENEMY_STATS, FOV_RADIUS
)

if TYPE_CHECKING:
    from dungeon import Dungeon


@dataclass
class Fighter:
    """
    Combat statistics component for entities that can fight.

    Attributes:
        hp: Current hit points
        max_hp: Maximum hit points
        attack: Attack power
        defense: Damage reduction
    """
    hp: int
    max_hp: int
    attack: int
    defense: int

    @property
    def is_alive(self) -> bool:
        """Check if this fighter is still alive."""
        return self.hp > 0

    @property
    def hp_percent(self) -> float:
        """Return HP as a percentage (0.0 to 1.0)."""
        if self.max_hp <= 0:
            return 0.0
        return self.hp / self.max_hp

    def heal(self, amount: int) -> int:
        """
        Heal by the given amount, up to max_hp.

        Returns:
            The actual amount healed.
        """
        old_hp = self.hp
        self.hp = min(self.hp + amount, self.max_hp)
        return self.hp - old_hp

    def take_damage(self, amount: int) -> int:
        """
        Take damage, reduced by defense.

        Args:
            amount: Raw damage before defense calculation

        Returns:
            The actual damage taken after defense.
        """
        # Defense reduces damage, minimum 0
        actual_damage = max(0, amount - self.defense)
        self.hp = max(0, self.hp - actual_damage)
        return actual_damage


class Actor:
    """
    Base class for all game actors (player and enemies).

    Wraps a McRogueFace Entity and adds game logic.
    """

    def __init__(self, x: int, y: int, sprite: int, name: str,
                 texture: mcrfpy.Texture, grid: mcrfpy.Grid,
                 fighter: Fighter):
        """
        Create a new actor.

        Args:
            x: Starting X position
            y: Starting Y position
            sprite: Sprite index for rendering
            name: Display name of this actor
            texture: Texture for the entity sprite
            grid: Grid to add the entity to
            fighter: Combat statistics
        """
        self.name = name
        self.fighter = fighter
        self.grid = grid
        self._x = x
        self._y = y

        # Create the McRogueFace entity
        self.entity = mcrfpy.Entity((x, y), texture, sprite)
        grid.entities.append(self.entity)

    @property
    def x(self) -> int:
        return self._x

    @x.setter
    def x(self, value: int) -> None:
        self._x = value
        self.entity.pos = (value, self._y)

    @property
    def y(self) -> int:
        return self._y

    @y.setter
    def y(self, value: int) -> None:
        self._y = value
        self.entity.pos = (self._x, value)

    @property
    def pos(self) -> Tuple[int, int]:
        return (self._x, self._y)

    @pos.setter
    def pos(self, value: Tuple[int, int]) -> None:
        self._x, self._y = value
        self.entity.pos = value

    @property
    def is_alive(self) -> bool:
        return self.fighter.is_alive

    def move(self, dx: int, dy: int) -> None:
        """Move by the given delta."""
        self.x += dx
        self.y += dy

    def move_to(self, x: int, y: int) -> None:
        """Move to an absolute position."""
        self.pos = (x, y)

    def distance_to(self, other: 'Actor') -> int:
        """Calculate Manhattan distance to another actor."""
        return abs(self.x - other.x) + abs(self.y - other.y)

    def remove(self) -> None:
        """Remove this actor's entity from the grid."""
        try:
            idx = self.entity.index()
            self.grid.entities.remove(idx)
        except (ValueError, RuntimeError):
            pass  # Already removed


class Player(Actor):
    """
    The player character with additional player-specific functionality.
    """

    def __init__(self, x: int, y: int, texture: mcrfpy.Texture,
                 grid: mcrfpy.Grid):
        fighter = Fighter(
            hp=PLAYER_START_HP,
            max_hp=PLAYER_START_HP,
            attack=PLAYER_START_ATTACK,
            defense=PLAYER_START_DEFENSE
        )
        super().__init__(
            x=x, y=y,
            sprite=SPRITE_PLAYER,
            name="Player",
            texture=texture,
            grid=grid,
            fighter=fighter
        )
        self.xp = 0
        self.level = 1
        self.dungeon_level = 1

    def gain_xp(self, amount: int) -> bool:
        """
        Gain experience points.

        Args:
            amount: XP to gain

        Returns:
            True if the player leveled up
        """
        self.xp += amount
        xp_to_level = self.xp_for_next_level

        if self.xp >= xp_to_level:
            self.level_up()
            return True
        return False

    @property
    def xp_for_next_level(self) -> int:
        """XP required for the next level."""
        return self.level * 100

    def level_up(self) -> None:
        """Level up the player, improving stats."""
        self.level += 1

        # Improve stats
        hp_increase = 5
        attack_increase = 1
        defense_increase = 1 if self.level % 3 == 0 else 0

        self.fighter.max_hp += hp_increase
        self.fighter.hp += hp_increase  # Heal the increase amount
        self.fighter.attack += attack_increase
        self.fighter.defense += defense_increase

    def update_fov(self, dungeon: 'Dungeon') -> None:
        """
        Update field of view based on player position.

        Uses entity.update_visibility() for TCOD FOV calculation.
        """
        # Update the entity's visibility data
        self.entity.update_visibility()

        # Apply FOV to dungeon tiles
        for x in range(dungeon.width):
            for y in range(dungeon.height):
                state = self.entity.at(x, y)
                tile = dungeon.get_tile(x, y)

                if tile:
                    tile.visible = state.visible
                    if state.visible:
                        tile.explored = True


class Enemy(Actor):
    """
    An enemy actor with AI behavior.
    """

    def __init__(self, x: int, y: int, enemy_type: str,
                 texture: mcrfpy.Texture, grid: mcrfpy.Grid):
        """
        Create a new enemy.

        Args:
            x: Starting X position
            y: Starting Y position
            enemy_type: Key into ENEMY_STATS dictionary
            texture: Texture for the entity sprite
            grid: Grid to add the entity to
        """
        stats = ENEMY_STATS.get(enemy_type, ENEMY_STATS['goblin'])

        fighter = Fighter(
            hp=stats['hp'],
            max_hp=stats['hp'],
            attack=stats['attack'],
            defense=stats['defense']
        )

        super().__init__(
            x=x, y=y,
            sprite=stats['sprite'],
            name=stats['name'],
            texture=texture,
            grid=grid,
            fighter=fighter
        )

        self.enemy_type = enemy_type
        self.xp_reward = stats['xp']

        # AI state
        self.target: Optional[Actor] = None
        self.path: List[Tuple[int, int]] = []


def create_player(x: int, y: int, texture: mcrfpy.Texture,
                  grid: mcrfpy.Grid) -> Player:
    """
    Factory function to create the player.

    Args:
        x: Starting X position
        y: Starting Y position
        texture: Texture for player sprite
        grid: Grid to add player to

    Returns:
        A new Player instance
    """
    return Player(x, y, texture, grid)


def create_enemy(x: int, y: int, enemy_type: str,
                 texture: mcrfpy.Texture, grid: mcrfpy.Grid) -> Enemy:
    """
    Factory function to create an enemy.

    Args:
        x: Starting X position
        y: Starting Y position
        enemy_type: Type of enemy ('goblin', 'orc', 'troll')
        texture: Texture for enemy sprite
        grid: Grid to add enemy to

    Returns:
        A new Enemy instance
    """
    return Enemy(x, y, enemy_type, texture, grid)
