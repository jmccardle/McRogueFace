"""
game.py - Main Entry Point for McRogueFace Complete Roguelike Template

This is the main game file that ties everything together:
- Scene setup
- Input handling
- Game loop
- Level transitions

To run: Copy this template to your McRogueFace scripts/ directory
and rename to game.py (or import from game.py).
"""

import mcrfpy
from typing import List, Optional

# Import game modules
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    GRID_X, GRID_Y, GRID_WIDTH, GRID_HEIGHT,
    DUNGEON_WIDTH, DUNGEON_HEIGHT,
    TEXTURE_PATH, FONT_PATH,
    KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT,
    KEY_UP_LEFT, KEY_UP_RIGHT, KEY_DOWN_LEFT, KEY_DOWN_RIGHT,
    KEY_WAIT, KEY_DESCEND,
    MSG_WELCOME, MSG_DESCEND, MSG_BLOCKED, MSG_STAIRS, MSG_DEATH, MSG_NO_STAIRS,
    FOV_RADIUS, COLOR_FOG, COLOR_REMEMBERED, COLOR_VISIBLE
)
from dungeon import Dungeon, generate_dungeon
from entities import Player, Enemy, create_player, create_enemy
from turns import TurnManager, GameState
from ui import GameUI, DeathScreen


class Game:
    """
    Main game class that manages the complete roguelike experience.
    """

    def __init__(self):
        """Initialize the game."""
        # Load resources
        self.texture = mcrfpy.Texture(TEXTURE_PATH, 16, 16)
        self.font = mcrfpy.Font(FONT_PATH)

        # Create scene
        mcrfpy.createScene("game")
        self.ui_collection = mcrfpy.sceneUI("game")

        # Create grid
        self.grid = mcrfpy.Grid(
            DUNGEON_WIDTH, DUNGEON_HEIGHT,
            self.texture,
            GRID_X, GRID_Y,
            GRID_WIDTH, GRID_HEIGHT
        )
        self.ui_collection.append(self.grid)

        # Game state
        self.dungeon: Optional[Dungeon] = None
        self.player: Optional[Player] = None
        self.enemies: List[Enemy] = []
        self.turn_manager: Optional[TurnManager] = None
        self.current_level = 1

        # UI
        self.game_ui = GameUI(self.font)
        self.game_ui.add_to_scene(self.ui_collection)

        self.death_screen: Optional[DeathScreen] = None
        self.game_over = False

        # Set up input handling
        mcrfpy.keypressScene(self.handle_keypress)

        # Start the game
        self.new_game()

        # Switch to game scene
        mcrfpy.setScene("game")

    def new_game(self) -> None:
        """Start a new game from level 1."""
        self.current_level = 1
        self.game_over = False

        # Clear any death screen
        if self.death_screen:
            self.death_screen.remove_from_scene(self.ui_collection)
            self.death_screen = None

        # Generate first level
        self.generate_level()

        # Welcome message
        self.game_ui.clear_messages()
        self.game_ui.add_message(MSG_WELCOME, (255, 255, 100, 255))

    def generate_level(self) -> None:
        """Generate a new dungeon level."""
        # Clear existing entities from grid
        while len(self.grid.entities) > 0:
            self.grid.entities.remove(0)

        self.enemies.clear()

        # Generate dungeon
        self.dungeon = generate_dungeon(self.current_level)
        self.dungeon.apply_to_grid(self.grid)

        # Create player at start position
        start_x, start_y = self.dungeon.player_start
        self.player = create_player(start_x, start_y, self.texture, self.grid)
        self.player.dungeon_level = self.current_level

        # Spawn enemies
        enemy_spawns = self.dungeon.get_enemy_spawns()
        for enemy_type, x, y in enemy_spawns:
            enemy = create_enemy(x, y, enemy_type, self.texture, self.grid)
            self.enemies.append(enemy)

        # Set up turn manager
        self.turn_manager = TurnManager(self.player, self.enemies, self.dungeon)
        self.turn_manager.on_message = self.game_ui.add_message
        self.turn_manager.on_player_death = self.on_player_death

        # Update FOV
        self.update_fov()

        # Center camera on player
        self.center_camera()

        # Update UI
        self.game_ui.update_level(self.current_level)
        self.update_ui()

    def descend(self) -> None:
        """Go down to the next dungeon level."""
        # Check if player is on stairs
        if self.player.pos != self.dungeon.stairs_pos:
            self.game_ui.add_message(MSG_NO_STAIRS, (150, 150, 150, 255))
            return

        self.current_level += 1
        self.game_ui.add_message(MSG_DESCEND % self.current_level, (100, 100, 255, 255))

        # Keep player stats
        old_hp = self.player.fighter.hp
        old_max_hp = self.player.fighter.max_hp
        old_attack = self.player.fighter.attack
        old_defense = self.player.fighter.defense
        old_xp = self.player.xp
        old_level = self.player.level

        # Generate new level
        self.generate_level()

        # Restore player stats
        self.player.fighter.hp = old_hp
        self.player.fighter.max_hp = old_max_hp
        self.player.fighter.attack = old_attack
        self.player.fighter.defense = old_defense
        self.player.xp = old_xp
        self.player.level = old_level

        self.update_ui()

    def update_fov(self) -> None:
        """Update field of view and apply to grid tiles."""
        if not self.player or not self.dungeon:
            return

        # Use entity's built-in FOV calculation
        self.player.entity.update_visibility()

        # Apply visibility to tiles
        for x in range(self.dungeon.width):
            for y in range(self.dungeon.height):
                point = self.grid.at(x, y)
                tile = self.dungeon.get_tile(x, y)

                if tile:
                    state = self.player.entity.at(x, y)

                    if state.visible:
                        # Currently visible
                        tile.explored = True
                        tile.visible = True
                        point.color_overlay = mcrfpy.Color(*COLOR_VISIBLE)
                    elif tile.explored:
                        # Explored but not visible
                        tile.visible = False
                        point.color_overlay = mcrfpy.Color(*COLOR_REMEMBERED)
                    else:
                        # Never seen
                        point.color_overlay = mcrfpy.Color(*COLOR_FOG)

    def center_camera(self) -> None:
        """Center the camera on the player."""
        if self.player:
            self.grid.center = (self.player.x, self.player.y)

    def update_ui(self) -> None:
        """Update all UI elements."""
        if self.player:
            self.game_ui.update_hp(
                self.player.fighter.hp,
                self.player.fighter.max_hp
            )

    def on_player_death(self) -> None:
        """Handle player death."""
        self.game_over = True
        self.game_ui.add_message(MSG_DEATH, (255, 0, 0, 255))

        # Show death screen
        self.death_screen = DeathScreen(self.font)
        self.death_screen.add_to_scene(self.ui_collection)

    def handle_keypress(self, key: str, state: str) -> None:
        """
        Handle keyboard input.

        Args:
            key: Key name
            state: "start" for key down, "end" for key up
        """
        # Only handle key down events
        if state != "start":
            return

        # Handle restart when dead
        if self.game_over:
            if key == "R":
                self.new_game()
            return

        # Handle movement
        dx, dy = 0, 0

        if key in KEY_UP:
            dy = -1
        elif key in KEY_DOWN:
            dy = 1
        elif key in KEY_LEFT:
            dx = -1
        elif key in KEY_RIGHT:
            dx = 1
        elif key in KEY_UP_LEFT:
            dx, dy = -1, -1
        elif key in KEY_UP_RIGHT:
            dx, dy = 1, -1
        elif key in KEY_DOWN_LEFT:
            dx, dy = -1, 1
        elif key in KEY_DOWN_RIGHT:
            dx, dy = 1, 1
        elif key in KEY_WAIT:
            # Skip turn
            self.turn_manager.handle_wait()
            self.after_turn()
            return
        elif key in KEY_DESCEND:
            # Try to descend
            self.descend()
            return
        elif key == "Escape":
            # Quit game
            mcrfpy.exit()
            return

        # Process movement/attack
        if dx != 0 or dy != 0:
            if self.turn_manager.handle_player_action(dx, dy):
                self.after_turn()
            else:
                # Movement was blocked
                self.game_ui.add_message(MSG_BLOCKED, (150, 150, 150, 255))

    def after_turn(self) -> None:
        """Called after each player turn."""
        # Update FOV
        self.update_fov()

        # Center camera
        self.center_camera()

        # Update UI
        self.update_ui()

        # Check if standing on stairs
        if self.player.pos == self.dungeon.stairs_pos:
            self.game_ui.add_message(MSG_STAIRS, (100, 255, 100, 255))

        # Clean up dead enemies
        self.enemies = [e for e in self.enemies if e.is_alive]


# =============================================================================
# ENTRY POINT
# =============================================================================

# Global game instance
game: Optional[Game] = None


def start_game():
    """Start the game."""
    global game
    game = Game()


# Auto-start when this script is loaded
start_game()
