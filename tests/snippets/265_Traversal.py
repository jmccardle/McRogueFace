# mcrf: objects=[BSP,Caption,Scene,Traversal] verified=0.2.8-dev status=ok
# Traversal - BSP traversal order enumeration, including string shortcuts
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

bsp = mcrfpy.BSP(pos=(0, 0), size=(32, 24))
bsp.split_recursive(depth=3, min_size=(4, 4))

# Iterate BSP nodes in different orders
pre_order_positions = []
for node in bsp.traverse(mcrfpy.Traversal.PRE_ORDER):
    pre_order_positions.append(node.pos)

# Level order (default) - breadth-first
level_order_count = 0
for node in bsp.traverse(mcrfpy.Traversal.LEVEL_ORDER):
    level_order_count += 1

# String shortcuts also work
post_order_count = 0
for node in bsp.traverse('post'):
    post_order_count += 1

# Using traverse with POST_ORDER ensures we see leaves before parents
leaves = []
for node in bsp.traverse(mcrfpy.Traversal.POST_ORDER):
    if node.is_leaf:
        leaves.append(node)

# Or simply iterate the BSP directly (uses leaf order)
leaves_direct = list(bsp)

# Process rooms from smallest (deepest) to largest, connecting child regions
corridor_count = 0
for node in bsp.traverse(mcrfpy.Traversal.INVERTED_LEVEL_ORDER):
    if not node.is_leaf:
        left_center = node.left.center()
        right_center = node.right.center()
        corridor_count += 1

status = mcrfpy.Caption(
    text=(f"Traversal: {level_order_count} nodes, {len(leaves)} leaves, "
          f"{corridor_count} corridors"),
    pos=(10, 10)
)
scene.children.append(status)
