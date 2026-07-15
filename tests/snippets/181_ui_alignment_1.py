# mcrf: objects=[Alignment,Color,Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("ui_alignment_quickstart")
mcrfpy.current_scene = scene

# Create parent container
parent = mcrfpy.Frame(pos=(100, 100), size=(400, 300))
scene.children.append(parent)

# Create centered child
child = mcrfpy.Frame(pos=(0, 0), size=(100, 50))
child.fill_color = mcrfpy.Color(200, 50, 50)
child.align = mcrfpy.Alignment.CENTER

# Add to parent - alignment triggers automatically
parent.children.append(child)
# child is now at (150, 125) - centered in the 400x300 parent
