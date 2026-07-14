# mcrf: objects=[Caption,Color,Frame,InputState,Key,Scene,Vector] verified=0.2.8-dev@a7ba486 status=ok
# Scene Position - Offset all scene content
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Add some content
for i in range(5):
    frame = mcrfpy.Frame(
        pos=(150 + i * 150, 300), size=(100, 100),
        fill_color=mcrfpy.Color(100 + i * 30, 100, 200 - i * 30)
    )
    scene.children.append(frame)

scene.children.append(mcrfpy.Caption(
    text="Press WASD to move scene.pos",
    pos=(350, 550)
))

pos_label = mcrfpy.Caption(text="scene.pos = (0, 0)", pos=(380, 600))
scene.children.append(pos_label)

def on_key(key, action):
    if action != mcrfpy.InputState.PRESSED:
        return
    x, y = scene.pos.x, scene.pos.y
    step = 20
    if key == mcrfpy.Key.W: y -= step
    elif key == mcrfpy.Key.S: y += step
    elif key == mcrfpy.Key.A: x -= step
    elif key == mcrfpy.Key.D: x += step
    elif key == mcrfpy.Key.R: x, y = 0, 0  # Reset

    scene.pos = mcrfpy.Vector(x, y)
    pos_label.text = f"scene.pos = ({x}, {y})"

scene.on_key = on_key
