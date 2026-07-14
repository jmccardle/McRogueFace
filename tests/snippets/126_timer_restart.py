# mcrf: objects=[Caption,Color,Frame,InputState,Key,Scene,Timer] verified=0.2.8-dev status=ok
# Timer Restart - Reset and start timer
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

count = 0
count_label = mcrfpy.Caption(text="Count: 0", pos=(450, 300))
count_label.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(count_label)

status = mcrfpy.Caption(text="Timer running", pos=(430, 400))
scene.children.append(status)

def on_tick(timer, runtime):
    global count
    count += 1
    count_label.text = f"Count: {count}"

timer = mcrfpy.Timer("counter", on_tick, 1000)

scene.children.append(mcrfpy.Caption(
    text="P=pause, R=restart (resets count too)",
    pos=(350, 550)
))

def on_key(key, action):
    global count
    if action != mcrfpy.InputState.PRESSED: return

    if key == mcrfpy.Key.P:
        if timer.paused:
            timer.resume()
            status.text = "Timer resumed"
        else:
            timer.pause()
            status.text = "Timer paused"

    elif key == mcrfpy.Key.R:
        count = 0
        count_label.text = "Count: 0"
        timer.restart()  # Reset timer AND ensure running
        status.text = "Timer restarted"

scene.on_key = on_key
