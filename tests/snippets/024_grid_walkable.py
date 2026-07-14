# mcrf: objects=[Caption,Color,Grid,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Grid Walkable - Walkable vs blocked tiles
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(1024, 768),
    zoom=4.0
)
scene.children.append(grid)

# Create maze-like pattern
for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        # Outer walls
        if x == 0 or x == 15 or y == 0 or y == 11:
            cell.tilesprite = 1  # Wall
            cell.walkable = False
        # Inner obstacles
        elif (x + y) % 4 == 0 and x > 2 and x < 13:
            cell.tilesprite = 1
            cell.walkable = False
        else:
            cell.tilesprite = 48  # Floor
            cell.walkable = True

# Legend
legend = mcrfpy.Caption(text="Walls are not walkable, floors are", pos=(350, 720))
legend.outline = 2
legend.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(legend)
