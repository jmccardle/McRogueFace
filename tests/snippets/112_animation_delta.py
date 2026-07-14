# mcrf: objects=[Caption,Color,Easing,Frame,InputState,Key,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Animation Delta - Relative animation
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

_caption = mcrfpy.Caption(
    text="Delta Animation (Relative Values)",
    pos=(340, 80))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

# Frame for absolute animation
abs_frame = mcrfpy.Frame(
    pos=(200, 300), size=(100, 100),
    fill_color=mcrfpy.Color(255, 100, 100)
)
scene.children.append(abs_frame)
scene.children.append(mcrfpy.Caption(text="Absolute: x -> 500", pos=(200, 420)))

# Frame for delta animation
delta_frame = mcrfpy.Frame(
    pos=(200, 500), size=(100, 100),
    fill_color=mcrfpy.Color(100, 100, 255)
)
scene.children.append(delta_frame)
scene.children.append(mcrfpy.Caption(text="Delta: x += 300", pos=(200, 620)))

scene.children.append(mcrfpy.Caption(text="Press SPACE to animate", pos=(400, 700)))

def on_key(key, action):
    if key == mcrfpy.Key.SPACE and action == mcrfpy.InputState.PRESSED:
        # Absolute: animate TO position 500
        abs_frame.animate("x", 500, 1.0, mcrfpy.Easing.EASE_OUT)

        # Delta: animate BY 300 (relative to current position)
        # Note: delta animations add to current value
        anim = mcrfpy.Animation("x", 300, 1.0, mcrfpy.Easing.EASE_OUT, delta=True)
        anim.start(delta_frame)

scene.on_key = on_key
