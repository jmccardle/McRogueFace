# mcrf: objects=[Entity,Grid,InputState,Key,Scene] verified=0.2.8-dev status=ok
import mcrfpy
import random

# Setup scene
scene = mcrfpy.Scene("game")
scene.activate()

# Create grid
grid = mcrfpy.Grid(
    grid_size=(50, 50),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(800, 600)
)
scene.children.append(grid)

# Initialize map (all walls)
for y in range(50):
    for x in range(50):
        point = grid.at(x, y)
        point.tilesprite = 1  # Wall
        point.walkable = False
        point.transparent = False

# Carve rooms
rooms = [
    (5, 5, 10, 8),
    (25, 5, 12, 10),
    (8, 25, 15, 12),
    (35, 30, 10, 15)
]

for rx, ry, rw, rh in rooms:
    for y in range(ry, ry + rh):
        for x in range(rx, rx + rw):
            point = grid.at(x, y)
            point.tilesprite = 0  # Floor
            point.walkable = True
            point.transparent = True

# Connect rooms with corridors
for i in range(len(rooms) - 1):
    x1 = rooms[i][0] + rooms[i][2] // 2
    y1 = rooms[i][1] + rooms[i][3] // 2
    x2 = rooms[i+1][0] + rooms[i+1][2] // 2
    y2 = rooms[i+1][1] + rooms[i+1][3] // 2

    # Horizontal then vertical
    for x in range(min(x1, x2), max(x1, x2) + 1):
        point = grid.at(x, y1)
        point.tilesprite = 0
        point.walkable = True
        point.transparent = True

    for y in range(min(y1, y2), max(y1, y2) + 1):
        point = grid.at(x2, y)
        point.tilesprite = 0
        point.walkable = True
        point.transparent = True

# Create player in first room
player = mcrfpy.Entity(
    grid_pos=(10, 9),
    texture=mcrfpy.default_texture,
    sprite_index=64
)
grid.entities.append(player)

# Center camera on player
grid.center = player.pos

# Movement handler -- on_key receives (Key, InputState) enums, not strings
def on_key(key, action):
    if action != mcrfpy.InputState.PRESSED:
        return

    dx, dy = 0, 0
    if key in (mcrfpy.Key.UP, mcrfpy.Key.W): dy = -1
    elif key in (mcrfpy.Key.DOWN, mcrfpy.Key.S): dy = 1
    elif key in (mcrfpy.Key.LEFT, mcrfpy.Key.A): dx = -1
    elif key in (mcrfpy.Key.RIGHT, mcrfpy.Key.D): dx = 1
    else:
        return

    new_x = player.grid_x + dx
    new_y = player.grid_y + dy

    # Check collision
    if grid.at(new_x, new_y).walkable:
        player.grid_pos = (new_x, new_y)
        grid.center = player.pos  # entity pixel position, matches grid.center's units

scene.on_key = on_key
