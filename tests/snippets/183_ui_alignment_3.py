# mcrf: objects=[Alignment,Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("ui_alignment_reactive")
mcrfpy.current_scene = scene

parent = mcrfpy.Frame(pos=(0, 0), size=(200, 200))
scene.children.append(parent)

child = mcrfpy.Frame(pos=(0, 0), size=(50, 50))
child.align = mcrfpy.Alignment.CENTER
parent.children.append(child)

print(f"Initial: ({child.x}, {child.y})")  # (75, 75)

# Resize parent
parent.w = 400
parent.h = 400

print(f"After resize: ({child.x}, {child.y})")  # (175, 175)
