# mcrf: objects=[Grid,Scene] verified=0.3.6-dev status=ok
import mcrfpy
import random

TILE_WALL = 1


class Room:
    """Represents a rectangular room in the dungeon."""

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @property
    def center(self):
        return (self.x + self.width // 2, self.y + self.height // 2)


def carve_room(grid, room):
    """Make every tile of the room floor."""
    for rx in range(room.x, room.x + room.width):
        for ry in range(room.y, room.y + room.height):
            point = grid.at(rx, ry)
            point.tilesprite = 0
            point.walkable = True
            point.transparent = True


def connect_points(grid, a, b):
    """Dig an L-shaped tunnel between two points."""
    for tx in range(min(a[0], b[0]), max(a[0], b[0]) + 1):
        carve_room(grid, Room(tx, a[1], 1, 1))
    for ty in range(min(a[1], b[1]), max(a[1], b[1]) + 1):
        carve_room(grid, Room(b[0], ty, 1, 1))


scene = mcrfpy.Scene("dungeon")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(60, 40), texture=mcrfpy.default_texture, pos=(0, 0), size=(960, 640))
scene.children.append(grid)

# region: bsp
class BSPNode:
    """Node in a BSP tree for dungeon generation."""

    MIN_SIZE = 6

    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.left = None
        self.right = None
        self.room = None

    def split(self):
        """Recursively split this node."""
        if self.left or self.right:
            return False

        # Choose split direction
        if self.w > self.h and self.w / self.h >= 1.25:
            horizontal = False
        elif self.h > self.w and self.h / self.w >= 1.25:
            horizontal = True
        else:
            horizontal = random.random() < 0.5

        max_size = (self.h if horizontal else self.w) - self.MIN_SIZE
        if max_size <= self.MIN_SIZE:
            return False

        split = random.randint(self.MIN_SIZE, max_size)

        if horizontal:
            self.left = BSPNode(self.x, self.y, self.w, split)
            self.right = BSPNode(self.x, self.y + split, self.w, self.h - split)
        else:
            self.left = BSPNode(self.x, self.y, split, self.h)
            self.right = BSPNode(self.x + split, self.y, self.w - split, self.h)

        return True

    def create_rooms(self, grid):
        """Create rooms in leaf nodes and connect siblings."""
        if self.left or self.right:
            if self.left:
                self.left.create_rooms(grid)
            if self.right:
                self.right.create_rooms(grid)

            # Connect children
            if self.left and self.right:
                left_room = self.left.get_room()
                right_room = self.right.get_room()
                if left_room and right_room:
                    connect_points(grid, left_room.center, right_room.center)
        else:
            # Leaf node - create room
            w = random.randint(3, self.w - 2)
            h = random.randint(3, self.h - 2)
            x = self.x + random.randint(1, self.w - w - 1)
            y = self.y + random.randint(1, self.h - h - 1)
            self.room = Room(x, y, w, h)
            carve_room(grid, self.room)

    def get_room(self):
        """Get a room from this node or its children."""
        if self.room:
            return self.room

        left_room = self.left.get_room() if self.left else None
        right_room = self.right.get_room() if self.right else None

        if left_room and right_room:
            return random.choice([left_room, right_room])
        return left_room or right_room


def generate_bsp_dungeon(grid, iterations=4):
    """Generate a BSP-based dungeon."""
    grid_w, grid_h = int(grid.grid_size.x), int(grid.grid_size.y)

    # Fill with walls
    for x in range(grid_w):
        for y in range(grid_h):
            point = grid.at(x, y)
            point.tilesprite = TILE_WALL
            point.walkable = False
            point.transparent = False

    # Build BSP tree
    root = BSPNode(0, 0, grid_w, grid_h)
    nodes = [root]

    for _ in range(iterations):
        new_nodes = []
        for node in nodes:
            if node.split():
                new_nodes.extend([node.left, node.right])
        nodes = new_nodes or nodes

    # Create rooms and corridors
    root.create_rooms(grid)

    # Collect all rooms
    rooms = []
    def collect_rooms(node):
        if node.room:
            rooms.append(node.room)
        if node.left:
            collect_rooms(node.left)
        if node.right:
            collect_rooms(node.right)

    collect_rooms(root)
    return rooms
# endregion

random.seed(42)
rooms = generate_bsp_dungeon(grid)
print(f"BSP dungeon with {len(rooms)} rooms")
