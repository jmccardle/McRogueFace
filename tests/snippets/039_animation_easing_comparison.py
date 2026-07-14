# mcrf: objects=[Caption,Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev status=ok
# Easing Comparison - Multiple easings side by side
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(
    pos=(0, 0), size=(1024, 768),
    fill_color=mcrfpy.Color(30, 30, 40)
))

easings = [
    (mcrfpy.Easing.LINEAR, "LINEAR", mcrfpy.Color(255, 100, 100)),
    (mcrfpy.Easing.EASE_IN_QUAD, "EASE_IN_QUAD", mcrfpy.Color(255, 200, 100)),
    (mcrfpy.Easing.EASE_OUT_QUAD, "EASE_OUT_QUAD", mcrfpy.Color(200, 255, 100)),
    (mcrfpy.Easing.EASE_IN_OUT_QUAD, "EASE_IN_OUT_QUAD", mcrfpy.Color(100, 255, 100)),
    (mcrfpy.Easing.EASE_OUT_BOUNCE, "EASE_OUT_BOUNCE", mcrfpy.Color(100, 255, 200)),
    (mcrfpy.Easing.EASE_OUT_ELASTIC, "EASE_OUT_ELASTIC", mcrfpy.Color(100, 200, 255)),
]

frames = []
for i, (easing, name, color) in enumerate(easings):
    y = 80 + i * 110

    label = mcrfpy.Caption(text=name, pos=(100, y + 15))
    label.fill_color = mcrfpy.Color(180, 180, 180)
    scene.children.append(label)

    frame = mcrfpy.Frame(
        pos=(350, y), size=(60, 50),
        fill_color=color
    )
    scene.children.append(frame)
    frames.append((frame, easing))
    frame.animate("x", 900, 3.0, easing)

def restart_animation(timer, runtime):
    for frame, easing in frames:
        frame.x = 350
        frame.animate("x", 900, 3.0, easing)

loop_timer = mcrfpy.Timer("loop", restart_animation, 8000)
