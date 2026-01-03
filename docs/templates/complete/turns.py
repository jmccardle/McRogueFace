"""
turns.py - Turn Management System for McRogueFace Roguelike

Handles the turn-based game flow: player turn, then enemy turns.
"""

from enum import Enum, auto
from typing import List, Optional, Callable, TYPE_CHECKING

from entities import Player, Enemy
from combat import try_attack, process_kill, CombatResult
from ai import process_enemy_turns

if TYPE_CHECKING:
    from dungeon import Dungeon


class GameState(Enum):
    """Current state of the game."""
    PLAYER_TURN = auto()      # Waiting for player input
    ENEMY_TURN = auto()       # Processing enemy actions
    PLAYER_DEAD = auto()      # Player has died
    VICTORY = auto()          # Player has won (optional)
    LEVEL_TRANSITION = auto() # Moving to next level


class TurnManager:
    """
    Manages the turn-based game loop.

    The game follows this flow:
    1. Player takes action (move or attack)
    2. If action was valid, enemies take turns
    3. Check for game over conditions
    4. Return to step 1
    """

    def __init__(self, player: Player, enemies: List[Enemy], dungeon: 'Dungeon'):
        """
        Initialize the turn manager.

        Args:
            player: The player entity
            enemies: List of all enemies
            dungeon: The dungeon map
        """
        self.player = player
        self.enemies = enemies
        self.dungeon = dungeon
        self.state = GameState.PLAYER_TURN
        self.turn_count = 0

        # Callbacks for game events
        self.on_message: Optional[Callable[[str, tuple], None]] = None
        self.on_player_death: Optional[Callable[[], None]] = None
        self.on_enemy_death: Optional[Callable[[Enemy], None]] = None
        self.on_turn_end: Optional[Callable[[int], None]] = None

    def reset(self, player: Player, enemies: List[Enemy], dungeon: 'Dungeon') -> None:
        """Reset the turn manager with new game state."""
        self.player = player
        self.enemies = enemies
        self.dungeon = dungeon
        self.state = GameState.PLAYER_TURN
        self.turn_count = 0

    def add_message(self, message: str, color: tuple = (255, 255, 255, 255)) -> None:
        """Add a message to the log via callback."""
        if self.on_message:
            self.on_message(message, color)

    def handle_player_action(self, dx: int, dy: int) -> bool:
        """
        Handle a player movement or attack action.

        Args:
            dx: X direction (-1, 0, or 1)
            dy: Y direction (-1, 0, or 1)

        Returns:
            True if the action consumed a turn, False otherwise
        """
        if self.state != GameState.PLAYER_TURN:
            return False

        target_x = self.player.x + dx
        target_y = self.player.y + dy

        # Check for attack
        result = try_attack(self.player, target_x, target_y, self.enemies)

        if result:
            # Player attacked something
            self.add_message(result.message, result.message_color)

            if result.killed:
                # Process kill
                xp = process_kill(self.player, result.defender)
                self.enemies.remove(result.defender)

                if xp > 0:
                    self.add_message(f"You gain {xp} XP!", (255, 255, 100, 255))

                if self.on_enemy_death:
                    self.on_enemy_death(result.defender)

            # Action consumed a turn
            self._end_player_turn()
            return True

        # No attack - try to move
        if self.dungeon.is_walkable(target_x, target_y):
            # Check for enemy blocking
            blocked = False
            for enemy in self.enemies:
                if enemy.is_alive and enemy.x == target_x and enemy.y == target_y:
                    blocked = True
                    break

            if not blocked:
                self.player.move_to(target_x, target_y)
                self._end_player_turn()
                return True

        # Movement blocked
        return False

    def handle_wait(self) -> bool:
        """
        Handle the player choosing to wait (skip turn).

        Returns:
            True (always consumes a turn)
        """
        if self.state != GameState.PLAYER_TURN:
            return False

        self.add_message("You wait...", (150, 150, 150, 255))
        self._end_player_turn()
        return True

    def _end_player_turn(self) -> None:
        """End the player's turn and process enemy turns."""
        self.state = GameState.ENEMY_TURN
        self._process_enemy_turns()

    def _process_enemy_turns(self) -> None:
        """Process all enemy turns."""
        # Get combat results from enemy actions
        results = process_enemy_turns(
            self.enemies,
            self.player,
            self.dungeon
        )

        # Report results
        for result in results:
            self.add_message(result.message, result.message_color)

        # Check if player died
        if not self.player.is_alive:
            self.state = GameState.PLAYER_DEAD
            if self.on_player_death:
                self.on_player_death()
        else:
            # End turn
            self.turn_count += 1
            self.state = GameState.PLAYER_TURN

            if self.on_turn_end:
                self.on_turn_end(self.turn_count)

    def is_player_turn(self) -> bool:
        """Check if it's the player's turn."""
        return self.state == GameState.PLAYER_TURN

    def is_game_over(self) -> bool:
        """Check if the game is over (player dead)."""
        return self.state == GameState.PLAYER_DEAD

    def get_enemy_count(self) -> int:
        """Get the number of living enemies."""
        return sum(1 for e in self.enemies if e.is_alive)


class ActionResult:
    """Result of a player action."""

    def __init__(self, success: bool, message: str = "",
                 color: tuple = (255, 255, 255, 255)):
        self.success = success
        self.message = message
        self.color = color


def try_move_or_attack(player: Player, dx: int, dy: int,
                       dungeon: 'Dungeon', enemies: List[Enemy]) -> ActionResult:
    """
    Attempt to move or attack in a direction.

    This is a simpler, standalone function for games that don't want
    the full TurnManager.

    Args:
        player: The player
        dx: X direction
        dy: Y direction
        dungeon: The dungeon map
        enemies: List of enemies

    Returns:
        ActionResult indicating success and any message
    """
    target_x = player.x + dx
    target_y = player.y + dy

    # Check for attack
    for enemy in enemies:
        if enemy.is_alive and enemy.x == target_x and enemy.y == target_y:
            result = try_attack(player, target_x, target_y, enemies)
            if result:
                if result.killed:
                    process_kill(player, enemy)
                    enemies.remove(enemy)
                return ActionResult(True, result.message, result.message_color)

    # Check for movement
    if dungeon.is_walkable(target_x, target_y):
        player.move_to(target_x, target_y)
        return ActionResult(True)

    return ActionResult(False, "You can't move there!", (150, 150, 150, 255))
