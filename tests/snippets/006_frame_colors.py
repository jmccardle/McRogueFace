# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev status=ok
# Frame Colors - Fill and outline colors
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Dark background
scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

colors = [
    (mcrfpy.Color(255, 100, 100), "Red"),
    (mcrfpy.Color(100, 255, 100), "Green"),
    (mcrfpy.Color(100, 100, 255), "Blue"),
    (mcrfpy.Color(255, 255, 100), "Yellow"),
]

for i, (color, name) in enumerate(colors):
    x = 112 + (i % 2) * 420
    y = 134 + (i // 2) * 280

    frame = mcrfpy.Frame(
        pos=(x, y), size=(380, 240),
        fill_color=color,
        outline_color=mcrfpy.Color(255, 255, 255),
        outline=3.0
    )
    scene.children.append(frame)

    label = mcrfpy.Caption(text=name, pos=(x + 150, y + 100))
    label.outline = 2
    label.outline_color = mcrfpy.Color(0, 0, 0)
    scene.children.append(label)
