import mcrfpy
import sys

scene = mcrfpy.Scene("test")
scene.activate()
f1 = mcrfpy.Frame((10,10), (100,100), fill_color = (255, 0, 0, 64))
f2 = mcrfpy.Frame((200,10), (100,100), fill_color = (0, 255, 0, 64))
f_child = mcrfpy.Frame((25,25), (50,50), fill_color = (0, 0, 255, 64))

scene.children.append(f1)
scene.children.append(f2)
f1.children.append(f_child)

failures = []

# Before reparent: child belongs to f1
if len(f1.children) != 1:
    failures.append("f1 should have 1 child before reparent, has %d" % len(f1.children))
if len(f2.children) != 0:
    failures.append("f2 should have 0 children before reparent, has %d" % len(f2.children))
if f_child.parent is not f1:
    failures.append("f_child.parent should be f1 before reparent, got %r" % (f_child.parent,))

# Reparent by assigning .parent
f_child.parent = f2

print(f1.children)
print(f2.children)

# After reparent: child moved out of f1 and into f2 (no duplication, no orphaning)
if len(f1.children) != 0:
    failures.append("f1 should have 0 children after reparent, has %d" % len(f1.children))
if len(f2.children) != 1:
    failures.append("f2 should have 1 child after reparent, has %d" % len(f2.children))
elif f2.children[0] is not f_child:
    failures.append("f2's child is not f_child")
if f_child.parent is not f2:
    failures.append("f_child.parent should be f2 after reparent, got %r" % (f_child.parent,))

if failures:
    for f in failures:
        print("FAIL: " + f)
    sys.exit(1)

print("PASS")
sys.exit(0)
