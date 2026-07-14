# mcrf: objects=[Caption,Color,Frame,InputState,Key,Scene,Timer] verified=0.2.8-dev@a7ba486 status=ok
# Exit Game - Clean shutdown
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

_caption = mcrfpy.Caption(
    text="Exit Game Demo",
    pos=(420, 200))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

scene.children.append(mcrfpy.Caption(
    text="Press ESC to exit the game",
    pos=(380, 350)
))

scene.children.append(mcrfpy.Caption(
    text="This will close the window cleanly",
    pos=(360, 420)
))

countdown = mcrfpy.Caption(text="", pos=(420, 550))
scene.children.append(countdown)

exit_countdown = 0
exit_timer = None

def tick(timer, runtime):
    global exit_countdown
    exit_countdown -= 1
    if exit_countdown > 0:
        countdown.text = f"Exiting in {exit_countdown}..."
    else:
        timer.stop()
        countdown.text = "Goodbye!"
        mcrfpy.exit()  # Clean shutdown

def on_key(key, action):
    global exit_countdown, exit_timer
    if key == mcrfpy.Key.ESCAPE and action == mcrfpy.InputState.PRESSED:
        if exit_timer is None:
            countdown.text = "Exiting in 3..."
            exit_countdown = 3
            exit_timer = mcrfpy.Timer("exit_timer", tick, 1000)

scene.on_key = on_key
