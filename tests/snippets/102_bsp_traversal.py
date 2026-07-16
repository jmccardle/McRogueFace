# mcrf: objects=[BSP,Caption,Color,ColorLayer,Frame,Grid,Scene,Traversal] verified=0.2.8-dev status=ok
# BSP Traversal - Different traversal orders
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Create BSP tree
bsp = mcrfpy.BSP(pos=(0, 0), size=(16, 12))
bsp.split_recursive(depth=3, min_size=(3, 3), seed=42)

# Visualize in a grid
grid = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(1024, 768),
    zoom=4.0
)
scene.children.append(grid)

# Add color layer for visualization
color_layer = mcrfpy.ColorLayer(z_index=1, name="rooms")
grid.add_layer(color_layer)

for y in range(12):
    for x in range(16):
        grid.at(x, y).tilesprite = 48

# Color leaves by traversal order
colors = [
    mcrfpy.Color(255, 100, 100, 150),
    mcrfpy.Color(255, 200, 100, 150),
    mcrfpy.Color(200, 255, 100, 150),
    mcrfpy.Color(100, 255, 100, 150),
    mcrfpy.Color(100, 255, 200, 150),
    mcrfpy.Color(100, 200, 255, 150),
    mcrfpy.Color(100, 100, 255, 150),
    mcrfpy.Color(200, 100, 255, 150),
]

traversal = mcrfpy.Traversal.IN_ORDER
leaves = list(bsp.traverse(traversal))

leaf_count = 0
for i, node in enumerate(leaves):
    if node.is_leaf:
        x, y = node.pos
        w, h = node.size
        color = colors[leaf_count % len(colors)]
        for ny in range(y, y + h):
            for nx in range(x, x + w):
                if 0 <= nx < 16 and 0 <= ny < 12:
                    color_layer.set((nx, ny), color)
        leaf_count += 1

status = mcrfpy.Caption(
    text=f"BSP IN_ORDER traversal - {len(leaves)} nodes, {leaf_count} leaves",
    pos=(280, 720)
)
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
