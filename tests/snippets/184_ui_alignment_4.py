# mcrf: objects=[Alignment,Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("ui_alignment_freeze")
mcrfpy.current_scene = scene

parent = mcrfpy.Frame(pos=(0, 0), size=(200, 200))
scene.children.append(parent)

child = mcrfpy.Frame(pos=(0, 0), size=(50, 50))

# Center the element first
child.align = mcrfpy.Alignment.CENTER
parent.children.append(child)  # Positions at center

# Freeze position
child.align = None

# Now parent resizing won't move the child
parent.w = 800  # child stays at its current position
