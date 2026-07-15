# mcrf: objects=[Color,Frame,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(
    pos=(0, 0), size=(1024, 768),
    fill_color=mcrfpy.Color(30, 30, 40)
))

# Create a repeating timer (fires every 500ms)
def on_tick(timer, runtime):
    print(f"Tick at {runtime}ms")

timer = mcrfpy.Timer("game_tick", on_tick, 500)

# One-shot timer (fires once after 2 seconds)
def delayed_action(timer, runtime):
    print("Delayed action executed!")

mcrfpy.Timer("delay", delayed_action, 2000, once=True)

# Control timer state
timer.pause()
timer.resume()
timer.restart()
timer.stop()

# Create paused (start manually later)
def callback(timer, runtime):
    pass

timer2 = mcrfpy.Timer("manual", callback, 1000, start=False)
timer2.start()
