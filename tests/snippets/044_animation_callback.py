# mcrf: objects=[Caption,Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev@a7ba486 status=ok
# Animation Callback - Run code when animation ends
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(
    pos=(0, 0), size=(1024, 768),
    fill_color=mcrfpy.Color(30, 30, 40)
))

frame = mcrfpy.Frame(
    pos=(100, 334), size=(100, 100),
    fill_color=mcrfpy.Color(255, 150, 100)
)
scene.children.append(frame)

status = mcrfpy.Caption(
    text="Animation in progress...",
    pos=(380, 500))
status.fill_color = mcrfpy.Color(200, 200, 200)
scene.children.append(status)

# Callback when animation completes
def on_complete(target, prop, value):
    status.text = f"Animation complete! {prop}={value:.0f}"
    target.fill_color = mcrfpy.Color(100, 255, 100)

def restart_animation(timer, runtime):
    frame.x = 100
    frame.fill_color = mcrfpy.Color(255, 150, 100)
    status.text = "Animation in progress..."
    frame.animate("x", 824, 2.0, mcrfpy.Easing.EASE_OUT, callback=on_complete)

frame.animate("x", 824, 2.0, mcrfpy.Easing.EASE_OUT, callback=on_complete)
loop_timer = mcrfpy.Timer("loop", restart_animation, 7000)  # 2s animation + 5s pause
