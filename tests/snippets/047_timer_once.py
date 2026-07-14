# mcrf: objects=[Caption,Color,Frame,Scene,Timer] verified=0.2.8-dev status=ok
# Timer Once - Single-shot timer
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(
    pos=(0, 0), size=(1024, 768),
    fill_color=mcrfpy.Color(30, 30, 40)
))

status = mcrfpy.Caption(
    text="Waiting for timer...",
    pos=(380, 350))
status.fill_color = mcrfpy.Color(200, 200, 200)
scene.children.append(status)

def on_fire(timer, runtime):
    status.text = "Timer fired! (once=True)"
    status.fill_color = mcrfpy.Color(100, 255, 100)

# Timer fires once after 2 seconds
timer = mcrfpy.Timer("delayed", on_fire, 2000, once=True)

scene.children.append(mcrfpy.Caption(
    text="Single-shot timer fires after 2 seconds",
    pos=(320, 450)
))
