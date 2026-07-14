# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Color Components - RGBA color manipulation
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Show color components
colors = [
    (mcrfpy.Color(255, 0, 0), "Pure Red"),
    (mcrfpy.Color(0, 255, 0), "Pure Green"),
    (mcrfpy.Color(0, 0, 255), "Pure Blue"),
    (mcrfpy.Color(255, 255, 0), "Yellow (R+G)"),
    (mcrfpy.Color(255, 0, 255), "Magenta (R+B)"),
    (mcrfpy.Color(0, 255, 255), "Cyan (G+B)"),
    (mcrfpy.Color(128, 128, 128), "Gray"),
    (mcrfpy.Color(255, 255, 255, 128), "White 50% Alpha"),
]

for i, (color, name) in enumerate(colors):
    x = 100 + (i % 4) * 230
    y = 150 + (i // 4) * 280

    frame = mcrfpy.Frame(pos=(x, y), size=(180, 100), fill_color=color)
    scene.children.append(frame)

    label = mcrfpy.Caption(text=name, pos=(x, y + 110))
    scene.children.append(label)

    rgba = mcrfpy.Caption(
        text=f"R:{color.r} G:{color.g} B:{color.b} A:{color.a}",
        pos=(x, y + 140))
    rgba.fill_color = mcrfpy.Color(150, 150, 150)
    scene.children.append(rgba)

_caption = mcrfpy.Caption(text="Color RGBA Components", pos=(400, 60))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)
