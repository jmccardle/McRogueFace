# mcrf: objects=[Alignment,Color,Frame,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Frame Alignment - Automatic positioning
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Container to show alignment
container = mcrfpy.Frame(
    pos=(112, 84), size=(800, 600),
    fill_color=mcrfpy.Color(40, 40, 60),
    outline=2.0
)
scene.children.append(container)

# Grid of alignment options (excluding CENTER to avoid margin error)
alignments = [
    (mcrfpy.Alignment.TOP_LEFT, "TOP_LEFT"),
    (mcrfpy.Alignment.TOP_CENTER, "TOP_CENTER"),
    (mcrfpy.Alignment.TOP_RIGHT, "TOP_RIGHT"),
    (mcrfpy.Alignment.CENTER_LEFT, "CENTER_LEFT"),
    (mcrfpy.Alignment.CENTER_RIGHT, "CENTER_RIGHT"),
    (mcrfpy.Alignment.BOTTOM_LEFT, "BOTTOM_LEFT"),
    (mcrfpy.Alignment.BOTTOM_CENTER, "BOTTOM_CENTER"),
    (mcrfpy.Alignment.BOTTOM_RIGHT, "BOTTOM_RIGHT"),
]

for alignment, name in alignments:
    box = mcrfpy.Frame(
        size=(80, 60),
        fill_color=mcrfpy.Color(150, 100, 200),
        align=alignment,
        margin=10
    )
    container.children.append(box)

# Center box (no margin for CENTER)
center_box = mcrfpy.Frame(
    size=(80, 60),
    fill_color=mcrfpy.Color(100, 200, 150),
    align=mcrfpy.Alignment.CENTER
)
container.children.append(center_box)
