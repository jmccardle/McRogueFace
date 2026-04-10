"""McRogueFace - Part 1: The '@' and the Dungeon Grid

Documentation: https://mcrogueface.github.io/tutorial/part_01_grid_movement
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/tutorials/part_01_grid_movement/part_01_grid_movement.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy

# Sprite indices for CP437 tileset
SPRITE_AT = 64      # '@' - player character
SPRITE_FLOOR = 46   # '.' - floor tile

# Grid dimensions (in tiles)
GRID_WIDTH = 20
GRID_HEIGHT = 15

# Create the scene
scene = mcrfpy.Scene("game")

# Load the texture (sprite sheet)
# Parameters: path, sprite_width, sprite_height
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

# Create the grid
# The grid displays tiles and contains entities
grid = mcrfpy.Grid(
    pos=(100, 80),          # Position on screen (pixels)
    size=(640, 480),        # Display size (pixels)
    zoom = 2.0,
    grid_size=(GRID_WIDTH, GRID_HEIGHT),  # Size in tiles
    texture=texture
)

# Fill the grid with floor tiles
for y in range(GRID_HEIGHT):
    for x in range(GRID_WIDTH):
        cell = grid.at(x, y)
        cell.tilesprite = SPRITE_FLOOR

# Create the player entity at the center of the grid
player = mcrfpy.Entity(
    grid_pos=(GRID_WIDTH // 2, GRID_HEIGHT // 2),  # Grid coordinates, not pixels!
    texture=texture,
    sprite_index=SPRITE_AT
)

# Add the player to the grid
# Option 1: Use the grid parameter in constructor
# player = mcrfpy.Entity(grid_pos=(10, 7), texture=texture, sprite_index=SPRITE_AT, grid=grid)

# Option 2: Append to grid.entities (what we will use)
grid.entities.append(player)

# Add the grid to the scene
scene.children.append(grid)

# Add a title caption
title = mcrfpy.Caption(
    pos=(100, 20),
    text="Part 1: Grid Movement - Use Arrow Keys or WASD"
)
title.fill_color = mcrfpy.Color(255, 255, 255)
title.font_size = 18
scene.children.append(title)

# Add a position display
pos_display = mcrfpy.Caption(
    pos=(100, 50),
    text=f"Player Position: ({player.x}, {player.y})"
)
pos_display.fill_color = mcrfpy.Color(200, 200, 100)
pos_display.font_size = 16
scene.children.append(pos_display)

def handle_keys(key, action) -> None:
    """Handle keyboard input to move the player.

    Args:
        key: A mcrfpy.Key enum value (e.g., Key.W, Key.UP)
        action: A mcrfpy.InputState enum value (PRESSED or RELEASED)
    """
    # Only respond to key press, not release
    if action != mcrfpy.InputState.PRESSED:
        return

    # Get current player position
    px, py = int(player.x), int(player.y)

    # Calculate new position based on key
    if key == mcrfpy.Key.W or key == mcrfpy.Key.UP:
        py -= 1  # Up decreases Y
    elif key == mcrfpy.Key.S or key == mcrfpy.Key.DOWN:
        py += 1  # Down increases Y
    elif key == mcrfpy.Key.A or key == mcrfpy.Key.LEFT:
        px -= 1  # Left decreases X
    elif key == mcrfpy.Key.D or key == mcrfpy.Key.RIGHT:
        px += 1  # Right increases X
    elif key == mcrfpy.Key.ESCAPE:
        mcrfpy.exit()
        return

    # Update player position
    player.x = px
    player.y = py

    # Update the position display
    pos_display.text = f"Player Position: ({player.x}, {player.y})"

# Set the key handler on the scene
# This is the preferred approach - works on ANY scene, not just the active one
scene.on_key = handle_keys

# Activate the scene
scene.activate()

print("Part 1 loaded! Use WASD or Arrow keys to move.")
