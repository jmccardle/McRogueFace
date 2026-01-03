"""
McRogueFace Minimal Template
============================

A starting point for simple roguelike prototypes.

This template demonstrates:
- Scene object pattern (preferred OOP approach)
- Grid-based movement with boundary checking
- Keyboard input handling
- Entity positioning on a grid

Usage:
    Place this file in your McRogueFace scripts directory and run McRogueFace.
    Use arrow keys to move the @ symbol. Press Escape to exit.
"""

import mcrfpy

# =============================================================================
# CONSTANTS
# =============================================================================

# Grid dimensions (in tiles)
GRID_WIDTH: int = 20
GRID_HEIGHT: int = 15

# Tile size in pixels (must match your sprite sheet)
TILE_SIZE: int = 16

# CP437 sprite indices (standard roguelike character mapping)
# In CP437, character codes map to sprite indices: '@' = 64, '.' = 46, etc.
SPRITE_PLAYER: int = 64   # '@' symbol
SPRITE_FLOOR: int = 46    # '.' symbol

# Colors (RGBA tuples)
COLOR_BACKGROUND: tuple[int, int, int] = (20, 20, 30)

# =============================================================================
# GAME STATE
# =============================================================================

# Player position in grid coordinates
player_x: int = GRID_WIDTH // 2
player_y: int = GRID_HEIGHT // 2

# Reference to player entity (set during setup)
player_entity: mcrfpy.Entity = None

# =============================================================================
# MOVEMENT LOGIC
# =============================================================================

def try_move(dx: int, dy: int) -> bool:
    """
    Attempt to move the player by (dx, dy) tiles.

    Args:
        dx: Horizontal movement (-1 = left, +1 = right, 0 = none)
        dy: Vertical movement (-1 = up, +1 = down, 0 = none)

    Returns:
        True if movement succeeded, False if blocked by boundary
    """
    global player_x, player_y

    new_x = player_x + dx
    new_y = player_y + dy

    # Boundary checking: ensure player stays within grid
    if 0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT:
        player_x = new_x
        player_y = new_y

        # Update the entity's position on the grid
        player_entity.x = player_x
        player_entity.y = player_y
        return True

    return False

# =============================================================================
# INPUT HANDLING
# =============================================================================

def handle_keypress(key: str, action: str) -> None:
    """
    Handle keyboard input for the game scene.

    Args:
        key: The key that was pressed (e.g., "Up", "Down", "Escape", "a", "W")
        action: Either "start" (key pressed) or "end" (key released)

    Note:
        We only process on "start" to avoid double-triggering on key release.
    """
    if action != "start":
        return

    # Movement keys (both arrow keys and WASD)
    if key == "Up" or key == "W" or key == "w":
        try_move(0, -1)
    elif key == "Down" or key == "S" or key == "s":
        try_move(0, 1)
    elif key == "Left" or key == "A" or key == "a":
        try_move(-1, 0)
    elif key == "Right" or key == "D" or key == "d":
        try_move(1, 0)

    # Exit on Escape
    elif key == "Escape":
        mcrfpy.exit()

# =============================================================================
# SCENE SETUP
# =============================================================================

def setup_game() -> mcrfpy.Scene:
    """
    Create and configure the game scene.

    Returns:
        The configured Scene object, ready to be activated.
    """
    global player_entity

    # Create the scene using the OOP pattern (preferred over createScene)
    scene = mcrfpy.Scene("game")

    # Load the sprite sheet texture
    # Adjust the path and tile size to match your assets
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", TILE_SIZE, TILE_SIZE)

    # Create the game grid
    # Grid(pos, size, grid_size) where:
    #   pos = pixel position on screen
    #   size = pixel dimensions of the grid display
    #   grid_size = number of tiles (columns, rows)
    grid = mcrfpy.Grid(
        pos=(32, 32),
        grid_size=(GRID_WIDTH, GRID_HEIGHT),
        texture=texture
    )
    grid.fill_color = mcrfpy.Color(*COLOR_BACKGROUND)

    # Fill the grid with floor tiles
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            point = grid.at(x, y)
            point.tilesprite = SPRITE_FLOOR
            point.walkable = True
            point.transparent = True

    # Create the player entity
    player_entity = mcrfpy.Entity(
        pos=(player_x, player_y),
        texture=texture,
        sprite_index=SPRITE_PLAYER
    )
    grid.entities.append(player_entity)

    # Add the grid to the scene's UI
    scene.children.append(grid)

    # Set up keyboard input handler for this scene
    scene.on_key = handle_keypress

    return scene

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

# Create and activate the game scene
game_scene = setup_game()
game_scene.activate()
