# mcrf: objects=[Caption,Color,ColorLayer,Entity,Grid,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Entity Pathfinding - Entity path_to method
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

# Floor with some walls
for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        if x == 8 and y > 1 and y < 10:
            cell.tilesprite = 1
            cell.walkable = False
        else:
            cell.tilesprite = 48
            cell.walkable = True

# Entity
player = mcrfpy.Entity(
    grid_pos=(3, 6),
    texture=mcrfpy.default_texture,
    sprite_index=84
)
grid.entities.append(player)

# Find path to target
target = (13, 6)
path = player.path_to(target)

# Visualize path using color layer
for px, py in path:
    path_layer.set((px, py), mcrfpy.Color(150, 200, 255, 180))

# Mark target
path_layer.set((target[0], target[1]), mcrfpy.Color(255, 200, 100, 200))

status = mcrfpy.Caption(text="Entity pathfinding around wall", pos=(360, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
