# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Frame Rotation - Rotate UI elements
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Dark background
scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

rotations = [0, 15, 30, 45, 60]
for i, angle in enumerate(rotations):
    frame = mcrfpy.Frame(
        pos=(100 + i * 180, 300), size=(120, 120),
        fill_color=mcrfpy.Color(150, 100, 200),
        outline=3.0,
        outline_color=mcrfpy.Color(255, 255, 255)
    )
    frame.rotation = angle
    scene.children.append(frame)

    label = mcrfpy.Caption(text=f"{angle}deg", pos=(130 + i * 180, 500))
    label.outline = 2
    label.outline_color = mcrfpy.Color(0, 0, 0)
    scene.children.append(label)

title = mcrfpy.Caption(text="Frame Rotation", pos=(420, 100))
title.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(title)
