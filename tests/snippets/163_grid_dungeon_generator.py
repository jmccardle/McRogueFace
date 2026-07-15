# mcrf: objects=[Entity,Grid,Scene] verified=0.2.8-dev status=ok
import mcrfpy
import random

# Tile indices (adjust for your tileset)
TILE_FLOOR = 0
TILE_WALL = 1
TILE_DOOR = 2
TILE_STAIRS_DOWN = 3
TILE_STAIRS_UP = 4


class Room:
    """Represents a rectangular room in the dungeon."""

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @property
    def center(self):
        """Return the center point of the room."""
        return (
            self.x + self.width // 2,
            self.y + self.height // 2
        )

    @property
    def inner(self):
        """Return the inner area (excluding walls)."""
        return (
            self.x + 1, self.y + 1,
            self.width - 2, self.height - 2
        )

    def intersects(self, other, padding=1):
        """Check if this room overlaps another (with padding)."""
        return (
            self.x - padding < other.x + other.width + padding and
            self.x + self.width + padding > other.x - padding and
            self.y - padding < other.y + other.height + padding and
            self.y + self.height + padding > other.y - padding
        )


class DungeonGenerator:
    """Procedural dungeon generator with rooms and corridors."""

    def __init__(self, grid, seed=None):
        self.grid = grid
        self.grid_w, self.grid_h = int(grid.grid_size.x), int(grid.grid_size.y)
        self.rooms = []

        if seed is not None:
            random.seed(seed)

    def generate(self, room_count=8, min_room=4, max_room=10):
        """Generate a complete dungeon level."""
        self.rooms = []

        # Fill with walls
        self._fill_walls()

        # Place rooms
        attempts = 0
        max_attempts = room_count * 10

        while len(self.rooms) < room_count and attempts < max_attempts:
            attempts += 1

            # Random room size
            w = random.randint(min_room, max_room)
            h = random.randint(min_room, max_room)

            # Random position (leaving border)
            x = random.randint(1, self.grid_w - w - 2)
            y = random.randint(1, self.grid_h - h - 2)

            room = Room(x, y, w, h)

            # Check overlap
            if not any(room.intersects(r) for r in self.rooms):
                self._carve_room(room)

                # Connect to previous room
                if self.rooms:
                    self._dig_corridor(self.rooms[-1].center, room.center)

                self.rooms.append(room)

        # Place stairs
        if len(self.rooms) >= 2:
            self._place_stairs()

        return self.rooms

    def _fill_walls(self):
        """Fill the entire grid with wall tiles."""
        for x in range(self.grid_w):
            for y in range(self.grid_h):
                point = self.grid.at(x, y)
                point.tilesprite = TILE_WALL
                point.walkable = False
                point.transparent = False

    def _carve_room(self, room):
        """Carve out a room, making it walkable."""
        for x in range(room.x, room.x + room.width):
            for y in range(room.y, room.y + room.height):
                self._set_floor(x, y)

    def _set_floor(self, x, y):
        """Set a single tile as floor."""
        if 0 <= x < self.grid_w and 0 <= y < self.grid_h:
            point = self.grid.at(x, y)
            point.tilesprite = TILE_FLOOR
            point.walkable = True
            point.transparent = True

    def _dig_corridor(self, start, end):
        """Dig an L-shaped corridor between two points."""
        x1, y1 = start
        x2, y2 = end

        # Randomly choose horizontal-first or vertical-first
        if random.random() < 0.5:
            # Horizontal then vertical
            self._dig_horizontal(x1, x2, y1)
            self._dig_vertical(y1, y2, x2)
        else:
            # Vertical then horizontal
            self._dig_vertical(y1, y2, x1)
            self._dig_horizontal(x1, x2, y2)

    def _dig_horizontal(self, x1, x2, y):
        """Dig a horizontal tunnel."""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self._set_floor(x, y)

    def _dig_vertical(self, y1, y2, x):
        """Dig a vertical tunnel."""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self._set_floor(x, y)

    def _place_stairs(self):
        """Place stairs in first and last rooms."""
        # Stairs up in first room
        start_room = self.rooms[0]
        sx, sy = start_room.center
        point = self.grid.at(sx, sy)
        point.tilesprite = TILE_STAIRS_UP

        # Stairs down in last room
        end_room = self.rooms[-1]
        ex, ey = end_room.center
        point = self.grid.at(ex, ey)
        point.tilesprite = TILE_STAIRS_DOWN

        return (sx, sy), (ex, ey)

    def get_spawn_point(self):
        """Get a good spawn point for the player."""
        if self.rooms:
            return self.rooms[0].center
        return (self.grid_w // 2, self.grid_h // 2)

    def get_random_floor(self):
        """Get a random walkable floor tile."""
        floors = []
        for x in range(self.grid_w):
            for y in range(self.grid_h):
                if self.grid.at(x, y).walkable:
                    floors.append((x, y))
        return random.choice(floors) if floors else None


# Setup
scene = mcrfpy.Scene("dungeon")
mcrfpy.current_scene = scene

texture = mcrfpy.default_texture
grid = mcrfpy.Grid(grid_size=(60, 40), texture=texture, pos=(0, 0), size=(960, 640))
scene.children.append(grid)

# Generate dungeon
generator = DungeonGenerator(grid, seed=42)
rooms = generator.generate(room_count=10)

# Place player at spawn
spawn = generator.get_spawn_point()
player = mcrfpy.Entity(spawn, texture, 64)
grid.entities.append(player)

# Place some enemies in random rooms
for i in range(5):
    pos = generator.get_random_floor()
    if pos and pos != spawn:
        enemy = mcrfpy.Entity(pos, texture, 80)
        grid.entities.append(enemy)

# Center camera
grid.center_camera(spawn)

print(f"Generated dungeon with {len(rooms)} rooms")
