# mcrf: objects=[Caption,Color,Scene] verified=0.2.8-dev status=ok
# Caption Styling - Text colors and fonts
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Title
title = mcrfpy.Caption(text="Caption Styles", pos=(350, 80))
title.fill_color = mcrfpy.Color(255, 255, 255)
scene.children.append(title)

# Different colors
colors = [
    (mcrfpy.Color(255, 100, 100), "Red Text"),
    (mcrfpy.Color(100, 255, 100), "Green Text"),
    (mcrfpy.Color(100, 100, 255), "Blue Text"),
    (mcrfpy.Color(255, 255, 100), "Yellow Text"),
    (mcrfpy.Color(255, 100, 255), "Magenta Text"),
    (mcrfpy.Color(100, 255, 255), "Cyan Text"),
]

for i, (color, text) in enumerate(colors):
    cap = mcrfpy.Caption(text=text, pos=(350, 180 + i * 80))
    cap.fill_color = color
    scene.children.append(cap)
