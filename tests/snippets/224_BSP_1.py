# mcrf: objects=[BSP,Caption,Color,ColorLayer,Grid,Scene] verified=0.2.8-dev status=ok
# BSP Quick Reference - create a tree, split, and iterate leaves
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(
    grid_size=(80, 50),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(800, 500),
)
scene.children.append(grid)

# Create a BSP tree covering a dungeon area
bsp = mcrfpy.BSP(pos=(0, 0), size=(80, 50))

# Split recursively into rooms
bsp.split_recursive(depth=4, min_size=(8, 8))

# Iterate over leaf nodes (rooms)
room_layer = mcrfpy.ColorLayer(z_index=1, name="rooms")
grid.add_layer(room_layer)

for leaf in bsp:
    x, y = leaf.pos
    w, h = leaf.size
    room_layer.set((x, y), mcrfpy.Color(200, 150, 100, 150))

# Use adjacency graph for corridor placement
for i, neighbors in enumerate(bsp.adjacency):
    leaf = bsp.get_leaf(i)
    for neighbor_idx in neighbors:
        # leaf and bsp.get_leaf(neighbor_idx) share a wall
        tiles = leaf.adjacent_tiles[neighbor_idx]
        # tiles contains Vector coordinates for corridor placement
        for tile in tiles:
            pass  # e.g. carve a corridor tile at (tile.x, tile.y)

status = mcrfpy.Caption(text=f"BSP: {len(bsp)} rooms", pos=(10, 10))
scene.children.append(status)
