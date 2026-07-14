# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Frame Outline - Border thickness
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

outlines = [0, 2, 5, 10, 20]
for i, thickness in enumerate(outlines):
    frame = mcrfpy.Frame(
        pos=(92 + i * 180, 234), size=(160, 300),
        fill_color=mcrfpy.Color(60, 80, 120),
        outline_color=mcrfpy.Color(255, 200, 100),
        outline=thickness
    )
    scene.children.append(frame)

    label = mcrfpy.Caption(
        text=f"outline={thickness}",
        pos=(92 + i * 180 + 30, 550)
    )
    scene.children.append(label)
