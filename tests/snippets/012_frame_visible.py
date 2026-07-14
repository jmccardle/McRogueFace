# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Frame Visibility - Show and hide elements
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Create three frames
visible_frame = mcrfpy.Frame(
    pos=(100, 234), size=(250, 300),
    fill_color=mcrfpy.Color(100, 200, 100),
    visible=True
)
scene.children.append(visible_frame)
scene.children.append(mcrfpy.Caption(text="visible=True", pos=(140, 550)))

hidden_frame = mcrfpy.Frame(
    pos=(387, 234), size=(250, 300),
    fill_color=mcrfpy.Color(200, 100, 100),
    visible=False  # This won't be displayed
)
scene.children.append(hidden_frame)
scene.children.append(mcrfpy.Caption(text="visible=False", pos=(427, 550)))
scene.children.append(mcrfpy.Caption(text="(frame exists but hidden)", pos=(397, 580)))

visible_frame2 = mcrfpy.Frame(
    pos=(674, 234), size=(250, 300),
    fill_color=mcrfpy.Color(100, 100, 200),
    visible=True
)
scene.children.append(visible_frame2)
scene.children.append(mcrfpy.Caption(text="visible=True", pos=(714, 550)))
