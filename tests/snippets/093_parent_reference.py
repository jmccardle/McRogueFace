# mcrf: objects=[Caption,Color,Frame,InputState,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Parent Reference - Access parent from child
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Parent container
parent = mcrfpy.Frame(
    pos=(262, 184), size=(500, 400),
    fill_color=mcrfpy.Color(80, 80, 120),
    name="parent_frame"
)
scene.children.append(parent)

# Child button
child = mcrfpy.Frame(
    pos=(150, 150), size=(200, 100),
    fill_color=mcrfpy.Color(100, 150, 100),
    name="child_button"
)
parent.children.append(child)

child.children.append(mcrfpy.Caption(text="Click me!", pos=(50, 35)))

status = mcrfpy.Caption(text="Click the button", pos=(350, 620))
scene.children.append(status)

def on_click(pos, button, action):
    if action == mcrfpy.InputState.PRESSED:
        # Access parent from child
        p = child.parent
        if p:
            status.text = f"My parent is: '{p.name}'"
            # Modify parent
            p.fill_color = mcrfpy.Color(120, 80, 80)

child.on_click = on_click
