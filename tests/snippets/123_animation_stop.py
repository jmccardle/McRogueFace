# mcrf: objects=[Caption,Color,Easing,Frame,InputState,Key,Scene] verified=0.2.8-dev status=ok
# Animation Stop/Complete - Control running animations
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

frame = mcrfpy.Frame(
    pos=(100, 300), size=(100, 100),
    fill_color=mcrfpy.Color(150, 100, 255)
)
scene.children.append(frame)

status = mcrfpy.Caption(text="Press SPACE to start, S to stop, C to complete", pos=(280, 500))
scene.children.append(status)

current_anim = None

def on_key(key, action):
    global current_anim
    if action != mcrfpy.InputState.PRESSED: return

    if key == mcrfpy.Key.SPACE:
        frame.x = 100
        current_anim = frame.animate("x", 800, 5.0, mcrfpy.Easing.LINEAR)
        status.text = "Animation started (5 seconds)"

    elif key == mcrfpy.Key.S and current_anim:
        current_anim.stop()
        status.text = f"Animation STOPPED at x={frame.x:.0f}"

    elif key == mcrfpy.Key.C and current_anim:
        current_anim.complete()
        status.text = f"Animation COMPLETED - jumped to x={frame.x:.0f}"

scene.on_key = on_key
