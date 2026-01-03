"""
ai.py - Enemy AI System for McRogueFace Roguelike

Simple AI behaviors for enemies: chase player when visible, wander otherwise.
Uses A* pathfinding via entity.path_to() for movement.
"""

from typing import List, Tuple, Optional, TYPE_CHECKING
import random

from entities import Enemy, Player, Actor
from combat import melee_attack, CombatResult

if TYPE_CHECKING:
    from dungeon import Dungeon


class AIBehavior:
    """Base class for AI behaviors."""

    def take_turn(self, enemy: Enemy, player: Player, dungeon: 'Dungeon',
                  enemies: List[Enemy]) -> Optional[CombatResult]:
        """
        Execute one turn of AI behavior.

        Args:
            enemy: The enemy taking a turn
            player: The player to potentially chase/attack
            dungeon: The dungeon map
            enemies: List of all enemies (for collision avoidance)

        Returns:
            CombatResult if combat occurred, None otherwise
        """
        raise NotImplementedError


class BasicChaseAI(AIBehavior):
    """
    Simple chase AI: If player is visible, move toward them.
    If adjacent, attack. Otherwise, stand still or wander.
    """

    def __init__(self, sight_range: int = 8):
        """
        Args:
            sight_range: How far the enemy can see
        """
        self.sight_range = sight_range

    def can_see_player(self, enemy: Enemy, player: Player,
                       dungeon: 'Dungeon') -> bool:
        """Check if enemy can see the player."""
        # Simple distance check combined with line of sight
        distance = enemy.distance_to(player)

        if distance > self.sight_range:
            return False

        # Check line of sight using Bresenham's line
        return self._has_line_of_sight(enemy.x, enemy.y, player.x, player.y, dungeon)

    def _has_line_of_sight(self, x1: int, y1: int, x2: int, y2: int,
                           dungeon: 'Dungeon') -> bool:
        """
        Check if there's a clear line of sight between two points.
        Uses Bresenham's line algorithm.
        """
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1

        if dx > dy:
            err = dx / 2
            while x != x2:
                if not dungeon.is_transparent(x, y):
                    return False
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2
            while y != y2:
                if not dungeon.is_transparent(x, y):
                    return False
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy

        return True

    def get_path_to_player(self, enemy: Enemy, player: Player) -> List[Tuple[int, int]]:
        """
        Get a path from enemy to player using A* pathfinding.

        Uses the entity's built-in path_to method.
        """
        try:
            path = enemy.entity.path_to(player.x, player.y)
            # Convert path to list of tuples
            return [(int(p[0]), int(p[1])) for p in path] if path else []
        except (AttributeError, TypeError):
            # Fallback: simple direction-based movement
            return []

    def is_position_blocked(self, x: int, y: int, dungeon: 'Dungeon',
                           enemies: List[Enemy], player: Player) -> bool:
        """Check if a position is blocked by terrain or another actor."""
        # Check terrain
        if not dungeon.is_walkable(x, y):
            return True

        # Check player position
        if player.x == x and player.y == y:
            return True

        # Check other enemies
        for other in enemies:
            if other.is_alive and other.x == x and other.y == y:
                return True

        return False

    def move_toward(self, enemy: Enemy, target_x: int, target_y: int,
                    dungeon: 'Dungeon', enemies: List[Enemy],
                    player: Player) -> bool:
        """
        Move one step toward the target position.

        Returns True if movement occurred, False otherwise.
        """
        # Try pathfinding first
        path = self.get_path_to_player(enemy, player)

        if path and len(path) > 1:
            # First element is current position, second is next step
            next_x, next_y = path[1]
        else:
            # Fallback: move in the general direction
            dx = 0
            dy = 0

            if target_x < enemy.x:
                dx = -1
            elif target_x > enemy.x:
                dx = 1

            if target_y < enemy.y:
                dy = -1
            elif target_y > enemy.y:
                dy = 1

            next_x = enemy.x + dx
            next_y = enemy.y + dy

        # Check if the position is blocked
        if not self.is_position_blocked(next_x, next_y, dungeon, enemies, player):
            enemy.move_to(next_x, next_y)
            return True

        # Try moving in just one axis
        if next_x != enemy.x:
            if not self.is_position_blocked(next_x, enemy.y, dungeon, enemies, player):
                enemy.move_to(next_x, enemy.y)
                return True

        if next_y != enemy.y:
            if not self.is_position_blocked(enemy.x, next_y, dungeon, enemies, player):
                enemy.move_to(enemy.x, next_y)
                return True

        return False

    def take_turn(self, enemy: Enemy, player: Player, dungeon: 'Dungeon',
                  enemies: List[Enemy]) -> Optional[CombatResult]:
        """Execute the enemy's turn."""
        if not enemy.is_alive:
            return None

        # Check if adjacent to player (can attack)
        if enemy.distance_to(player) == 1:
            return melee_attack(enemy, player)

        # Check if can see player
        if self.can_see_player(enemy, player, dungeon):
            # Move toward player
            self.move_toward(enemy, player.x, player.y, dungeon, enemies, player)

        return None


class WanderingAI(BasicChaseAI):
    """
    AI that wanders randomly when it can't see the player.
    More active than BasicChaseAI.
    """

    def __init__(self, sight_range: int = 8, wander_chance: float = 0.3):
        """
        Args:
            sight_range: How far the enemy can see
            wander_chance: Probability of wandering each turn (0.0 to 1.0)
        """
        super().__init__(sight_range)
        self.wander_chance = wander_chance

    def wander(self, enemy: Enemy, dungeon: 'Dungeon',
               enemies: List[Enemy], player: Player) -> bool:
        """
        Move in a random direction.

        Returns True if movement occurred.
        """
        # Random direction
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),  # Cardinal
            (-1, -1), (1, -1), (-1, 1), (1, 1)  # Diagonal
        ]
        random.shuffle(directions)

        for dx, dy in directions:
            new_x = enemy.x + dx
            new_y = enemy.y + dy

            if not self.is_position_blocked(new_x, new_y, dungeon, enemies, player):
                enemy.move_to(new_x, new_y)
                return True

        return False

    def take_turn(self, enemy: Enemy, player: Player, dungeon: 'Dungeon',
                  enemies: List[Enemy]) -> Optional[CombatResult]:
        """Execute the enemy's turn with wandering behavior."""
        if not enemy.is_alive:
            return None

        # Check if adjacent to player (can attack)
        if enemy.distance_to(player) == 1:
            return melee_attack(enemy, player)

        # Check if can see player
        if self.can_see_player(enemy, player, dungeon):
            # Chase player
            self.move_toward(enemy, player.x, player.y, dungeon, enemies, player)
        else:
            # Wander randomly
            if random.random() < self.wander_chance:
                self.wander(enemy, dungeon, enemies, player)

        return None


# Default AI instance
default_ai = WanderingAI(sight_range=8, wander_chance=0.3)


def process_enemy_turns(enemies: List[Enemy], player: Player,
                        dungeon: 'Dungeon',
                        ai: AIBehavior = None) -> List[CombatResult]:
    """
    Process turns for all enemies.

    Args:
        enemies: List of all enemies
        player: The player
        dungeon: The dungeon map
        ai: AI behavior to use (defaults to WanderingAI)

    Returns:
        List of combat results from this round of enemy actions
    """
    if ai is None:
        ai = default_ai

    results = []

    for enemy in enemies:
        if enemy.is_alive:
            result = ai.take_turn(enemy, player, dungeon, enemies)
            if result:
                results.append(result)

    return results
