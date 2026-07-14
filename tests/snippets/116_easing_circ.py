# mcrf: objects=[Caption,Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev status=ok
# Easing Circular - Circular motion curve
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

_caption = mcrfpy.Caption(
    text="Circular Easing - Arc-like Motion",
    pos=(350, 50))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

easings = [
    (mcrfpy.Easing.EASE_IN_CIRC, "EASE_IN_CIRC"),
    (mcrfpy.Easing.EASE_OUT_CIRC, "EASE_OUT_CIRC"),
    (mcrfpy.Easing.EASE_IN_OUT_CIRC, "EASE_IN_OUT_CIRC"),
]

colors = [mcrfpy.Color(255, 120, 120), mcrfpy.Color(120, 255, 120), mcrfpy.Color(120, 120, 255)]

frames = []
for i, ((easing, name), color) in enumerate(zip(easings, colors)):
    y = 150 + i * 180
    scene.children.append(mcrfpy.Caption(text=name, pos=(100, y + 20)))
    frame = mcrfpy.Frame(pos=(350, y), size=(80, 60), fill_color=color)
    scene.children.append(frame)
    frames.append((frame, easing))
    frame.animate("x", 870, 3.0, easing)

scene.children.append(mcrfpy.Caption(text="Circular easing follows quarter-circle curve", pos=(310, 700)))

def restart_animation(timer, runtime):
    for frame, easing in frames:
        frame.x = 350
        frame.animate("x", 870, 3.0, easing)

loop_timer = mcrfpy.Timer("loop", restart_animation, 8000)
