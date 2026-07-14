# mcrf: objects=[Caption,Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev status=ok
# Easing Exponential - Dramatic acceleration
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

_caption = mcrfpy.Caption(
    text="Exponential Easing - Dramatic Effect",
    pos=(340, 50))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

easings = [
    (mcrfpy.Easing.EASE_IN_EXPO, "EASE_IN_EXPO"),
    (mcrfpy.Easing.EASE_OUT_EXPO, "EASE_OUT_EXPO"),
    (mcrfpy.Easing.EASE_IN_OUT_EXPO, "EASE_IN_OUT_EXPO"),
]

colors = [
    mcrfpy.Color(255, 200, 100),
    mcrfpy.Color(100, 200, 255),
    mcrfpy.Color(200, 100, 255),
]

frames = []
for i, ((easing, name), color) in enumerate(zip(easings, colors)):
    y = 150 + i * 180

    label = mcrfpy.Caption(text=name, pos=(100, y + 20))
    scene.children.append(label)

    frame = mcrfpy.Frame(pos=(350, y), size=(80, 60), fill_color=color)
    scene.children.append(frame)
    frames.append((frame, easing))
    frame.animate("x", 870, 3.0, easing)

scene.children.append(mcrfpy.Caption(
    text="Exponential provides very sharp acceleration/deceleration",
    pos=(280, 700)
))

def restart_animation(timer, runtime):
    for frame, easing in frames:
        frame.x = 350
        frame.animate("x", 870, 3.0, easing)

loop_timer = mcrfpy.Timer("loop", restart_animation, 8000)
