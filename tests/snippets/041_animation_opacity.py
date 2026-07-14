# mcrf: objects=[Caption,Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev status=ok
# Animation Opacity - Fade in/out
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(
    pos=(0, 0), size=(1024, 768),
    fill_color=mcrfpy.Color(30, 30, 40)
))

# Frame that fades out
frame = mcrfpy.Frame(
    pos=(262, 184), size=(500, 400),
    fill_color=mcrfpy.Color(200, 100, 255),
    opacity=1.0
)
scene.children.append(frame)

label = mcrfpy.Caption(
    text="I'm fading away...",
    pos=(170, 180))
label.fill_color = mcrfpy.Color(255, 255, 255)
frame.children.append(label)

_caption = mcrfpy.Caption(
    text="Animating opacity from 1.0 to 0.0",
    pos=(360, 620))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

def restart_animation(timer, runtime):
    frame.opacity = 1.0
    frame.animate("opacity", 0.0, 4.0, mcrfpy.Easing.EASE_IN)

frame.animate("opacity", 0.0, 4.0, mcrfpy.Easing.EASE_IN)
loop_timer = mcrfpy.Timer("loop", restart_animation, 9000)  # 4s animation + 5s pause
