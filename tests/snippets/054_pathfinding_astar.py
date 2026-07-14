# mcrf: objects=[Caption,Color,ColorLayer,Grid,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Pathfinding A* - Find path between points
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

# Add color layer for path visualization
path_layer = mcrfpy.ColorLayer(z_index=1, name="path")
grid.add_layer(path_layer)

# Create maze
for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        # Border walls
        if x == 0 or x == 15 or y == 0 or y == 11:
            cell.tilesprite = 1
            cell.walkable = False
        # Some obstacles
        elif x == 8 and y > 1 and y < 10:
            cell.tilesprite = 1
            cell.walkable = False
        elif x == 4 and y > 3 and y < 11:
            cell.tilesprite = 1
            cell.walkable = False
        else:
            cell.tilesprite = 48
            cell.walkable = True

# Find path
start = (2, 6)
end = (13, 6)
path = grid.find_path(start, end)

# Highlight path using color layer
for px, py in path:
    path_layer.set((px, py), mcrfpy.Color(100, 255, 100, 180))

# Mark start/end
path_layer.set((start[0], start[1]), mcrfpy.Color(100, 100, 255, 200))
path_layer.set((end[0], end[1]), mcrfpy.Color(255, 100, 100, 200))

status = mcrfpy.Caption(text=f"A* Path length: {len(path)} - Blue=start, Red=end", pos=(320, 700))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
