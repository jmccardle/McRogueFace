# mcrf: objects=[Caption,Color,Frame,Scene,Vector] verified=0.2.8-dev@a7ba486 status=ok
# Frame Origin - Rotation pivot point
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Dark background
scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# All frames rotated 45 degrees, different origins
origins = [
    ((0, 0), "top-left"),
    ((60, 60), "center"),
    ((120, 0), "top-right"),
    ((0, 120), "bottom-left"),
]

for i, (origin, name) in enumerate(origins):
    x = 150 + (i % 2) * 400
    y = 180 + (i // 2) * 280

    # Reference frame (no rotation)
    ref = mcrfpy.Frame(
        pos=(x, y), size=(120, 120),
        fill_color=mcrfpy.Color(50, 50, 50),
        outline=1.0,
        outline_color=mcrfpy.Color(100, 100, 100)
    )
    scene.children.append(ref)

    # Rotated frame
    frame = mcrfpy.Frame(
        pos=(x, y), size=(120, 120),
        fill_color=mcrfpy.Color(200, 100, 150),
        opacity=0.8
    )
    frame.rotation = 45
    frame.origin = mcrfpy.Vector(origin[0], origin[1])
    scene.children.append(frame)

    label = mcrfpy.Caption(text=f"origin: {name}", pos=(x, y + 160))
    label.outline = 2
    label.outline_color = mcrfpy.Color(0, 0, 0)
    scene.children.append(label)
