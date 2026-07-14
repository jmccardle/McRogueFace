# mcrf: objects=[Caption,Grid,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Procgen Cellular - Cave generation
import mcrfpy
import random

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(
    grid_size=(40, 30),
    texture=mcrfpy.default_texture,
    pos=(112, 84),
    size=(800, 600)
)
scene.children.append(grid)

# Initialize with random walls
for y in range(30):
    for x in range(40):
        cell = grid.at(x, y)
        if x == 0 or x == 39 or y == 0 or y == 29:
            cell.tilesprite = 1
        elif random.random() < 0.45:
            cell.tilesprite = 1
        else:
            cell.tilesprite = 48

# Cellular automata iterations
def count_neighbors(x, y):
    count = 0
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < 40 and 0 <= ny < 30:
                if grid.at(nx, ny).tilesprite == 1:
                    count += 1
            else:
                count += 1
    return count

def iterate():
    changes = []
    for y in range(1, 29):
        for x in range(1, 39):
            neighbors = count_neighbors(x, y)
            if neighbors > 4:
                changes.append((x, y, 1))
            elif neighbors < 4:
                changes.append((x, y, 48))
    for x, y, tile in changes:
        grid.at(x, y).tilesprite = tile

# Run 4 iterations
for _ in range(4):
    iterate()

scene.children.append(mcrfpy.Caption(text="Cellular automata cave generation", pos=(340, 700)))
