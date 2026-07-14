# mcrf: objects=[Caption,Color,Easing,Frame,InputState,Key,Scene,Timer] verified=0.2.8-dev@a7ba486 status=ok
# Animation Complete Check - Monitor animation state
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

frame = mcrfpy.Frame(
    pos=(100, 334), size=(100, 100),
    fill_color=mcrfpy.Color(255, 150, 100)
)
scene.children.append(frame)

status = mcrfpy.Caption(text="Animation state: not started", pos=(350, 500))
scene.children.append(status)

elapsed_label = mcrfpy.Caption(text="", pos=(380, 550))
scene.children.append(elapsed_label)

scene.children.append(mcrfpy.Caption(text="Press SPACE to start animation", pos=(350, 650)))

current_anim = None

def update_status(timer, runtime):
    if current_anim:
        elapsed_label.text = f"Elapsed: {current_anim.elapsed:.2f}s / {current_anim.duration}s"
        if current_anim.is_complete:
            status.text = "Animation state: COMPLETE"
            status.fill_color = mcrfpy.Color(100, 255, 100)
        else:
            status.text = "Animation state: in progress"
            status.fill_color = mcrfpy.Color(255, 255, 100)

timer = mcrfpy.Timer("check", update_status, 50)

def on_key(key, action):
    global current_anim
    if key == mcrfpy.Key.SPACE and action == mcrfpy.InputState.PRESSED:
        frame.x = 100
        current_anim = frame.animate("x", 800, 3.0, mcrfpy.Easing.EASE_IN_OUT)
        status.text = "Animation state: started"

scene.on_key = on_key
