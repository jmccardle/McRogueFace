"""
dungeon.py - Procedural Dungeon Generation for McRogueFace

Generates a roguelike dungeon with rooms connected by corridors.
Includes stairs placement for multi-level progression.
"""

import random
from dataclasses import dataclass
from typing import List, Tuple, Optional

from constants import (
    DUNGEON_WIDTH, DUNGEON_HEIGHT,
    ROOM_MIN_SIZE, ROOM_MAX_SIZE, MAX_ROOMS,
    SPRITE_FLOOR, SPRITE_WALL, SPRITE_STAIRS_DOWN,
    MAX_ENEMIES_PER_ROOM, MIN_ENEMIES_PER_ROOM,
    ENEMY_SPAWN_WEIGHTS, DEFAULT_SPAWN_WEIGHTS
)


@dataclass
class Rect:
    """A rectangle representing a room in the dungeon."""
    x: int
    y: int
    width: int
    height: int

    @property
    def x2(self) -> int:
        return self.x + self.width

    @property
    def y2(self) -> int:
        return self.y + self.height

    @property
    def center(self) -> Tuple[int, int]:
        """Return the center coordinates of this room."""
        center_x = (self.x + self.x2) // 2
        center_y = (self.y + self.y2) // 2
        return center_x, center_y

    def intersects(self, other: 'Rect') -> bool:
        """Check if this room overlaps with another (with 1 tile buffer)."""
        return (self.x <= other.x2 + 1 and self.x2 + 1 >= other.x and
                self.y <= other.y2 + 1 and self.y2 + 1 >= other.y)

    def inner(self) -> Tuple[int, int, int, int]:
        """Return the inner area of the room (excluding walls)."""
        return self.x + 1, self.y + 1, self.width - 2, self.height - 2


class Tile:
    """Represents a single tile in the dungeon."""

    def __init__(self, walkable: bool = False, transparent: bool = False,
                 sprite: int = SPRITE_WALL):
        self.walkable = walkable
        self.transparent = transparent
        self.sprite = sprite
        self.explored = False
        self.visible = False


class Dungeon:
    """
    The dungeon map with rooms, corridors, and tile data.

    Attributes:
        width: Width of the dungeon in tiles
        height: Height of the dungeon in tiles
        level: Current dungeon depth
        tiles: 2D array of Tile objects
        rooms: List of rooms (Rect objects)
        player_start: Starting position for the player
        stairs_pos: Position of the stairs down
    """

    def __init__(self, width: int = DUNGEON_WIDTH, height: int = DUNGEON_HEIGHT,
                 level: int = 1):
        self.width = width
        self.height = height
        self.level = level
        self.tiles: List[List[Tile]] = []
        self.rooms: List[Rect] = []
        self.player_start: Tuple[int, int] = (0, 0)
        self.stairs_pos: Tuple[int, int] = (0, 0)

        # Initialize all tiles as walls
        self._init_tiles()

    def _init_tiles(self) -> None:
        """Fill the dungeon with wall tiles."""
        self.tiles = [
            [Tile(walkable=False, transparent=False, sprite=SPRITE_WALL)
             for _ in range(self.height)]
            for _ in range(self.width)
        ]

    def in_bounds(self, x: int, y: int) -> bool:
        """Check if coordinates are within dungeon bounds."""
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a tile can be walked on."""
        if not self.in_bounds(x, y):
            return False
        return self.tiles[x][y].walkable

    def is_transparent(self, x: int, y: int) -> bool:
        """Check if a tile allows light to pass through."""
        if not self.in_bounds(x, y):
            return False
        return self.tiles[x][y].transparent

    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        """Get the tile at the given position."""
        if not self.in_bounds(x, y):
            return None
        return self.tiles[x][y]

    def set_tile(self, x: int, y: int, walkable: bool, transparent: bool,
                 sprite: int) -> None:
        """Set properties of a tile."""
        if self.in_bounds(x, y):
            tile = self.tiles[x][y]
            tile.walkable = walkable
            tile.transparent = transparent
            tile.sprite = sprite

    def carve_room(self, room: Rect) -> None:
        """Carve out a room in the dungeon (make tiles walkable)."""
        inner_x, inner_y, inner_w, inner_h = room.inner()

        for x in range(inner_x, inner_x + inner_w):
            for y in range(inner_y, inner_y + inner_h):
                self.set_tile(x, y, walkable=True, transparent=True,
                             sprite=SPRITE_FLOOR)

    def carve_tunnel_h(self, x1: int, x2: int, y: int) -> None:
        """Carve a horizontal tunnel."""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.set_tile(x, y, walkable=True, transparent=True,
                         sprite=SPRITE_FLOOR)

    def carve_tunnel_v(self, y1: int, y2: int, x: int) -> None:
        """Carve a vertical tunnel."""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.set_tile(x, y, walkable=True, transparent=True,
                         sprite=SPRITE_FLOOR)

    def connect_rooms(self, room1: Rect, room2: Rect) -> None:
        """Connect two rooms with an L-shaped corridor."""
        x1, y1 = room1.center
        x2, y2 = room2.center

        # Randomly choose to go horizontal then vertical, or vice versa
        if random.random() < 0.5:
            self.carve_tunnel_h(x1, x2, y1)
            self.carve_tunnel_v(y1, y2, x2)
        else:
            self.carve_tunnel_v(y1, y2, x1)
            self.carve_tunnel_h(x1, x2, y2)

    def place_stairs(self) -> None:
        """Place stairs in the last room."""
        if self.rooms:
            # Stairs go in the center of the last room
            self.stairs_pos = self.rooms[-1].center
            x, y = self.stairs_pos
            self.set_tile(x, y, walkable=True, transparent=True,
                         sprite=SPRITE_STAIRS_DOWN)

    def generate(self) -> None:
        """Generate the dungeon using BSP-style room placement."""
        self._init_tiles()
        self.rooms.clear()

        for _ in range(MAX_ROOMS):
            # Random room dimensions
            w = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)

            # Random position (ensure room fits in dungeon)
            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)

            new_room = Rect(x, y, w, h)

            # Check for intersections with existing rooms
            if any(new_room.intersects(other) for other in self.rooms):
                continue

            # Room is valid - carve it out
            self.carve_room(new_room)

            if self.rooms:
                # Connect to previous room
                self.connect_rooms(self.rooms[-1], new_room)
            else:
                # First room - player starts here
                self.player_start = new_room.center

            self.rooms.append(new_room)

        # Place stairs in the last room
        self.place_stairs()

    def get_spawn_positions(self) -> List[Tuple[int, int]]:
        """
        Get valid spawn positions for enemies.
        Returns positions from all rooms except the first (player start).
        """
        positions = []

        for room in self.rooms[1:]:  # Skip first room (player start)
            inner_x, inner_y, inner_w, inner_h = room.inner()

            for x in range(inner_x, inner_x + inner_w):
                for y in range(inner_y, inner_y + inner_h):
                    # Don't spawn on stairs
                    if (x, y) != self.stairs_pos:
                        positions.append((x, y))

        return positions

    def get_enemy_spawns(self) -> List[Tuple[str, int, int]]:
        """
        Determine which enemies to spawn and where.
        Returns list of (enemy_type, x, y) tuples.
        """
        spawns = []

        # Get spawn weights for this level
        weights = ENEMY_SPAWN_WEIGHTS.get(self.level, DEFAULT_SPAWN_WEIGHTS)

        # Create weighted list for random selection
        enemy_types = []
        for enemy_type, weight in weights:
            enemy_types.extend([enemy_type] * weight)

        # Spawn enemies in each room (except the first)
        for room in self.rooms[1:]:
            num_enemies = random.randint(MIN_ENEMIES_PER_ROOM, MAX_ENEMIES_PER_ROOM)

            # Scale up enemies slightly with dungeon level
            num_enemies = min(num_enemies + (self.level - 1) // 2, MAX_ENEMIES_PER_ROOM + 2)

            inner_x, inner_y, inner_w, inner_h = room.inner()
            used_positions = set()

            for _ in range(num_enemies):
                # Find an unused position
                attempts = 0
                while attempts < 20:
                    x = random.randint(inner_x, inner_x + inner_w - 1)
                    y = random.randint(inner_y, inner_y + inner_h - 1)

                    if (x, y) not in used_positions and (x, y) != self.stairs_pos:
                        enemy_type = random.choice(enemy_types)
                        spawns.append((enemy_type, x, y))
                        used_positions.add((x, y))
                        break

                    attempts += 1

        return spawns

    def apply_to_grid(self, grid) -> None:
        """
        Apply the dungeon data to a McRogueFace Grid object.

        Args:
            grid: A mcrfpy.Grid object to update
        """
        for x in range(self.width):
            for y in range(self.height):
                tile = self.tiles[x][y]
                point = grid.at(x, y)
                point.tilesprite = tile.sprite
                point.walkable = tile.walkable
                point.transparent = tile.transparent


def generate_dungeon(level: int = 1) -> Dungeon:
    """
    Convenience function to generate a new dungeon.

    Args:
        level: The dungeon depth (affects enemy spawns)

    Returns:
        A fully generated Dungeon object
    """
    dungeon = Dungeon(level=level)
    dungeon.generate()
    return dungeon
