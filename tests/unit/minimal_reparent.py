import mcrfpy
scene = mcrfpy.Scene("test")
scene.activate()
f1 = mcrfpy.Frame((10,10), (100,100), fill_color = (255, 0, 0, 64))
f2 = mcrfpy.Frame((200,10), (100,100), fill_color = (0, 255, 0, 64))
f_child = mcrfpy.Frame((25,25), (50,50), fill_color = (0, 0, 255, 64))

scene.children.append(f1)
scene.children.append(f2)
f1.children.append(f_child)
f_child.parent = f2

print(f1.children)
print(f2.children)
