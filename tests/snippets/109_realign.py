# mcrf: objects=[Alignment,Caption,Color,Frame,InputState,Key,Scene] verified=0.2.8-dev status=ok
# Realign - Reapply alignment after changes
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Container
container = mcrfpy.Frame(
    pos=(212, 184), size=(600, 400),
    fill_color=mcrfpy.Color(50, 50, 70),
    outline=2.0
)
scene.children.append(container)

# Centered child
child = mcrfpy.Frame(
    size=(200, 100),
    fill_color=mcrfpy.Color(150, 100, 100),
    align=mcrfpy.Alignment.CENTER
)
container.children.append(child)

child.children.append(mcrfpy.Caption(text="Centered", pos=(60, 35)))

status = mcrfpy.Caption(text="Press SPACE to resize container", pos=(320, 620))
scene.children.append(status)

small = True

def on_key(key, action):
    global small
    if key == mcrfpy.Key.SPACE and action == mcrfpy.InputState.PRESSED:
        if small:
            container.w = 800
            container.h = 500
            status.text = "Container resized! Child realigns automatically"
        else:
            container.w = 600
            container.h = 400
            status.text = "Container shrunk! Alignment maintained"
        small = not small
        # realign() is called automatically when parent resizes
        # but you can call it manually: child.realign()

scene.on_key = on_key
