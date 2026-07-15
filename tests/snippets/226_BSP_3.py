# mcrf: objects=[BSP,Caption,Scene] verified=0.2.8-dev status=ok
# BSP adjacency - connect rooms with corridors via the wall-tile map
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

bsp = mcrfpy.BSP(pos=(0, 0), size=(80, 50))
bsp.split_recursive(depth=4, min_size=(8, 8))

# Get all neighbor relationships
lines = []
for i, neighbors in enumerate(bsp.adjacency):
    lines.append(f"Leaf {i} is adjacent to: {neighbors}")

# Get wall tiles between adjacent leaves
leaf = bsp.get_leaf(0)
wall_count = 0
for neighbor_idx in leaf.adjacent_tiles.keys():
    tiles = leaf.adjacent_tiles[neighbor_idx]
    # tiles is a tuple of Vector objects representing
    # coordinates on THIS leaf's edge that border the neighbor
    for tile in tiles:
        wall_count += 1

status = mcrfpy.Caption(text=f"BSP: {len(lines)} leaves, {wall_count} shared wall tiles", pos=(10, 10))
scene.children.append(status)
