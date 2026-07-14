# mcrf: objects=[Caption,Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev status=ok
# Animation Size - Grow and shrink
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(
    pos=(0, 0), size=(1024, 768),
    fill_color=mcrfpy.Color(30, 30, 40)
))

# Frame that grows
frame = mcrfpy.Frame(
    pos=(462, 334), size=(100, 100),
    fill_color=mcrfpy.Color(100, 255, 150),
    outline=2.0,
    outline_color=mcrfpy.Color(255, 255, 255)
)
scene.children.append(frame)

_caption = mcrfpy.Caption(
    text="Animating w and h properties",
    pos=(380, 620))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

def restart_animation(timer, runtime):
    frame.w = 100
    frame.h = 100
    frame.animate("w", 400, 2.0, mcrfpy.Easing.EASE_OUT_ELASTIC)
    frame.animate("h", 300, 2.0, mcrfpy.Easing.EASE_OUT_ELASTIC)

# Animate both dimensions
frame.animate("w", 400, 2.0, mcrfpy.Easing.EASE_OUT_ELASTIC)
frame.animate("h", 300, 2.0, mcrfpy.Easing.EASE_OUT_ELASTIC)
loop_timer = mcrfpy.Timer("loop", restart_animation, 7000)  # 2s animation + 5s pause
