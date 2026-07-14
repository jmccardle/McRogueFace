# mcrf: objects=[BSP,Caption,Color,ColorLayer,Grid,Scene] verified=0.2.8-dev status=ok
# BSP Basic - Binary space partition for dungeon generation
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

# Add color layer for room visualization
room_layer = mcrfpy.ColorLayer(z_index=1, name="rooms")
grid.add_layer(room_layer)

# Fill with walls
for y in range(12):
    for x in range(16):
        grid.at(x, y).tilesprite = 1
        grid.at(x, y).walkable = False

# Create BSP tree (pos and size as tuples)
bsp = mcrfpy.BSP(pos=(0, 0), size=(16, 12))
bsp.split_recursive(depth=3, min_size=(3, 3))

# Room colors
colors = [
    mcrfpy.Color(255, 150, 150, 150),
    mcrfpy.Color(150, 255, 150, 150),
    mcrfpy.Color(150, 150, 255, 150),
    mcrfpy.Color(255, 255, 150, 150),
    mcrfpy.Color(255, 150, 255, 150),
    mcrfpy.Color(150, 255, 255, 150),
]

# Carve rooms from leaves
for i, leaf in enumerate(bsp):
    x, y = leaf.pos
    w, h = leaf.size
    # Shrink room slightly
    for ry in range(y + 1, y + h - 1):
        for rx in range(x + 1, x + w - 1):
            if 0 <= rx < 16 and 0 <= ry < 12:
                grid.at(rx, ry).tilesprite = 48
                grid.at(rx, ry).walkable = True
                room_layer.set((rx, ry), colors[i % len(colors)])

status = mcrfpy.Caption(text="BSP dungeon - each color is a leaf node", pos=(320, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
