# mcrf: objects=[Alignment,Caption,Color,Frame,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Alignment Margins - Spacing from edges
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

container = mcrfpy.Frame(
    pos=(112, 84), size=(800, 600),
    fill_color=mcrfpy.Color(40, 40, 60),
    outline=2.0
)
scene.children.append(container)

# Different margin examples
corners = [
    (mcrfpy.Alignment.TOP_LEFT, 0, "margin=0"),
    (mcrfpy.Alignment.TOP_RIGHT, 20, "margin=20"),
    (mcrfpy.Alignment.BOTTOM_LEFT, 40, "margin=40"),
    (mcrfpy.Alignment.BOTTOM_RIGHT, 60, "margin=60"),
]

for align, margin, label in corners:
    box = mcrfpy.Frame(
        size=(120, 80),
        fill_color=mcrfpy.Color(150, 100, 100),
        align=align,
        margin=margin
    )
    container.children.append(box)
    box.children.append(mcrfpy.Caption(text=label, pos=(15, 30)))

# Center with margins
center = mcrfpy.Frame(
    size=(200, 100),
    fill_color=mcrfpy.Color(100, 150, 100),
    align=mcrfpy.Alignment.CENTER,
    margin=0
)
container.children.append(center)
center.children.append(mcrfpy.Caption(text="CENTER, no margin", pos=(20, 35)))

scene.children.append(mcrfpy.Caption(text="Margin affects distance from edges when aligned", pos=(280, 700)))
