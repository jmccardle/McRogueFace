# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Frame Z-Index - Control rendering order
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Dark background
scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Create overlapping frames with different z_index
# Lower z_index = rendered first (behind)
back = mcrfpy.Frame(
    pos=(262, 184), size=(300, 300),
    fill_color=mcrfpy.Color(255, 100, 100),
    z_index=0
)
scene.children.append(back)

middle = mcrfpy.Frame(
    pos=(362, 234), size=(300, 300),
    fill_color=mcrfpy.Color(100, 255, 100),
    z_index=1
)
scene.children.append(middle)

front = mcrfpy.Frame(
    pos=(462, 284), size=(300, 300),
    fill_color=mcrfpy.Color(100, 100, 255),
    z_index=2
)
scene.children.append(front)

# Labels with outlines for visibility
label1 = mcrfpy.Caption(text="z_index=0 (back)", pos=(262, 500))
label1.outline = 2
label1.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(label1)

label2 = mcrfpy.Caption(text="z_index=1 (middle)", pos=(362, 550))
label2.outline = 2
label2.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(label2)

label3 = mcrfpy.Caption(text="z_index=2 (front)", pos=(462, 600))
label3.outline = 2
label3.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(label3)
