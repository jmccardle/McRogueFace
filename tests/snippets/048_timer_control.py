# mcrf: objects=[Caption,Color,Frame,InputState,Key,Scene,Timer] verified=0.2.8-dev status=ok
# Timer Control - Pause, resume, stop
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(
    pos=(0, 0), size=(1024, 768),
    fill_color=mcrfpy.Color(30, 30, 40)
))

# Moving frame
frame = mcrfpy.Frame(
    pos=(100, 334), size=(80, 80),
    fill_color=mcrfpy.Color(255, 150, 100)
)
scene.children.append(frame)

status = mcrfpy.Caption(
    text="Timer running - P=pause, R=resume, S=stop",
    pos=(280, 500)
)
scene.children.append(status)

direction = 1

def animate(timer, runtime):
    global direction
    frame.x += 5 * direction
    if frame.x > 844:
        direction = -1
    elif frame.x < 100:
        direction = 1

timer = mcrfpy.Timer("mover", animate, 16)

def on_key(key, action):
    if action != mcrfpy.InputState.PRESSED:
        return
    if key == mcrfpy.Key.P:
        timer.pause()
        status.text = "Timer PAUSED"
    elif key == mcrfpy.Key.R:
        timer.resume()
        status.text = "Timer RESUMED"
    elif key == mcrfpy.Key.S:
        timer.stop()
        status.text = "Timer STOPPED"

scene.on_key = on_key
