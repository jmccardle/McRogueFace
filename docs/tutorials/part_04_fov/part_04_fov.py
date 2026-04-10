"""McRogueFace - Part 4: Field of View

Documentation: https://mcrogueface.github.io/tutorial/part_04_fov
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/tutorials/part_04_fov/part_04_fov.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy
import random

# =============================================================================
# Constants
# =============================================================================

# Sprite indices for CP437 tileset
SPRITE_WALL = 35    # '#' - wall
SPRITE_FLOOR = 46   # '.' - floor
SPRITE_PLAYER = 64  # '@' - player

# Grid dimensions
GRID_WIDTH = 50
GRID_HEIGHT = 35

# Room generation parameters
ROOM_MIN_SIZE = 6
ROOM_MAX_SIZE = 12
MAX_ROOMS = 8

# FOV settings
FOV_RADIUS = 8

# Visibility colors (applied as overlays)
COLOR_VISIBLE = mcrfpy.Color(0, 0, 0, 0)           # Fully transparent - show tile
COLOR_DISCOVERED = mcrfpy.Color(0, 0, 40, 180)     # Dark blue tint - dimmed
COLOR_UNKNOWN = mcrfpy.Color(0, 0, 0, 255)         # Solid black - hidden

# =============================================================================
# Room Class (from Part 3)
# =============================================================================

class RectangularRoom:
    """A rectangular room with its position and size."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> tuple[int, int]:
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return center_x, center_y

    @property
    def inner(self) -> tuple[slice, slice]:
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: "RectangularRoom") -> bool:
        return (
            self.x1 <= other.x2 and
            self.x2 >= other.x1 and
            self.y1 <= other.y2 and
            self.y2 >= other.y1
        )

# =============================================================================
# Exploration Tracking
# =============================================================================

# Note: The ColorLayer's draw_fov() method tracks exploration state
# internally - tiles that have been visible at least once are rendered
# with the 'discovered' color. No manual tracking needed!

# =============================================================================
# Dungeon Generation (from Part 3, with transparent property)
# =============================================================================

def fill_with_walls(grid: mcrfpy.Grid) -> None:
    """Fill the entire grid with wall tiles."""
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            cell = grid.at(x, y)
            cell.tilesprite = SPRITE_WALL
            cell.walkable = False
            cell.transparent = False  # Walls block line of sight

def carve_room(grid: mcrfpy.Grid, room: RectangularRoom) -> None:
    """Carve out a room by setting its inner tiles to floor."""
    inner_x, inner_y = room.inner
    for y in range(inner_y.start, inner_y.stop):
        for x in range(inner_x.start, inner_x.stop):
            if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                cell = grid.at(x, y)
                cell.tilesprite = SPRITE_FLOOR
                cell.walkable = True
                cell.transparent = True  # Floors allow line of sight

def carve_tunnel_horizontal(grid: mcrfpy.Grid, x1: int, x2: int, y: int) -> None:
    """Carve a horizontal tunnel."""
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
            cell = grid.at(x, y)
            cell.tilesprite = SPRITE_FLOOR
            cell.walkable = True
            cell.transparent = True

def carve_tunnel_vertical(grid: mcrfpy.Grid, y1: int, y2: int, x: int) -> None:
    """Carve a vertical tunnel."""
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
            cell = grid.at(x, y)
            cell.tilesprite = SPRITE_FLOOR
            cell.walkable = True
            cell.transparent = True

def carve_l_tunnel(
    grid: mcrfpy.Grid,
    start: tuple[int, int],
    end: tuple[int, int]
) -> None:
    """Carve an L-shaped tunnel between two points."""
    x1, y1 = start
    x2, y2 = end

    if random.random() < 0.5:
        carve_tunnel_horizontal(grid, x1, x2, y1)
        carve_tunnel_vertical(grid, y1, y2, x2)
    else:
        carve_tunnel_vertical(grid, y1, y2, x1)
        carve_tunnel_horizontal(grid, x1, x2, y2)

def generate_dungeon(grid: mcrfpy.Grid) -> tuple[int, int]:
    """Generate a dungeon with rooms and tunnels."""
    fill_with_walls(grid)

    rooms: list[RectangularRoom] = []

    for _ in range(MAX_ROOMS):
        room_width = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        room_height = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x = random.randint(1, GRID_WIDTH - room_width - 2)
        y = random.randint(1, GRID_HEIGHT - room_height - 2)

        new_room = RectangularRoom(x, y, room_width, room_height)

        overlaps = False
        for other_room in rooms:
            if new_room.intersects(other_room):
                overlaps = True
                break

        if overlaps:
            continue

        carve_room(grid, new_room)
        if rooms:
            carve_l_tunnel(grid, new_room.center, rooms[-1].center)
        rooms.append(new_room)

    if rooms:
        return rooms[0].center
    return GRID_WIDTH // 2, GRID_HEIGHT // 2

# =============================================================================
# Field of View
# =============================================================================

def update_fov(grid: mcrfpy.Grid, fov_layer, player_x: int, player_y: int) -> None:
    """Update the field of view visualization.

    Uses the ColorLayer's built-in draw_fov() method, which computes FOV
    via libtcod and paints visibility colors in a single call. The layer
    tracks explored state automatically.

    Args:
        grid: The game grid
        fov_layer: The ColorLayer for FOV visualization
        player_x: Player's X position
        player_y: Player's Y position
    """
    # draw_fov computes FOV and paints the color layer in one step.
    # It tracks explored state internally so previously-seen tiles stay dimmed.
    fov_layer.draw_fov(
        (player_x, player_y),
        radius=FOV_RADIUS,
        visible=COLOR_VISIBLE,
        discovered=COLOR_DISCOVERED,
        unknown=COLOR_UNKNOWN
    )

# =============================================================================
# Collision Detection
# =============================================================================

def can_move_to(grid: mcrfpy.Grid, x: int, y: int) -> bool:
    """Check if a position is valid for movement."""
    if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
        return False
    return grid.at(x, y).walkable

# =============================================================================
# Game Setup
# =============================================================================

# Create the scene
scene = mcrfpy.Scene("game")

# Load texture
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

# Create the grid
grid = mcrfpy.Grid(
    pos=(50, 80),
    size=(800, 560),
    grid_size=(GRID_WIDTH, GRID_HEIGHT),
    texture=texture,
    zoom=1.0
)

# Generate the dungeon
player_start_x, player_start_y = generate_dungeon(grid)

# Add a color layer for FOV visualization (below entities)
# Create the layer object, then attach it to the grid
fov_layer = mcrfpy.ColorLayer(z_index=-1, name="fov")
grid.add_layer(fov_layer)

# Initialize the FOV layer to all black (unknown)
fov_layer.fill(COLOR_UNKNOWN)

# Create the player
player = mcrfpy.Entity(
    grid_pos=(player_start_x, player_start_y),
    texture=texture,
    sprite_index=SPRITE_PLAYER
)
grid.entities.append(player)

# Calculate initial FOV
update_fov(grid, fov_layer, player_start_x, player_start_y)

# Add grid to scene
scene.children.append(grid)

# =============================================================================
# UI Elements
# =============================================================================

title = mcrfpy.Caption(
    pos=(50, 15),
    text="Part 4: Field of View"
)
title.fill_color = mcrfpy.Color(255, 255, 255)
title.font_size = 24
scene.children.append(title)

instructions = mcrfpy.Caption(
    pos=(50, 50),
    text="WASD/Arrows: Move | R: Regenerate | Escape: Quit"
)
instructions.fill_color = mcrfpy.Color(180, 180, 180)
instructions.font_size = 16
scene.children.append(instructions)

pos_display = mcrfpy.Caption(
    pos=(50, 660),
    text=f"Position: ({int(player.x)}, {int(player.y)})"
)
pos_display.fill_color = mcrfpy.Color(200, 200, 100)
pos_display.font_size = 16
scene.children.append(pos_display)

fov_display = mcrfpy.Caption(
    pos=(400, 660),
    text=f"FOV Radius: {FOV_RADIUS}"
)
fov_display.fill_color = mcrfpy.Color(100, 200, 100)
fov_display.font_size = 16
scene.children.append(fov_display)

# =============================================================================
# Input Handling
# =============================================================================

def regenerate_dungeon() -> None:
    """Generate a new dungeon and reposition the player."""
    new_x, new_y = generate_dungeon(grid)
    player.x = new_x
    player.y = new_y

    # Reset FOV layer to unknown
    fov_layer.fill(COLOR_UNKNOWN)

    # Calculate new FOV
    update_fov(grid, fov_layer, new_x, new_y)
    pos_display.text = f"Position: ({new_x}, {new_y})"

def handle_keys(key, action) -> None:
    """Handle keyboard input."""
    if action != mcrfpy.InputState.PRESSED:
        return

    px, py = int(player.x), int(player.y)
    new_x, new_y = px, py

    if key == mcrfpy.Key.W or key == mcrfpy.Key.UP:
        new_y -= 1
    elif key == mcrfpy.Key.S or key == mcrfpy.Key.DOWN:
        new_y += 1
    elif key == mcrfpy.Key.A or key == mcrfpy.Key.LEFT:
        new_x -= 1
    elif key == mcrfpy.Key.D or key == mcrfpy.Key.RIGHT:
        new_x += 1
    elif key == mcrfpy.Key.R:
        regenerate_dungeon()
        return
    elif key == mcrfpy.Key.ESCAPE:
        mcrfpy.exit()
        return
    else:
        return

    if can_move_to(grid, new_x, new_y):
        player.x = new_x
        player.y = new_y
        pos_display.text = f"Position: ({new_x}, {new_y})"

        # Update FOV after movement
        update_fov(grid, fov_layer, new_x, new_y)

scene.on_key = handle_keys

# =============================================================================
# Start the Game
# =============================================================================

scene.activate()
print("Part 4 loaded! Explore the dungeon - watch the fog of war!")