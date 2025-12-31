"""McRogueFace - Part 3: Procedural Dungeon Generation

Documentation: https://mcrogueface.github.io/tutorial/part_03_dungeon_generation
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/tutorials/part_03_dungeon_generation/part_03_dungeon_generation.py

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

# =============================================================================
# Room Class
# =============================================================================

class RectangularRoom:
    """A rectangular room with its position and size."""

    def __init__(self, x: int, y: int, width: int, height: int):
        """Create a new room.

        Args:
            x: Left edge X coordinate
            y: Top edge Y coordinate
            width: Room width in tiles
            height: Room height in tiles
        """
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> tuple[int, int]:
        """Return the center coordinates of the room."""
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return center_x, center_y

    @property
    def inner(self) -> tuple[slice, slice]:
        """Return the inner area of the room (excluding walls).

        The inner area is one tile smaller on each side to leave room
        for walls between adjacent rooms.
        """
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: "RectangularRoom") -> bool:
        """Check if this room overlaps with another room.

        Args:
            other: Another RectangularRoom to check against

        Returns:
            True if the rooms overlap, False otherwise
        """
        return (
            self.x1 <= other.x2 and
            self.x2 >= other.x1 and
            self.y1 <= other.y2 and
            self.y2 >= other.y1
        )

# =============================================================================
# Dungeon Generation
# =============================================================================

def fill_with_walls(grid: mcrfpy.Grid) -> None:
    """Fill the entire grid with wall tiles."""
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            cell = grid.at(x, y)
            cell.tilesprite = SPRITE_WALL
            cell.walkable = False
            cell.transparent = False

def carve_room(grid: mcrfpy.Grid, room: RectangularRoom) -> None:
    """Carve out a room by setting its inner tiles to floor.

    Args:
        grid: The game grid
        room: The room to carve
    """
    inner_x, inner_y = room.inner
    for y in range(inner_y.start, inner_y.stop):
        for x in range(inner_x.start, inner_x.stop):
            if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                cell = grid.at(x, y)
                cell.tilesprite = SPRITE_FLOOR
                cell.walkable = True
                cell.transparent = True

def carve_tunnel_horizontal(grid: mcrfpy.Grid, x1: int, x2: int, y: int) -> None:
    """Carve a horizontal tunnel.

    Args:
        grid: The game grid
        x1: Starting X coordinate
        x2: Ending X coordinate
        y: Y coordinate of the tunnel
    """
    start_x = min(x1, x2)
    end_x = max(x1, x2)
    for x in range(start_x, end_x + 1):
        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
            cell = grid.at(x, y)
            cell.tilesprite = SPRITE_FLOOR
            cell.walkable = True
            cell.transparent = True

def carve_tunnel_vertical(grid: mcrfpy.Grid, y1: int, y2: int, x: int) -> None:
    """Carve a vertical tunnel.

    Args:
        grid: The game grid
        y1: Starting Y coordinate
        y2: Ending Y coordinate
        x: X coordinate of the tunnel
    """
    start_y = min(y1, y2)
    end_y = max(y1, y2)
    for y in range(start_y, end_y + 1):
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
    """Carve an L-shaped tunnel between two points.

    Randomly chooses to go horizontal-then-vertical or vertical-then-horizontal.

    Args:
        grid: The game grid
        start: Starting (x, y) coordinates
        end: Ending (x, y) coordinates
    """
    x1, y1 = start
    x2, y2 = end

    # Randomly choose whether to go horizontal or vertical first
    if random.random() < 0.5:
        # Horizontal first, then vertical
        carve_tunnel_horizontal(grid, x1, x2, y1)
        carve_tunnel_vertical(grid, y1, y2, x2)
    else:
        # Vertical first, then horizontal
        carve_tunnel_vertical(grid, y1, y2, x1)
        carve_tunnel_horizontal(grid, x1, x2, y2)

def generate_dungeon(grid: mcrfpy.Grid) -> tuple[int, int]:
    """Generate a dungeon with rooms and tunnels.

    Args:
        grid: The game grid to generate the dungeon in

    Returns:
        The (x, y) coordinates where the player should start
    """
    # Start with all walls
    fill_with_walls(grid)

    rooms: list[RectangularRoom] = []

    for _ in range(MAX_ROOMS):
        # Random room dimensions
        room_width = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        room_height = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)

        # Random position (leaving 1-tile border)
        x = random.randint(1, GRID_WIDTH - room_width - 2)
        y = random.randint(1, GRID_HEIGHT - room_height - 2)

        new_room = RectangularRoom(x, y, room_width, room_height)

        # Check for overlap with existing rooms
        overlaps = False
        for other_room in rooms:
            if new_room.intersects(other_room):
                overlaps = True
                break

        if overlaps:
            continue  # Skip this room, try another

        # No overlap - carve out the room
        carve_room(grid, new_room)

        # Connect to previous room with a tunnel
        if rooms:
            # Tunnel from this room's center to the previous room's center
            carve_l_tunnel(grid, new_room.center, rooms[-1].center)

        rooms.append(new_room)

    # Return the center of the first room as the player start position
    if rooms:
        return rooms[0].center
    else:
        # Fallback if no rooms were generated
        return GRID_WIDTH // 2, GRID_HEIGHT // 2

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
    texture=texture
)
grid.zoom = 1.0

# Generate the dungeon and get player start position
player_start_x, player_start_y = generate_dungeon(grid)

# Create the player at the starting position
player = mcrfpy.Entity(
    grid_pos=(player_start_x, player_start_y),
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
    pos=(50, 15),
    text="Part 3: Procedural Dungeon Generation"
)
title.fill_color = mcrfpy.Color(255, 255, 255)
title.font_size = 24
scene.children.append(title)

instructions = mcrfpy.Caption(
    pos=(50, 50),
    text="WASD/Arrows: Move | R: Regenerate dungeon | Escape: Quit"
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

room_display = mcrfpy.Caption(
    pos=(400, 660),
    text="Press R to regenerate the dungeon"
)
room_display.fill_color = mcrfpy.Color(100, 200, 100)
room_display.font_size = 16
scene.children.append(room_display)

# =============================================================================
# Input Handling
# =============================================================================

def regenerate_dungeon() -> None:
    """Generate a new dungeon and reposition the player."""
    new_x, new_y = generate_dungeon(grid)
    player.x = new_x
    player.y = new_y
    pos_display.text = f"Position: ({new_x}, {new_y})"
    room_display.text = "New dungeon generated!"

def handle_keys(key: str, action: str) -> None:
    """Handle keyboard input."""
    if action != "start":
        return

    px, py = int(player.x), int(player.y)
    new_x, new_y = px, py

    if key == "W" or key == "Up":
        new_y -= 1
    elif key == "S" or key == "Down":
        new_y += 1
    elif key == "A" or key == "Left":
        new_x -= 1
    elif key == "D" or key == "Right":
        new_x += 1
    elif key == "R":
        regenerate_dungeon()
        return
    elif key == "Escape":
        mcrfpy.exit()
        return
    else:
        return

    if can_move_to(grid, new_x, new_y):
        player.x = new_x
        player.y = new_y
        pos_display.text = f"Position: ({new_x}, {new_y})"

scene.on_key = handle_keys

# =============================================================================
# Start the Game
# =============================================================================

scene.activate()
print("Part 3 loaded! Explore the dungeon or press R to regenerate.")