# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev status=ok
# Frame Children - Nested UI elements
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Parent container
parent = mcrfpy.Frame(
    pos=(162, 134), size=(700, 500),
    fill_color=mcrfpy.Color(40, 40, 60),
    outline=3.0,
    outline_color=mcrfpy.Color(100, 100, 150)
)
scene.children.append(parent)

# Child frames - positions relative to parent
child1 = mcrfpy.Frame(
    pos=(20, 20), size=(200, 200),
    fill_color=mcrfpy.Color(200, 80, 80)
)
parent.children.append(child1)

child2 = mcrfpy.Frame(
    pos=(240, 20), size=(200, 200),
    fill_color=mcrfpy.Color(80, 200, 80)
)
parent.children.append(child2)

child3 = mcrfpy.Frame(
    pos=(460, 20), size=(200, 200),
    fill_color=mcrfpy.Color(80, 80, 200)
)
parent.children.append(child3)

# Label
label = mcrfpy.Caption(
    text="Children use parent-relative coordinates",
    pos=(150, 450)
)
parent.children.append(label)
