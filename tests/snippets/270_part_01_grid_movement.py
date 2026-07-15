# mcrf: objects=[Caption,Color,Entity,Grid,InputState,Key,Scene,Texture] verified=0.2.8-dev status=ok
"""McRogueFace Tutorial - Part 1: The '@' and the Dungeon Grid

Learn to create a grid, place a player entity, and handle movement.
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
# Note: zoom must be set in the constructor to ensure correct initial camera position
grid = mcrfpy.Grid(
    pos=(100, 80),          # Position on screen (pixels)
    size=(640, 480),        # Display size (pixels)
    grid_size=(GRID_WIDTH, GRID_HEIGHT),  # Size in tiles
    texture=texture,
    zoom=2.0                # Zoom level (set here, not after, for correct camera!)
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
    text=f"Player Position: ({player.grid_x}, {player.grid_y})"
)
pos_display.fill_color = mcrfpy.Color(200, 200, 100)
pos_display.font_size = 16
scene.children.append(pos_display)

def handle_keys(key: mcrfpy.Key, action: mcrfpy.InputState) -> None:
    """Handle keyboard input to move the player.

    Args:
        key: The mcrfpy.Key enum value that was pressed
        action: mcrfpy.InputState.PRESSED or mcrfpy.InputState.RELEASED
    """
    # Only respond to key press, not release
    if action != mcrfpy.InputState.PRESSED:
        return

    # Get current player position
    px, py = player.grid_x, player.grid_y

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
    player.grid_x = px
    player.grid_y = py

    # Update the position display
    pos_display.text = f"Player Position: ({player.grid_x}, {player.grid_y})"

# Set the key handler on the scene
# This is the preferred approach - works on ANY scene, not just the active one
scene.on_key = handle_keys

# Activate the scene
scene.activate()

print("Part 1 loaded! Use WASD or Arrow keys to move.")
