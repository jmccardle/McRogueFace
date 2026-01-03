"""
dungeon.py - Procedural Dungeon Generation

This module provides classic roguelike dungeon generation using the
"rooms and corridors" algorithm:

1. Generate random non-overlapping rectangular rooms
2. Connect rooms with L-shaped corridors
3. Mark tiles as walkable/transparent based on terrain type

The algorithm is simple but effective, producing dungeons similar to
the original Rogue game.
"""

from __future__ import annotations
import random
from typing import Iterator, Tuple, List, TYPE_CHECKING

if TYPE_CHECKING:
    import mcrfpy

from constants import (
    MAP_WIDTH, MAP_HEIGHT,
    ROOM_MIN_SIZE, ROOM_MAX_SIZE, MAX_ROOMS,
    SPRITE_FLOOR, SPRITE_WALL,
    COLOR_FLOOR, COLOR_WALL,
)


class RectangularRoom:
    """
    A rectangular room in the dungeon.

    This class represents a single room and provides utilities for
    working with room geometry. Rooms are defined by their top-left
    corner (x1, y1) and bottom-right corner (x2, y2).

    Attributes:
        x1, y1: Top-left corner coordinates
        x2, y2: Bottom-right corner coordinates
    """

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        """
        Create a new rectangular room.

        Args:
            x: X coordinate of the top-left corner
            y: Y coordinate of the top-left corner
            width: Width of the room in tiles
            height: Height of the room in tiles
        """
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        """
        Return the center coordinates of the room.

        This is useful for connecting rooms with corridors and
        for placing the player in the starting room.

        Returns:
            Tuple of (center_x, center_y)
        """
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        """
        Return the inner area of the room as a pair of slices.

        The inner area excludes the walls (1 tile border), giving
        the floor area where entities can be placed.

        Returns:
            Tuple of (x_slice, y_slice) for array indexing
        """
        # Add 1 to exclude the walls on all sides
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: RectangularRoom) -> bool:
        """
        Check if this room overlaps with another room.

        Used during generation to ensure rooms don't overlap.

        Args:
            other: Another RectangularRoom to check against

        Returns:
            True if the rooms overlap, False otherwise
        """
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )

    def inner_tiles(self) -> Iterator[Tuple[int, int]]:
        """
        Iterate over all floor tile coordinates in the room.

        Yields coordinates for the interior of the room (excluding walls).

        Yields:
            Tuples of (x, y) coordinates
        """
        for x in range(self.x1 + 1, self.x2):
            for y in range(self.y1 + 1, self.y2):
                yield x, y


def tunnel_between(
    start: Tuple[int, int],
    end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """
    Generate an L-shaped tunnel between two points.

    The tunnel goes horizontally first, then vertically (or vice versa,
    chosen randomly). This creates the classic roguelike corridor style.

    Args:
        start: Starting (x, y) coordinates
        end: Ending (x, y) coordinates

    Yields:
        Tuples of (x, y) coordinates for each tile in the tunnel
    """
    x1, y1 = start
    x2, y2 = end

    # Randomly choose whether to go horizontal-first or vertical-first
    if random.random() < 0.5:
        # Horizontal first, then vertical
        corner_x, corner_y = x2, y1
    else:
        # Vertical first, then horizontal
        corner_x, corner_y = x1, y2

    # Generate the horizontal segment
    for x in range(min(x1, corner_x), max(x1, corner_x) + 1):
        yield x, y1

    # Generate the vertical segment
    for y in range(min(y1, corner_y), max(y1, corner_y) + 1):
        yield corner_x, y

    # Generate to the endpoint (if needed)
    for x in range(min(corner_x, x2), max(corner_x, x2) + 1):
        yield x, corner_y

    for y in range(min(corner_y, y2), max(corner_y, y2) + 1):
        yield x2, y


def generate_dungeon(
    max_rooms: int = MAX_ROOMS,
    room_min_size: int = ROOM_MIN_SIZE,
    room_max_size: int = ROOM_MAX_SIZE,
    map_width: int = MAP_WIDTH,
    map_height: int = MAP_HEIGHT,
) -> List[RectangularRoom]:
    """
    Generate a dungeon using the rooms-and-corridors algorithm.

    This function creates a list of non-overlapping rooms. The actual
    tile data should be applied to a Grid using populate_grid().

    Algorithm:
    1. Try to place MAX_ROOMS rooms randomly
    2. Reject rooms that overlap existing rooms
    3. Connect each new room to the previous room with a corridor

    Args:
        max_rooms: Maximum number of rooms to generate
        room_min_size: Minimum room dimension
        room_max_size: Maximum room dimension
        map_width: Width of the dungeon in tiles
        map_height: Height of the dungeon in tiles

    Returns:
        List of RectangularRoom objects representing the dungeon layout
    """
    rooms: List[RectangularRoom] = []

    for _ in range(max_rooms):
        # Random room dimensions
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        # Random position (ensuring room fits within map bounds)
        x = random.randint(0, map_width - room_width - 1)
        y = random.randint(0, map_height - room_height - 1)

        new_room = RectangularRoom(x, y, room_width, room_height)

        # Check if this room overlaps with any existing room
        if any(new_room.intersects(other) for other in rooms):
            continue  # Skip this room, try again

        # Room is valid, add it
        rooms.append(new_room)

    return rooms


def populate_grid(grid: mcrfpy.Grid, rooms: List[RectangularRoom]) -> None:
    """
    Apply dungeon layout to a McRogueFace Grid.

    This function:
    1. Fills the entire grid with walls
    2. Carves out floor tiles for each room
    3. Carves corridors connecting adjacent rooms
    4. Sets walkable/transparent flags appropriately

    Args:
        grid: The McRogueFace Grid to populate
        rooms: List of RectangularRoom objects from generate_dungeon()
    """
    grid_width, grid_height = grid.grid_size

    # Step 1: Fill entire map with walls
    for x in range(grid_width):
        for y in range(grid_height):
            point = grid.at(x, y)
            point.tilesprite = SPRITE_WALL
            point.walkable = False
            point.transparent = False
            point.color = COLOR_WALL

    # Step 2: Carve out rooms
    for room in rooms:
        for x, y in room.inner_tiles():
            # Bounds check (room might extend past grid)
            if 0 <= x < grid_width and 0 <= y < grid_height:
                point = grid.at(x, y)
                point.tilesprite = SPRITE_FLOOR
                point.walkable = True
                point.transparent = True
                point.color = COLOR_FLOOR

    # Step 3: Carve corridors between adjacent rooms
    for i in range(1, len(rooms)):
        # Connect each room to the previous room
        start = rooms[i - 1].center
        end = rooms[i].center

        for x, y in tunnel_between(start, end):
            if 0 <= x < grid_width and 0 <= y < grid_height:
                point = grid.at(x, y)
                point.tilesprite = SPRITE_FLOOR
                point.walkable = True
                point.transparent = True
                point.color = COLOR_FLOOR


def get_random_floor_position(
    grid: mcrfpy.Grid,
    rooms: List[RectangularRoom],
    exclude_first_room: bool = False
) -> Tuple[int, int]:
    """
    Get a random walkable floor position for entity placement.

    This is useful for placing enemies, items, or other entities
    in valid floor locations.

    Args:
        grid: The populated Grid to search
        rooms: List of rooms (used for faster random selection)
        exclude_first_room: If True, won't return positions from the
                          first room (where the player usually starts)

    Returns:
        Tuple of (x, y) coordinates of a walkable floor tile
    """
    available_rooms = rooms[1:] if exclude_first_room and len(rooms) > 1 else rooms

    if not available_rooms:
        # Fallback: find any walkable tile
        grid_width, grid_height = grid.grid_size
        walkable_tiles = []
        for x in range(grid_width):
            for y in range(grid_height):
                if grid.at(x, y).walkable:
                    walkable_tiles.append((x, y))
        return random.choice(walkable_tiles) if walkable_tiles else (1, 1)

    # Pick a random room and a random position within it
    room = random.choice(available_rooms)
    floor_tiles = list(room.inner_tiles())
    return random.choice(floor_tiles)


def get_spawn_positions(
    rooms: List[RectangularRoom],
    count: int,
    exclude_first_room: bool = True
) -> List[Tuple[int, int]]:
    """
    Get multiple spawn positions for enemies.

    Distributes enemies across different rooms for better gameplay.

    Args:
        rooms: List of rooms from dungeon generation
        count: Number of positions to generate
        exclude_first_room: If True, won't spawn in the player's starting room

    Returns:
        List of (x, y) coordinate tuples
    """
    available_rooms = rooms[1:] if exclude_first_room and len(rooms) > 1 else rooms

    if not available_rooms:
        return []

    positions = []
    for i in range(count):
        # Cycle through rooms to distribute enemies
        room = available_rooms[i % len(available_rooms)]
        floor_tiles = list(room.inner_tiles())

        # Try to avoid placing on the same tile
        available_tiles = [t for t in floor_tiles if t not in positions]
        if available_tiles:
            positions.append(random.choice(available_tiles))
        elif floor_tiles:
            positions.append(random.choice(floor_tiles))

    return positions
