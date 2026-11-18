# mcrf: objects=[Grid,Scene] verified=0.3.6 status=ok
import mcrfpy
import random



def rooms_overlap(a, b):
    """True if two (x, y, w, h) rooms overlap, with one tile of padding."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return (ax - 1 < bx + bw + 1 and ax + aw + 1 > bx - 1 and
            ay - 1 < by + bh + 1 and ay + ah + 1 > by - 1)


def carve_room(grid, x, y, w, h):
    """Make every tile of the room floor."""
    for rx in range(x, x + w):
        for ry in range(y, y + h):
            point = grid.at(rx, ry)
            point.tilesprite = 0
            point.walkable = True
            point.transparent = True


def connect_rooms(grid, a, b):
    """Dig an L-shaped tunnel between the centers of two rooms."""
    ax, ay = a[0] + a[2] // 2, a[1] + a[3] // 2
    bx, by = b[0] + b[2] // 2, b[1] + b[3] // 2
    for tx in range(min(ax, bx), max(ax, bx) + 1):
        carve_room(grid, tx, ay, 1, 1)
    for ty in range(min(ay, by), max(ay, by) + 1):
        carve_room(grid, bx, ty, 1, 1)


scene = mcrfpy.Scene("dungeon")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(60, 40), texture=mcrfpy.default_texture, pos=(0, 0), size=(960, 640))
scene.children.append(grid)

# region: quickstart
import mcrfpy
import random

def generate_dungeon(grid, room_count=8):
    """Generate a dungeon with rooms and corridors."""
    rooms = []
    grid_w, grid_h = int(grid.grid_size.x), int(grid.grid_size.y)

    # Fill with walls first
    for x in range(grid_w):
        for y in range(grid_h):
            point = grid.at(x, y)
            point.tilesprite = 1  # Wall tile
            point.walkable = False
            point.transparent = False

    # Generate rooms
    for _ in range(room_count * 3):  # Try more times than needed
        if len(rooms) >= room_count:
            break

        # Random room dimensions
        w = random.randint(4, 10)
        h = random.randint(4, 10)
        x = random.randint(1, grid_w - w - 1)
        y = random.randint(1, grid_h - h - 1)

        new_room = (x, y, w, h)

        # Check for overlap with existing rooms
        if not any(rooms_overlap(new_room, room) for room in rooms):
            carve_room(grid, x, y, w, h)

            # Connect to previous room
            if rooms:
                connect_rooms(grid, rooms[-1], new_room)

            rooms.append(new_room)

    return rooms
# endregion

rooms = generate_dungeon(grid)
print(f"Generated {len(rooms)} rooms")
