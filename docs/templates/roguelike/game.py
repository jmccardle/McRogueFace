"""
game.py - Roguelike Template Main Entry Point

A minimal but complete roguelike starter using McRogueFace.

This template demonstrates:
- Scene and grid setup
- Procedural dungeon generation
- Player entity with keyboard movement
- Enemy entities (static, no AI)
- Field of view using TCOD via Entity.update_visibility()
- FOV visualization with grid color overlays

Run with: ./mcrogueface

Controls:
- Arrow keys / WASD: Move player
- Escape: Quit game

The template is designed to be extended. Good next steps:
- Add enemy AI (chase player, pathfinding)
- Implement combat system
- Add items and inventory
- Add multiple dungeon levels
"""

import mcrfpy
from typing import List, Tuple

# Import our template modules
from constants import (
    MAP_WIDTH, MAP_HEIGHT,
    SPRITE_WIDTH, SPRITE_HEIGHT,
    FOV_RADIUS,
    COLOR_VISIBLE, COLOR_EXPLORED, COLOR_UNKNOWN,
    SPRITE_PLAYER,
)
from dungeon import generate_dungeon, populate_grid, RectangularRoom
from entities import (
    create_player,
    create_enemies_in_rooms,
    move_entity,
    EntityStats,
)


# =============================================================================
# GAME STATE
# =============================================================================
# Global game state - in a larger game, you'd use a proper state management
# system, but for a template this keeps things simple and visible.

class GameState:
    """Container for all game state."""

    def __init__(self):
        # Core game objects (set during initialization)
        self.grid: mcrfpy.Grid = None
        self.player: mcrfpy.Entity = None
        self.rooms: List[RectangularRoom] = []
        self.enemies: List[Tuple[mcrfpy.Entity, EntityStats]] = []

        # Texture reference
        self.texture: mcrfpy.Texture = None


# Global game state instance
game = GameState()


# =============================================================================
# FOV (FIELD OF VIEW) SYSTEM
# =============================================================================

def update_fov() -> None:
    """
    Update the field of view based on player position.

    This function:
    1. Calls update_visibility() on the player entity to compute FOV using TCOD
    2. Applies color overlays to tiles based on visibility state

    The FOV creates the classic roguelike effect where:
    - Visible tiles are fully bright (no overlay)
    - Previously seen tiles are dimmed (remembered layout)
    - Never-seen tiles are completely dark

    TCOD handles the actual FOV computation based on the grid's
    walkable and transparent flags set during dungeon generation.
    """
    if not game.player or not game.grid:
        return

    # Tell McRogueFace/TCOD to recompute visibility from player position
    game.player.update_visibility()

    grid_width, grid_height = game.grid.grid_size

    # Apply visibility colors to each tile
    for x in range(grid_width):
        for y in range(grid_height):
            point = game.grid.at(x, y)

            # Get the player's visibility state for this tile
            state = game.player.at(x, y)

            if state.visible:
                # Currently visible - no overlay (full brightness)
                point.color_overlay = COLOR_VISIBLE
            elif state.discovered:
                # Previously seen - dimmed overlay (memory)
                point.color_overlay = COLOR_EXPLORED
            else:
                # Never seen - completely dark
                point.color_overlay = COLOR_UNKNOWN


# =============================================================================
# INPUT HANDLING
# =============================================================================

def handle_keys(key: str, state: str) -> None:
    """
    Handle keyboard input for player movement and game controls.

    This is the main input handler registered with McRogueFace.
    It processes key events and updates game state accordingly.

    Args:
        key: The key that was pressed (e.g., "W", "Up", "Escape")
        state: Either "start" (key pressed) or "end" (key released)
    """
    # Only process key press events, not releases
    if state != "start":
        return

    # Movement deltas: (dx, dy)
    movement = {
        # Arrow keys
        "Up": (0, -1),
        "Down": (0, 1),
        "Left": (-1, 0),
        "Right": (1, 0),
        # WASD keys
        "W": (0, -1),
        "S": (0, 1),
        "A": (-1, 0),
        "D": (1, 0),
        # Numpad (for diagonal movement if desired)
        "Numpad8": (0, -1),
        "Numpad2": (0, 1),
        "Numpad4": (-1, 0),
        "Numpad6": (1, 0),
        "Numpad7": (-1, -1),
        "Numpad9": (1, -1),
        "Numpad1": (-1, 1),
        "Numpad3": (1, 1),
    }

    if key in movement:
        dx, dy = movement[key]

        # Get list of all entity objects for collision checking
        all_entities = [e for e, _ in game.enemies]

        # Attempt to move the player
        if move_entity(game.player, game.grid, dx, dy, all_entities):
            # Movement succeeded - update FOV
            update_fov()

            # Center camera on player
            px, py = game.player.pos
            game.grid.center = (px, py)

    elif key == "Escape":
        # Quit the game
        mcrfpy.exit()


# =============================================================================
# GAME INITIALIZATION
# =============================================================================

def initialize_game() -> None:
    """
    Set up the game world.

    This function:
    1. Creates the scene and loads resources
    2. Generates the dungeon layout
    3. Creates and places all entities
    4. Initializes the FOV system
    5. Sets up input handling
    """
    # Create the game scene
    mcrfpy.createScene("game")
    ui = mcrfpy.sceneUI("game")

    # Load the tileset texture
    # The default McRogueFace texture works great for roguelikes
    game.texture = mcrfpy.Texture(
        "assets/kenney_tinydungeon.png",
        SPRITE_WIDTH,
        SPRITE_HEIGHT
    )

    # Create the grid (tile-based game world)
    # Using keyword arguments for clarity - this is the preferred style
    game.grid = mcrfpy.Grid(
        pos=(0, 0),                          # Screen position in pixels
        size=(1024, 768),                    # Display size in pixels
        grid_size=(MAP_WIDTH, MAP_HEIGHT),   # Map size in tiles
        texture=game.texture
    )
    ui.append(game.grid)

    # Generate dungeon layout
    game.rooms = generate_dungeon()

    # Apply dungeon to grid (sets tiles, walkable flags, etc.)
    populate_grid(game.grid, game.rooms)

    # Place player in the center of the first room
    if game.rooms:
        start_x, start_y = game.rooms[0].center
    else:
        # Fallback if no rooms generated
        start_x, start_y = MAP_WIDTH // 2, MAP_HEIGHT // 2

    game.player = create_player(
        grid=game.grid,
        texture=game.texture,
        x=start_x,
        y=start_y
    )

    # Center camera on player
    game.grid.center = (start_x, start_y)

    # Spawn enemies in other rooms
    game.enemies = create_enemies_in_rooms(
        grid=game.grid,
        texture=game.texture,
        rooms=game.rooms,
        enemies_per_room=2,
        skip_first_room=True
    )

    # Initial FOV calculation
    update_fov()

    # Register input handler
    mcrfpy.keypressScene(handle_keys)

    # Switch to game scene
    mcrfpy.setScene("game")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main() -> None:
    """
    Main entry point for the roguelike template.

    This function is called when the script starts. It initializes
    the game and McRogueFace handles the game loop automatically.
    """
    initialize_game()

    # Display welcome message
    print("=" * 50)
    print("  ROGUELIKE TEMPLATE")
    print("=" * 50)
    print("Controls:")
    print("  Arrow keys / WASD - Move")
    print("  Escape - Quit")
    print()
    print(f"Dungeon generated with {len(game.rooms)} rooms")
    print(f"Enemies spawned: {len(game.enemies)}")
    print("=" * 50)


# Run the game
if __name__ == "__main__":
    main()
else:
    # McRogueFace runs game.py directly, not as __main__
    main()
