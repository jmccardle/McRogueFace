"""McRogueFace - Part 2: Walls, Floors, and Collision

Documentation: https://mcrogueface.github.io/tutorial/part_02_tiles_collision
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/tutorials/part_02_tiles_collision/part_02_tiles_collision.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy

# =============================================================================
# Constants
# =============================================================================

# Sprite indices for CP437 tileset
SPRITE_WALL = 35    # '#' - wall
SPRITE_FLOOR = 46   # '.' - floor
SPRITE_PLAYER = 64  # '@' - player

# Grid dimensions
GRID_WIDTH = 30
GRID_HEIGHT = 20

# =============================================================================
# Map Creation
# =============================================================================

def create_map(grid: mcrfpy.Grid) -> None:
    """Fill the grid with walls and floors.

    Creates a simple room with walls around the edges and floor in the middle.
    """
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            cell = grid.at(x, y)

            # Place walls around the edges
            if x == 0 or x == GRID_WIDTH - 1 or y == 0 or y == GRID_HEIGHT - 1:
                cell.tilesprite = SPRITE_WALL
                cell.walkable = False
            else:
                cell.tilesprite = SPRITE_FLOOR
                cell.walkable = True

    # Add some interior walls to make it interesting
    # Vertical wall
    for y in range(5, 15):
        cell = grid.at(10, y)
        cell.tilesprite = SPRITE_WALL
        cell.walkable = False

    # Horizontal wall
    for x in range(15, 25):
        cell = grid.at(x, 10)
        cell.tilesprite = SPRITE_WALL
        cell.walkable = False

    # Leave gaps for doorways
    grid.at(10, 10).tilesprite = SPRITE_FLOOR
    grid.at(10, 10).walkable = True
    grid.at(20, 10).tilesprite = SPRITE_FLOOR
    grid.at(20, 10).walkable = True

# =============================================================================
# Collision Detection
# =============================================================================

def can_move_to(grid: mcrfpy.Grid, x: int, y: int) -> bool:
    """Check if a position is valid for movement.

    Args:
        grid: The game grid
        x: Target X coordinate (in tiles)
        y: Target Y coordinate (in tiles)

    Returns:
        True if the position is walkable, False otherwise
    """
    # Check grid bounds first
    if x < 0 or x >= GRID_WIDTH:
        return False
    if y < 0 or y >= GRID_HEIGHT:
        return False

    # Check if the tile is walkable
    cell = grid.at(x, y)
    return cell.walkable

# =============================================================================
# Game Setup
# =============================================================================

# Create the scene
scene = mcrfpy.Scene("game")

# Load texture
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

# Create the grid
grid = mcrfpy.Grid(
    pos=(80, 100),
    size=(720, 480),
    grid_size=(GRID_WIDTH, GRID_HEIGHT),
    texture=texture,
    zoom=1.5
)

# Build the map
create_map(grid)

# Create the player in the center of the left room
player = mcrfpy.Entity(
    grid_pos=(5, 10),
    texture=texture,
    sprite_index=SPRITE_PLAYER
)
grid.entities.append(player)

# Add grid to scene
scene.children.append(grid)

# =============================================================================
# UI Elements
# =============================================================================

title = mcrfpy.Caption(
    pos=(80, 20),
    text="Part 2: Walls and Collision"
)
title.fill_color = mcrfpy.Color(255, 255, 255)
title.font_size = 24
scene.children.append(title)

instructions = mcrfpy.Caption(
    pos=(80, 55),
    text="WASD or Arrow Keys to move | Walls block movement"
)
instructions.fill_color = mcrfpy.Color(180, 180, 180)
instructions.font_size = 16
scene.children.append(instructions)

pos_display = mcrfpy.Caption(
    pos=(80, 600),
    text=f"Position: ({int(player.x)}, {int(player.y)})"
)
pos_display.fill_color = mcrfpy.Color(200, 200, 100)
pos_display.font_size = 16
scene.children.append(pos_display)

status_display = mcrfpy.Caption(
    pos=(400, 600),
    text="Status: Ready"
)
status_display.fill_color = mcrfpy.Color(100, 200, 100)
status_display.font_size = 16
scene.children.append(status_display)

# =============================================================================
# Input Handling
# =============================================================================

def handle_keys(key: str, action: str) -> None:
    """Handle keyboard input with collision detection."""
    if action != "start":
        return

    # Get current position
    px, py = int(player.x), int(player.y)

    # Calculate intended new position
    new_x, new_y = px, py

    if key == "W" or key == "Up":
        new_y -= 1
    elif key == "S" or key == "Down":
        new_y += 1
    elif key == "A" or key == "Left":
        new_x -= 1
    elif key == "D" or key == "Right":
        new_x += 1
    elif key == "Escape":
        mcrfpy.exit()
        return
    else:
        return  # Ignore other keys

    # Check collision before moving
    if can_move_to(grid, new_x, new_y):
        player.x = new_x
        player.y = new_y
        pos_display.text = f"Position: ({new_x}, {new_y})"
        status_display.text = "Status: Moved"
        status_display.fill_color = mcrfpy.Color(100, 200, 100)
    else:
        status_display.text = "Status: Blocked!"
        status_display.fill_color = mcrfpy.Color(200, 100, 100)

scene.on_key = handle_keys

# =============================================================================
# Start the Game
# =============================================================================

scene.activate()
print("Part 2 loaded! Try walking into walls.")