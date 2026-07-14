# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Frame Clipping - clip_children property
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Frame WITHOUT clipping
no_clip = mcrfpy.Frame(
    pos=(100, 200), size=(300, 300),
    fill_color=mcrfpy.Color(60, 60, 100),
    outline=2.0, outline_color=mcrfpy.Color(150, 150, 200),
    clip_children=False
)
scene.children.append(no_clip)

overflow1 = mcrfpy.Frame(
    pos=(150, 150), size=(200, 200),
    fill_color=mcrfpy.Color(255, 100, 100)
)
no_clip.children.append(overflow1)

label1 = mcrfpy.Caption(text="clip_children=False", pos=(120, 520))
scene.children.append(label1)

# Frame WITH clipping
with_clip = mcrfpy.Frame(
    pos=(524, 200), size=(300, 300),
    fill_color=mcrfpy.Color(60, 60, 100),
    outline=2.0, outline_color=mcrfpy.Color(150, 150, 200),
    clip_children=True
)
scene.children.append(with_clip)

overflow2 = mcrfpy.Frame(
    pos=(150, 150), size=(200, 200),
    fill_color=mcrfpy.Color(100, 255, 100)
)
with_clip.children.append(overflow2)

label2 = mcrfpy.Caption(text="clip_children=True", pos=(544, 520))
scene.children.append(label2)
