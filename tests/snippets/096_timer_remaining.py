# mcrf: objects=[Caption,Color,Frame,Scene,Timer] verified=0.2.8-dev status=ok
# Timer Remaining - Check time until next tick
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

_caption = mcrfpy.Caption(
    text="Timer Properties",
    pos=(420, 100))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

# Progress bar background
bar_bg = mcrfpy.Frame(
    pos=(212, 300), size=(600, 40),
    fill_color=mcrfpy.Color(50, 50, 70),
    outline=2.0
)
scene.children.append(bar_bg)

# Progress bar fill
bar_fill = mcrfpy.Frame(
    pos=(2, 2), size=(596, 36),
    fill_color=mcrfpy.Color(100, 200, 100)
)
bar_bg.children.append(bar_fill)

status = mcrfpy.Caption(text="", pos=(350, 400))
scene.children.append(status)

tick_count = 0
tick_label = mcrfpy.Caption(text="Ticks: 0", pos=(450, 500))
scene.children.append(tick_label)

def on_tick(timer, runtime):
    global tick_count
    tick_count += 1
    tick_label.text = f"Ticks: {tick_count}"

# 3 second timer
main_timer = mcrfpy.Timer("main", on_tick, 3000)

def update_display(timer, runtime):
    remaining = main_timer.remaining
    interval = main_timer.interval
    progress = 1.0 - (remaining / interval)
    bar_fill.w = int(596 * progress)
    status.text = f"Remaining: {remaining}ms / {interval}ms"

display_timer = mcrfpy.Timer("display", update_display, 16)
