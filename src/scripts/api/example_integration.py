"""Example: Integrating a McRogueFace game with the API bridge.

This file shows how a game script can integrate with the API to provide
rich metadata and semantic hints for external clients.
"""

# Import the API module
import sys
sys.path.insert(0, '../src/scripts')

from api import start_server
from api.metadata import (
    set_game_info,
    set_controls,
    set_keyboard_hints,
    set_custom_hints,
    register_scene,
)


def setup_api_for_crypt_of_sokoban():
    """Example setup for the Crypt of Sokoban game."""

    # Set basic game info
    set_game_info(
        name="Crypt of Sokoban",
        version="0.1.0",
        description="A puzzle roguelike combining Sokoban mechanics with dungeon exploration. Push boulders, avoid enemies, and descend deeper into the crypt.",
        author="7DRL 2025"
    )

    # Set control descriptions
    set_controls({
        "movement": "W/A/S/D keys",
        "wait": "Period (.) to skip turn",
        "zap": "Z to use equipped item's active ability",
        "use_item_1": "Numpad 1 to use first inventory slot",
        "use_item_2": "Numpad 2 to use second inventory slot",
        "use_item_3": "Numpad 3 to use third inventory slot",
        "pull_boulder": "X to pull adjacent boulder toward you",
        "debug_descend": "P to descend (debug)",
    })

    # Set keyboard hints for LLM context
    set_keyboard_hints([
        {"key": "W", "action": "Move up"},
        {"key": "A", "action": "Move left"},
        {"key": "S", "action": "Move down"},
        {"key": "D", "action": "Move right"},
        {"key": ".", "action": "Wait (skip turn, enemies still move)"},
        {"key": "Z", "action": "Zap - use equipped item's ability"},
        {"key": "X", "action": "Pull boulder toward you"},
        {"key": "1", "action": "Use item in slot 1"},
        {"key": "2", "action": "Use item in slot 2"},
        {"key": "3", "action": "Use item in slot 3"},
    ])

    # Set custom hints for LLM strategizing
    set_custom_hints("""
Crypt of Sokoban Strategy Guide:

CORE MECHANICS:
- Push boulders by walking into them (if space behind is clear)
- Pull boulders with X key while standing adjacent
- Boulders block enemy movement - use them as barriers!
- Step on buttons to unlock doors/exits
- Each floor has one exit that leads deeper

ENEMIES:
- Rats: Basic enemy, moves toward you
- Big Rats: Tougher, 2 damage per hit
- Cyclops: Very dangerous, 3 damage, can push boulders!

ITEMS:
- Potions: Consumable healing/buffs (use with 1/2/3 keys)
- Weapons: Equip for passive bonuses and active abilities
- Each item has a "zap" ability on cooldown

STRATEGY TIPS:
- Always look for buttons before moving - stepping on them opens paths
- Trap enemies behind boulders when possible
- Don't get cornered - keep escape routes open
- Use Z ability when enemies cluster together
- Higher floors have better loot but harder enemies
""")

    # Register scenes
    register_scene("menu", "Main menu with Play, Settings, and audio controls")
    register_scene("play", "Main gameplay scene with dungeon grid, HUD, and sidebar")

    # Start the server
    server = start_server(8765)
    print("[Game] API bridge configured for Crypt of Sokoban")

    return server


# Example usage in game.py:
# from api.example_integration import setup_api_for_crypt_of_sokoban
# api_server = setup_api_for_crypt_of_sokoban()
