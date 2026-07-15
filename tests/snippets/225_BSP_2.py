# mcrf: objects=[BSP,Caption,Scene,Traversal] verified=0.2.8-dev status=ok
# BSP traversal - iterate leaves and all nodes in various orders
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

bsp = mcrfpy.BSP(pos=(0, 0), size=(80, 50))
bsp.split_recursive(depth=4, min_size=(8, 8))

# len() returns number of leaf nodes
num_rooms = len(bsp)

# Iterate directly over leaves
for leaf in bsp:
    pass

# Or use leaves() explicitly
for leaf in bsp.leaves():
    pass

# Traverse all nodes (including internal)
lines = []
for node in bsp.traverse(mcrfpy.Traversal.PRE_ORDER):
    if node.is_leaf:
        lines.append(f"Leaf: {node.pos}")
    else:
        lines.append(f"Split at: {node.split_position}")

status = mcrfpy.Caption(text=f"BSP: {num_rooms} rooms, {len(lines)} nodes visited", pos=(10, 10))
scene.children.append(status)
