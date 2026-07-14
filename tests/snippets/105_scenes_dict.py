# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev status=ok
# Scenes Tuple - Access all scenes
import mcrfpy

# Create several scenes
for name in ["menu", "game", "options", "credits"]:
    s = mcrfpy.Scene(name)
    s.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))
    s.children.append(mcrfpy.Caption(text=f"{name.upper()} SCENE", pos=(420, 350)))

scene = mcrfpy.Scene("main")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

_caption = mcrfpy.Caption(
    text="All Registered Scenes",
    pos=(380, 100))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

# List all scenes (scenes is a tuple)
y = 200
for s in mcrfpy.scenes:
    cap = mcrfpy.Caption(
        text=f"• {s.name}",
        pos=(300, y)
    )
    scene.children.append(cap)
    y += 50

scene.children.append(mcrfpy.Caption(
    text=f"Total scenes: {len(mcrfpy.scenes)}",
    pos=(380, 550)
))
