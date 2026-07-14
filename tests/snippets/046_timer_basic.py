# mcrf: objects=[Caption,Color,Frame,Scene,Timer] verified=0.2.8-dev status=ok
# Timer Basic - Periodic callback
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(
    pos=(0, 0), size=(1024, 768),
    fill_color=mcrfpy.Color(30, 30, 40)
))

counter = mcrfpy.Caption(
    text="Ticks: 0",
    pos=(420, 350))
counter.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(counter)

count = 0

def on_tick(timer, runtime):
    global count
    count += 1
    counter.text = f"Ticks: {count}"

# Timer fires every 500ms
timer = mcrfpy.Timer("ticker", on_tick, 500)

scene.children.append(mcrfpy.Caption(
    text="Timer interval: 500ms",
    pos=(410, 450)
))
