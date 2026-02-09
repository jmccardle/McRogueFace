import mcrfpy

s = mcrfpy.Scene("test")
s.activate()

g = mcrfpy.Grid(pos=(0,0), size=(1024,768), grid_size = (64, 48))
s.children.append(g)

def keys(*args):
    print("key: ", args)

def clicks(*args):
    print("click:", args)

s.on_key = keys
g.on_click = clicks

