# mcrf: objects=[Caption,Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev status=ok
# Easing Cubic - Cubic easing functions
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

_caption = mcrfpy.Caption(
    text="Cubic Easing Functions",
    pos=(380, 50))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

easings = [
    (mcrfpy.Easing.EASE_IN_CUBIC, "EASE_IN_CUBIC", mcrfpy.Color(255, 100, 100)),
    (mcrfpy.Easing.EASE_OUT_CUBIC, "EASE_OUT_CUBIC", mcrfpy.Color(100, 255, 100)),
    (mcrfpy.Easing.EASE_IN_OUT_CUBIC, "EASE_IN_OUT_CUBIC", mcrfpy.Color(100, 100, 255)),
]

frames = []
for i, (easing, name, color) in enumerate(easings):
    y = 150 + i * 180

    label = mcrfpy.Caption(text=name, pos=(100, y + 20))
    label.fill_color = mcrfpy.Color(180, 180, 180)
    scene.children.append(label)

    frame = mcrfpy.Frame(pos=(350, y), size=(80, 60), fill_color=color)
    scene.children.append(frame)
    frames.append((frame, easing))

    # Markers
    scene.children.append(mcrfpy.Frame(pos=(350, y - 5), size=(3, 70), fill_color=mcrfpy.Color(80, 80, 80)))
    scene.children.append(mcrfpy.Frame(pos=(870, y - 5), size=(3, 70), fill_color=mcrfpy.Color(80, 80, 80)))

    frame.animate("x", 870, 3.0, easing)

scene.children.append(mcrfpy.Caption(
    text="Cubic provides stronger acceleration than quadratic",
    pos=(300, 700)
))

def restart_animation(timer, runtime):
    for frame, easing in frames:
        frame.x = 350
        frame.animate("x", 870, 3.0, easing)

loop_timer = mcrfpy.Timer("loop", restart_animation, 8000)
