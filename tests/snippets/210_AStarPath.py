# mcrf: objects=[Caption,Entity,Grid,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("astar_demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(10, 10))
scene.children.append(grid)

for y in range(10):
    for x in range(10):
        grid.at(x, y).walkable = True

player = mcrfpy.Entity((0, 0), grid=grid)
target_x, target_y = 3, 3

# Create path from grid
path = grid.find_path(player.cell_pos, (target_x, target_y))

if path:
    # Check path length
    print(f"Path has {path.remaining} steps")

    # Peek at next step without consuming
    next_pos = path.peek()

    # Walk the path step by step
    while path:
        next_step = path.walk()
        x, y = next_step
        player.cell_pos = (x, y)

status = mcrfpy.Caption(text=f"Player at {player.cell_pos}", pos=(10, 10))
scene.children.append(status)
