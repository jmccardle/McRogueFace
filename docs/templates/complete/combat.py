"""
combat.py - Combat System for McRogueFace Roguelike

Handles attack resolution, damage calculation, and combat outcomes.
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import random

from entities import Actor, Player, Enemy
from constants import (
    MSG_PLAYER_ATTACK, MSG_PLAYER_KILL, MSG_PLAYER_MISS,
    MSG_ENEMY_ATTACK, MSG_ENEMY_MISS
)


@dataclass
class CombatResult:
    """
    Result of a combat action.

    Attributes:
        attacker: The attacking actor
        defender: The defending actor
        damage: Damage dealt (after defense)
        killed: Whether the defender was killed
        message: Human-readable result message
        message_color: Color tuple for the message
    """
    attacker: Actor
    defender: Actor
    damage: int
    killed: bool
    message: str
    message_color: Tuple[int, int, int, int]


def calculate_damage(attack: int, defense: int, variance: float = 0.2) -> int:
    """
    Calculate damage with some randomness.

    Args:
        attack: Attacker's attack power
        defense: Defender's defense value
        variance: Random variance as percentage (0.2 = +/-20%)

    Returns:
        Final damage amount (minimum 0)
    """
    # Base damage is attack vs defense
    base_damage = attack - defense

    # Add some variance
    if base_damage > 0:
        variance_amount = int(base_damage * variance)
        damage = base_damage + random.randint(-variance_amount, variance_amount)
    else:
        # Small chance to do 1 damage even with high defense
        damage = 1 if random.random() < 0.1 else 0

    return max(0, damage)


def attack(attacker: Actor, defender: Actor) -> CombatResult:
    """
    Perform an attack from one actor to another.

    Args:
        attacker: The actor making the attack
        defender: The actor being attacked

    Returns:
        CombatResult with outcome details
    """
    # Calculate damage
    damage = calculate_damage(
        attacker.fighter.attack,
        defender.fighter.defense
    )

    # Apply damage
    actual_damage = defender.fighter.take_damage(damage + defender.fighter.defense)
    # Note: take_damage applies defense internally, so we add it back
    # Actually, we calculated damage already reduced by defense, so just apply it:
    defender.fighter.hp = max(0, defender.fighter.hp - damage + actual_damage)
    # Simplified: just use take_damage properly
    # Reset and do it right:

    # Apply raw damage (defense already calculated)
    defender.fighter.hp = max(0, defender.fighter.hp - damage)
    killed = not defender.is_alive

    # Generate message based on attacker/defender types
    if isinstance(attacker, Player):
        if killed:
            message = MSG_PLAYER_KILL % defender.name
            color = (255, 255, 100, 255)  # Yellow for kills
        elif damage > 0:
            message = MSG_PLAYER_ATTACK % (defender.name, damage)
            color = (255, 255, 255, 255)  # White for hits
        else:
            message = MSG_PLAYER_MISS % defender.name
            color = (150, 150, 150, 255)  # Gray for misses
    else:
        if damage > 0:
            message = MSG_ENEMY_ATTACK % (attacker.name, damage)
            color = (255, 100, 100, 255)  # Red for enemy hits
        else:
            message = MSG_ENEMY_MISS % attacker.name
            color = (150, 150, 150, 255)  # Gray for misses

    return CombatResult(
        attacker=attacker,
        defender=defender,
        damage=damage,
        killed=killed,
        message=message,
        message_color=color
    )


def melee_attack(attacker: Actor, defender: Actor) -> CombatResult:
    """
    Perform a melee attack (bump attack).
    This is the standard roguelike bump-to-attack.

    Args:
        attacker: The actor making the attack
        defender: The actor being attacked

    Returns:
        CombatResult with outcome details
    """
    return attack(attacker, defender)


def try_attack(attacker: Actor, target_x: int, target_y: int,
               enemies: list, player: Optional[Player] = None) -> Optional[CombatResult]:
    """
    Attempt to attack whatever is at the target position.

    Args:
        attacker: The actor making the attack
        target_x: X coordinate to attack
        target_y: Y coordinate to attack
        enemies: List of Enemy actors
        player: The player (if attacker is an enemy)

    Returns:
        CombatResult if something was attacked, None otherwise
    """
    # Check if player is attacking
    if isinstance(attacker, Player):
        # Look for enemy at position
        for enemy in enemies:
            if enemy.is_alive and enemy.x == target_x and enemy.y == target_y:
                return melee_attack(attacker, enemy)
    else:
        # Enemy attacking - check if player is at position
        if player and player.x == target_x and player.y == target_y:
            return melee_attack(attacker, player)

    return None


def process_kill(attacker: Actor, defender: Actor) -> int:
    """
    Process the aftermath of killing an enemy.

    Args:
        attacker: The actor that made the kill
        defender: The actor that was killed

    Returns:
        XP gained (if attacker is player and defender is enemy)
    """
    xp_gained = 0

    if isinstance(attacker, Player) and isinstance(defender, Enemy):
        xp_gained = defender.xp_reward
        attacker.gain_xp(xp_gained)

    # Remove the dead actor from the grid
    defender.remove()

    return xp_gained
