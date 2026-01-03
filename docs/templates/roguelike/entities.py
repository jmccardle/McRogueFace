"""
entities.py - Entity Management for Roguelike Template

This module provides entity creation and management utilities for the
roguelike template. Entities in McRogueFace are game objects that exist
on a Grid, such as the player, enemies, items, and NPCs.

The module includes:
- Entity factory functions for creating common entity types
- Helper functions for entity management
- Simple data containers for entity stats (for future expansion)

Note: McRogueFace entities are simple position + sprite objects. For
complex game logic like AI, combat, and inventory, you'll want to wrap
them in Python classes that reference the underlying Entity.
"""

from __future__ import annotations
from typing import Tuple, Optional, List, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    import mcrfpy

from constants import (
    SPRITE_PLAYER, SPRITE_ORC, SPRITE_TROLL, SPRITE_GOBLIN,
    COLOR_PLAYER, COLOR_ORC, COLOR_TROLL, COLOR_GOBLIN,
    ENEMY_TYPES,
)


@dataclass
class EntityStats:
    """
    Optional stats container for game entities.

    This dataclass can be used to track stats for entities that need them.
    Attach it to your entity wrapper class for combat, leveling, etc.

    Attributes:
        hp: Current hit points
        max_hp: Maximum hit points
        power: Attack power
        defense: Damage reduction
        name: Display name for the entity
    """
    hp: int = 10
    max_hp: int = 10
    power: int = 3
    defense: int = 0
    name: str = "Unknown"

    @property
    def is_alive(self) -> bool:
        """Check if the entity is still alive."""
        return self.hp > 0

    def take_damage(self, amount: int) -> int:
        """
        Apply damage, accounting for defense.

        Args:
            amount: Raw damage amount

        Returns:
            Actual damage dealt after defense
        """
        actual_damage = max(0, amount - self.defense)
        self.hp = max(0, self.hp - actual_damage)
        return actual_damage

    def heal(self, amount: int) -> int:
        """
        Heal the entity.

        Args:
            amount: Amount to heal

        Returns:
            Actual amount healed (may be less if near max HP)
        """
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp


def create_player(
    grid: mcrfpy.Grid,
    texture: mcrfpy.Texture,
    x: int,
    y: int
) -> mcrfpy.Entity:
    """
    Create and place the player entity on the grid.

    The player uses the classic '@' symbol (sprite index 64 in CP437).

    Args:
        grid: The Grid to place the player on
        texture: The texture/tileset to use
        x: Starting X position
        y: Starting Y position

    Returns:
        The created player Entity
    """
    import mcrfpy

    player = mcrfpy.Entity(
        pos=(x, y),
        texture=texture,
        sprite_index=SPRITE_PLAYER
    )
    grid.entities.append(player)

    return player


def create_enemy(
    grid: mcrfpy.Grid,
    texture: mcrfpy.Texture,
    x: int,
    y: int,
    enemy_type: str = "orc"
) -> Tuple[mcrfpy.Entity, EntityStats]:
    """
    Create an enemy entity with associated stats.

    Enemy types are defined in constants.py. Currently available:
    - "orc": Standard enemy, balanced stats
    - "troll": Tough enemy, high HP and power
    - "goblin": Weak enemy, low stats

    Args:
        grid: The Grid to place the enemy on
        texture: The texture/tileset to use
        x: X position
        y: Y position
        enemy_type: Key from ENEMY_TYPES dict

    Returns:
        Tuple of (Entity, EntityStats) for the created enemy
    """
    import mcrfpy

    # Get enemy definition, default to orc if not found
    enemy_def = ENEMY_TYPES.get(enemy_type, ENEMY_TYPES["orc"])

    entity = mcrfpy.Entity(
        pos=(x, y),
        texture=texture,
        sprite_index=enemy_def["sprite"]
    )
    grid.entities.append(entity)

    stats = EntityStats(
        hp=enemy_def["hp"],
        max_hp=enemy_def["hp"],
        power=enemy_def["power"],
        defense=enemy_def["defense"],
        name=enemy_def["name"]
    )

    return entity, stats


def create_enemies_in_rooms(
    grid: mcrfpy.Grid,
    texture: mcrfpy.Texture,
    rooms: list,
    enemies_per_room: int = 2,
    skip_first_room: bool = True
) -> List[Tuple[mcrfpy.Entity, EntityStats]]:
    """
    Populate dungeon rooms with enemies.

    This helper function places random enemies throughout the dungeon,
    typically skipping the first room (where the player starts).

    Args:
        grid: The Grid to populate
        texture: The texture/tileset to use
        rooms: List of RectangularRoom objects from dungeon generation
        enemies_per_room: Maximum enemies to spawn per room
        skip_first_room: If True, don't spawn enemies in the first room

    Returns:
        List of (Entity, EntityStats) tuples for all created enemies
    """
    import random

    enemies = []
    enemy_type_keys = list(ENEMY_TYPES.keys())

    # Iterate through rooms, optionally skipping the first
    rooms_to_populate = rooms[1:] if skip_first_room else rooms

    for room in rooms_to_populate:
        # Random number of enemies (0 to enemies_per_room)
        num_enemies = random.randint(0, enemies_per_room)

        # Get available floor tiles in this room
        floor_tiles = list(room.inner_tiles())

        for _ in range(num_enemies):
            if not floor_tiles:
                break

            # Pick a random position and remove it from available
            pos = random.choice(floor_tiles)
            floor_tiles.remove(pos)

            # Pick a random enemy type (weighted toward weaker enemies)
            if random.random() < 0.8:
                enemy_type = "orc"  # 80% orcs
            else:
                enemy_type = "troll"  # 20% trolls

            x, y = pos
            entity, stats = create_enemy(grid, texture, x, y, enemy_type)
            enemies.append((entity, stats))

    return enemies


def get_blocking_entity_at(
    entities: List[mcrfpy.Entity],
    x: int,
    y: int
) -> Optional[mcrfpy.Entity]:
    """
    Check if there's a blocking entity at the given position.

    Useful for collision detection - checks if an entity exists at
    the target position before moving there.

    Args:
        entities: List of entities to check
        x: X coordinate to check
        y: Y coordinate to check

    Returns:
        The entity at that position, or None if empty
    """
    for entity in entities:
        if entity.pos[0] == x and entity.pos[1] == y:
            return entity
    return None


def move_entity(
    entity: mcrfpy.Entity,
    grid: mcrfpy.Grid,
    dx: int,
    dy: int,
    entities: List[mcrfpy.Entity] = None
) -> bool:
    """
    Attempt to move an entity by a delta.

    Checks for:
    - Grid bounds
    - Walkable terrain
    - Other blocking entities (if entities list provided)

    Args:
        entity: The entity to move
        grid: The grid for terrain collision
        dx: Delta X (-1, 0, or 1 typically)
        dy: Delta Y (-1, 0, or 1 typically)
        entities: Optional list of entities to check for collision

    Returns:
        True if movement succeeded, False otherwise
    """
    dest_x = entity.pos[0] + dx
    dest_y = entity.pos[1] + dy

    # Check grid bounds
    grid_width, grid_height = grid.grid_size
    if not (0 <= dest_x < grid_width and 0 <= dest_y < grid_height):
        return False

    # Check if tile is walkable
    if not grid.at(dest_x, dest_y).walkable:
        return False

    # Check for blocking entities
    if entities and get_blocking_entity_at(entities, dest_x, dest_y):
        return False

    # Move is valid
    entity.pos = (dest_x, dest_y)
    return True


def distance_between(
    entity1: mcrfpy.Entity,
    entity2: mcrfpy.Entity
) -> float:
    """
    Calculate the Chebyshev distance between two entities.

    Chebyshev distance (also called chessboard distance) counts
    diagonal moves as 1, which is standard for roguelikes.

    Args:
        entity1: First entity
        entity2: Second entity

    Returns:
        Distance in tiles (diagonal = 1)
    """
    dx = abs(entity1.pos[0] - entity2.pos[0])
    dy = abs(entity1.pos[1] - entity2.pos[1])
    return max(dx, dy)


def entities_in_radius(
    center: mcrfpy.Entity,
    entities: List[mcrfpy.Entity],
    radius: float
) -> List[mcrfpy.Entity]:
    """
    Find all entities within a given radius of a center entity.

    Uses Chebyshev distance for roguelike-style radius.

    Args:
        center: The entity to search around
        entities: List of entities to check
        radius: Maximum distance in tiles

    Returns:
        List of entities within the radius (excluding center)
    """
    nearby = []
    for entity in entities:
        if entity is not center:
            if distance_between(center, entity) <= radius:
                nearby.append(entity)
    return nearby


def remove_entity(
    entity: mcrfpy.Entity,
    grid: mcrfpy.Grid
) -> bool:
    """
    Remove an entity from a grid.

    Args:
        entity: The entity to remove
        grid: The grid containing the entity

    Returns:
        True if removal succeeded, False otherwise
    """
    try:
        idx = entity.index()
        grid.entities.remove(idx)
        return True
    except (ValueError, AttributeError):
        return False
