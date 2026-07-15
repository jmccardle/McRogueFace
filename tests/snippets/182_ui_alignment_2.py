# mcrf: objects=[Alignment,Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("ui_alignment_margins")
mcrfpy.current_scene = scene

parent = mcrfpy.Frame(pos=(100, 100), size=(400, 300))
scene.children.append(parent)

# Health bar in top-left corner with 10px padding
health_bar = mcrfpy.Frame(pos=(0, 0), size=(200, 30))
health_bar.align = mcrfpy.Alignment.TOP_LEFT
health_bar.margin = 10.0  # 10px from top and left edges

parent.children.append(health_bar)
# health_bar is now at (10, 10)

# Element with different horizontal/vertical margins
element = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
element.align = mcrfpy.Alignment.BOTTOM_RIGHT
element.horiz_margin = 20.0  # 20px from right edge
element.vert_margin = 10.0   # 10px from bottom edge

parent.children.append(element)
