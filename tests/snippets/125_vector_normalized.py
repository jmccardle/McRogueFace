# mcrf: objects=[Caption,Color,Frame,Scene,Vector] verified=0.2.8-dev status=ok
# Vector Normalized - Unit vectors
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

_caption = mcrfpy.Caption(
    text="Vector Normalization",
    pos=(400, 80))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

# Test vectors
vectors = [
    mcrfpy.Vector(100, 0),
    mcrfpy.Vector(0, 50),
    mcrfpy.Vector(30, 40),
    mcrfpy.Vector(-100, 100),
]

y = 180
for v in vectors:
    normalized = v.normalize()

    info = f"Vector({v.x:.0f}, {v.y:.0f})"
    scene.children.append(mcrfpy.Caption(text=info, pos=(150, y)))

    scene.children.append(mcrfpy.Caption(
        text=f"magnitude = {v.magnitude():.2f}",
        pos=(400, y)
    ))

    scene.children.append(mcrfpy.Caption(
        text=f"normalized = ({normalized.x:.2f}, {normalized.y:.2f})",
        pos=(600, y)
    ))

    y += 80

status = mcrfpy.Caption(text="Normalized vectors have magnitude = 1.0", pos=(350, 600))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
